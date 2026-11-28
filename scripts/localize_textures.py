#!/usr/bin/env python3
"""Generate review-only Russian PNG proposals from the Milestone 3N manifest."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
from importlib.metadata import version
from io import BytesIO
import json
from pathlib import Path
import re
import shutil
import sys
import tempfile
import unicodedata

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.scan_milestone3n_artwork import DATASETS, OUTPUT, _texture_rows, _unpack, digest, file_digest
from src.extraction.garc import GARC
from src.rebuilding.artwork_localization import (ReviewRequired, Translator, classify_english, local_paddle,
                                                 multi_pass_ocr, ocr, render, text_key, _ROTATIONS)
from src.rebuilding.artwork_rendering import reference_style, render_enhanced
from src.rebuilding.bclim import ETC_FORMATS, recompress_bclim_etc
from src.rebuilding.textures import decode_bclim, encode_bclim

OUTPUT_ROOT = ROOT / "build/offline-textures"
BATTLE_REFERENCES = ROOT / "build/milestone-3i/editing"
ARTWORK_GLOSSARY = ROOT / "glossary/artwork-terms.json"
# Source fingerprints keep the 3O pilot stable when discovery assigns new IDs.
PILOT_HASHES = (
    "5ef407c541df09ff47a4502ab65173348c4bbf58dd90cc087c55d43de46f920c",  # T000264
    "b6910ab4e5a54c5fbb411429f622224d1fb14fc3253684bc312906f59ce9087e",  # T002718
    "83a5eb0fd06b86fa2e10068940eafc2614c7fb3d39355f206cd2187299226ca0",  # T003077
    "64f004d6c884d93b38d8023b28c33b2cf56e0b584a09a5ef3e896747c55e96ea",  # T003101
    "76bba1450dbda41153ab562ff276d087ee2e7bf07c8aae34c4eacd9449e16a94",  # T003394
    "3fcb80a78d88f42a275b857a2edea018a21a7ca184d050a3ce3c483557b66cd1",  # T003397
    "da42241162b8a7c3d4e7d91cf0062ec44ce867cca9de4386e7896fc9a1e91054",  # T003423
    "5b43e1f52f37eeebd00f095f843c7b54caf8b989975eee0ee677bc47916fee6c",  # T003430
    "f0ea91a7e9a720a09bee5eeae253b5acfbc6e7e8640c7834be38d1b6a962fb39",  # T003475
    "41ece7f5a2c27d5d62d99e2f9027f6dab52176fb902672f95ce18ee85f4d78d7",  # T003563
)


@lru_cache(maxsize=2)
def archive_bytes(path: Path) -> bytes:
    if path.stat().st_size > 128 * 1024 * 1024:
        raise ReviewRequired("Source archive exceeds the proposal reader's 128 MiB limit")
    return _unpack(path.read_bytes())[0]


def original_texture(row: dict) -> bytes:
    dataset = row["game"], row["version"]
    if dataset not in DATASETS:
        raise ValueError(f"Unknown dataset: {dataset}")
    source_root = ROOT.joinpath("workspace", *dataset).resolve(strict=True)
    path = (source_root / row["archive_path"]).resolve(strict=True)
    if source_root not in path.parents:
        raise ValueError("Texture archive path escapes its source dataset")
    data = archive_bytes(path)
    member = row["nested_member"]
    if member:
        identifiers = list(map(int, member.split("/")))
        if len(identifiers) % 2:
            raise ValueError(f"Invalid member locator: {member}")
        for entry, subfile in zip(identifiers[::2], identifiers[1::2]):
            part = next((part for part in GARC.parse(data).entries[entry].members
                         if part.subfile_id == subfile), None)
            if part is None:
                raise ValueError(f"Missing member: {member}")
            data, _ = _unpack(part.data)
        parts, _ = _texture_rows(data)
        data = next((part["data"] for part in parts
                     if part["name"] == row["internal_filename"] and digest(part["data"]) == row["sha256"]), b"")
    if digest(data) != row["sha256"]:
        raise ValueError(f"Source BCLIM fingerprint mismatch for {row['asset_id']}")
    return data


def json_bytes(data) -> bytes:
    return (json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()


def png_bytes(image: Image.Image) -> bytes:
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def process(row: dict, args, translate, directory: Path) -> dict:
    result = {"status": "review", "lines": []}
    with Image.open(scanner_png(row)) as png:
        original = png.convert("RGBA")
    before = png_bytes(original)
    (directory / "before.png").write_bytes(before)
    after = before
    try:
        if row.get("source_kind") == "BCH":
            raise ReviewRequired("BCH previews require a separate artwork review")
        raw = original_texture(row)
        if row["format"] not in (8, 9):
            raise ReviewRequired("BCLIM format is outside the 3I encoder subset")
        try:
            width, height, fmt, pixels = decode_bclim(raw)
        except ValueError as exc:
            raise ReviewRequired(f"3I texture layout: {exc}") from exc
        if (width, height) != original.size or pixels != original.tobytes():
            raise ReviewRequired("Scanner PNG differs from source pixels and may contain manual edits")
        lines = result["lines"] = ocr(original, args.tesseract, args.tessdata)
        if ocr_evidence(lines) != "single_high_confidence_latin_line":
            raise ReviewRequired("OCR returned no single high-confidence English line")
        line = lines[0]
        if line["english"].casefold() in {"fin", "fine"} and row["internal_filename"] == "the_end_txt.bclim":
            raise ReviewRequired("End-card lettering requires language identification")
        russian, method = translate(line["english"])
        line.update(russian=russian, translation_method=method)
        rendered = render(original, line["box"], russian, args.font)
        if rendered.tobytes() == pixels:
            raise ReviewRequired("Rendered pixels are identical to the source")
        encoded = encode_bclim(rendered.tobytes(), width, height, raw)
        if decode_bclim(encoded) != (width, height, fmt, rendered.tobytes()):
            raise ReviewRequired("The 3I BCLIM round trip changed rendered pixels")
        after = png_bytes(rendered)
        result.update(status="proposal", reason="Visual and linguistic review required",
                      changed_pixels=sum(a != b for a, b in zip(original.get_flattened_data(),
                                                                 rendered.get_flattened_data())),
                      proposed_bclim_sha256=digest(encoded))
    except ReviewRequired as exc:
        result["reason"] = str(exc)
    (directory / "after.png").write_bytes(after)
    result.update(before_sha256=digest(before), after_sha256=digest(after))
    (directory / "result.json").write_bytes(json_bytes(result))
    return result


def style_references(rows: dict, root: Path) -> tuple[list[dict], dict]:
    refs = []
    fingerprints = {}
    manifest = json.loads((root / "manifest.json").read_bytes())
    assets = manifest["assets"]
    if len(assets) != 24 or len({row["png"] for row in assets}) != 24:
        raise ValueError("Expected the 24 canonical battle references")
    for entry in assets:
        name = entry["png"]
        if Path(name).name != name:
            raise ValueError("Invalid reference name")
        source_hash = entry["source_bclim_sha256"]
        if source_hash not in rows:
            # A BCH-only manifest has no battle rows. Use the canonical
            # discovery manifest to resolve the original asset by hash.
            original_rows = json.loads((OUTPUT / "texture-manifest.json").read_bytes())
            rows = {row["sha256"]: [row] for row in original_rows}
        before = scanner_png(rows[source_hash][0])
        after = (root / name).resolve(strict=True)
        if after.parent != root.resolve():
            raise ValueError("Style reference must stay in the canonical directory")
        fingerprints[name] = {"original": file_digest(before), "edited": file_digest(after)}
        with Image.open(before) as original, Image.open(after) as edited:
            refs.append(reference_style(original.convert("RGBA"), edited.convert("RGBA")))
    return refs, fingerprints


def texture_context(row: dict) -> tuple[str, ...]:
    name = row["internal_filename"]
    if name.startswith(("zkn_", "p_zkn_")):
        return ("ui", "battle_ui")
    if name.startswith("vs_"):
        return ("artwork_battle_results", "battle_terminology")
    if name.startswith(("sick_", "dead_", "exp_", "hp_")):
        return ("artwork_battle_status", "battle_terminology")
    if name.startswith("meter_"):
        return ("artwork_stats", "battle_terminology")
    return ("texture_ui", "artwork_menu", "ui")


def translated_lines(lines: list[dict], translate: Translator, context: tuple[str, ...]) -> list[dict]:
    if len(lines) > 1:
        # Translate a stacked label as one phrase to retain word order and
        # context, then allocate complete words to the original line slots.
        target, method = translate(" ".join(line["text"] for line in lines), context)
        words = target.split()
        if len(words) < len(lines):
            raise ReviewRequired("Russian phrase cannot fit the original number of lines")
        out = []
        start = 0
        for i, line in enumerate(lines):
            remaining = len(lines) - i
            count = (len(words) - start) // remaining
            out.append(dict(line, russian=" ".join(words[start:start + count]), translation_method=method))
            start += count
        return out
    line, = lines
    russian, method = translate(line["text"], context)
    return [dict(line, russian=russian, translation_method=method)]


def russian_key(text: str) -> str:
    return " ".join(re.findall(r"[^\W_]+", unicodedata.normalize("NFC", text.casefold())))


def process_enhanced(row: dict, args, translate: Translator, directory: Path, *, protected: bool = False) -> dict:
    with Image.open(scanner_png(row)) as png:
        original = png.convert("RGBA")
    before = png_bytes(original)
    (directory / "before.png").write_bytes(before)
    after = before
    result = {"status": "review", "lines": []}
    try:
        evidence = multi_pass_ocr(original, args.tesseract, args.tessdata, paddle=args.paddle_recognizer)
        vocabulary = {word for phrase in translate.terms for word in text_key(phrase).split()}
        classification, lines = classify_english(evidence, row["internal_filename"], vocabulary)
        result.update(classification=classification, evidence=evidence, lines=lines)
        if protected:
            result["status"] = "protected"
            raise ReviewRequired("Read-only benchmark control with existing manual artwork")
        if not lines:
            raise ReviewRequired("English lettering was not confirmed")
        context = texture_context(row)
        result["lines"] = lines = translated_lines(lines, translate, context)
        if classification == "english_review":
            raise ReviewRequired("OCR evidence needs agreement before rendering")
        if row.get("source_kind") == "BCH":
            raise ReviewRequired("BCH assets have no verified artwork proposal encoder")
        raw = original_texture(row)
        width, height, fmt, source = decode_bclim(raw)
        if (width, height) != original.size or source != original.tobytes():
            raise ReviewRequired("Preview is not byte-equivalent to the decoded source")
        if fmt not in (8, 9, *ETC_FORMATS):
            raise ReviewRequired("Source format is outside the enhanced editing subset")
        rendered, mask, profiles = render_enhanced(original, lines, args.fonts, args.style_profiles, fmt)
        result["visual"] = profiles
        if not mask.getbbox():
            raise ReviewRequired("No glyph pixels changed")
        draft = png_bytes(rendered)
        (directory / "draft.png").write_bytes(draft)
        result["draft_sha256"] = digest(draft)
        proposed = rendered.tobytes()
        try:
            if fmt in ETC_FORMATS:
                encoded, result["compression"] = recompress_bclim_etc(proposed, raw, mask.tobytes())
            else:
                encoded = encode_bclim(proposed, width, height, raw)
        except ValueError as exc:
            raise ReviewRequired(f"Texture could not be safely encoded: {exc}") from exc
        rw, rh, rf, decoded = decode_bclim(encoded)
        if (rw, rh, rf) != (width, height, fmt):
            raise ReviewRequired("Encoding changed source layout")
        if fmt not in ETC_FORMATS and decoded != proposed:
            raise ReviewRequired("Uncompressed texture did not reproduce rendered pixels exactly")
        allowed = mask.tobytes()
        for i in range(width * height):
            at = i * 4
            if not allowed[i] and decoded[at:at + 4] != source[at:at + 4]:
                raise ReviewRequired("Decoded artwork changed outside the lettering mask")
            if decoded[at + 3] != proposed[at + 3]:
                raise ReviewRequired("Encoding changed the proposed transparency")
        verified = Image.frombytes("RGBA", original.size, decoded)
        checks = []
        for line, profile in zip(lines, profiles):
            region = verified.crop(profile["region"])
            if line["rotation"]:
                region = region.transpose(_ROTATIONS[line["rotation"]])
            readback = multi_pass_ocr(region, args.tesseract, args.tessdata, language="rus")
            matched = any(russian_key(observation["text"]) == russian_key(line["russian"])
                          and observation["confidence"] >= 75 and len(observation["passes"]) >= 2
                          for observation in readback)
            checks.append({"expected": line["russian"], "matched": matched, "lines": readback})
        result["russian_ocr"] = checks
        if not all(check["matched"] for check in checks):
            raise ReviewRequired("Russian OCR did not independently confirm every decoded line")
        if any(profile["visual_score"] < 0.68 or profile["palette_coverage"] < 0.88
               or profile["width_fit"] < 0.68 or profile["slant_match"] < 0.62
               or profile["soft_alpha_drift"] > 0.18 for profile in profiles):
            raise ReviewRequired("Letterform, spacing, palette or soft-alpha profile fell outside visual limits")
        if any(line["translation_method"] != "glossary" for line in lines):
            raise ReviewRequired("Offline model translation requires linguistic review")
        after = png_bytes(verified)
        result.update(status="automatic_preview", reason="Local OCR, style and encoding gates passed",
                      changed_pixels=sum(bool(value) for value in allowed), proposed_bclim_sha256=digest(encoded))
    except ReviewRequired as exc:
        result["reason"] = str(exc)
    (directory / "after.png").write_bytes(after)
    result.update(before_sha256=digest(before), after_sha256=digest(after))
    (directory / "result.json").write_bytes(json_bytes(result))
    return result


def benchmark_scores(textures: list[dict], labels: dict) -> dict:
    scores = Counter()
    rows = []
    english_classes = {"english", "rotated_english", "multiline_english"}
    for texture in textures:
        label = labels[texture["sha256"]]
        detected = texture.get("classification") in english_classes
        expected = label.get("english")
        scores["english_expected" if expected else "non_english_expected"] += 1
        actual = " ".join(line["text"] for line in texture.get("lines", []))
        translated = " ".join(line.get("russian", "") for line in texture.get("lines", [])).strip()
        text_match = bool(expected and text_key(actual) == text_key(expected))
        translation_match = bool(translated and russian_key(translated) in {
            russian_key(t) for t in label.get("russian", [])
        })
        scores["true_positive" if expected and detected else "false_negative" if expected else
               "false_positive" if detected else "true_negative"] += 1
        scores["exact_english_transcriptions"] += text_match
        scores["incorrect_confirmed_transcriptions"] += bool(expected and detected and not text_match)
        scores["protected_controls"] += texture["status"] == "protected"
        scores["translations_attempted"] += bool(translated)
        scores["gold_translation_matches"] += translation_match
        scores["rendered_drafts"] += "draft_sha256" in texture
        scores["automatic_previews"] += texture["status"] == "automatic_preview"
        scores["incorrect_automatic_previews"] += texture["status"] == "automatic_preview" and not translation_match
        rows.append({"sha256": texture["sha256"], "label": label, "english_detected": detected,
                     "actual_english": actual, "actual_russian": translated, "text_match": text_match,
                     "translation_match": translation_match})
    visual = [profile for texture in textures for profile in texture.get("visual", [])]
    averages = {key: round(sum(profile[key] for profile in visual) / len(visual), 3)
                for key in ("visual_score", "palette_coverage", "width_fit", "slant_match", "soft_alpha_drift")} if visual else {}
    return {"counts": dict(scores), "rendered_line_quality_means": averages, "assets": rows}


def curated_selection(path: Path, groups: dict) -> dict:
    indexed = defaultdict(set)
    for checksum in groups:
        indexed[checksum[:12]].add(checksum)
    selected = []
    missing = []
    for png in sorted(path.glob("*.png")):
        match = re.match(r"T\d+_([a-f0-9]{12})_", png.name)
        hashes = indexed.get(match[1], set()) if match else set()
        if len(hashes) != 1:
            missing.append(png.name)
        else:
            selected.append(next(iter(hashes)))
    return {"assets": sorted(set(selected)), "files": len(selected) + len(missing), "unmapped": missing}


def protected_hashes(args) -> set[str]:
    protected = set()
    # Match owner-edited files by stable raw hash prefix as scanner IDs can change.
    for root in args.protect:
        if not root.is_dir():
            raise ValueError(f"Manual edit directory does not exist: {root}")
    for root in {OUTPUT / "done", args.manifest.parent / "done", *args.protect}:
        for path in root.rglob("*.png"):
            match = re.match(r"T\d+_([a-f0-9]{12,64})_", path.name)
            if not match:
                raise ValueError(f"Cannot identify protected source hash from {path.name}")
            protected.add(match[1])
    return protected


def is_protected(raw_hash: str, rows: list[dict], protected: set[str]) -> bool:
    return any(raw_hash.startswith(prefix) for prefix in protected) or any(
        not row["pending_translation"] for row in rows
    )


def scanner_png(row: dict) -> Path:
    path = (ROOT / row["png_path"]).resolve(strict=True)
    if (ROOT / "build").resolve() not in path.parents:
        raise ValueError("Scanner export must be under build/")
    return path


def ocr_evidence(lines: list[dict]) -> str:
    if not lines:
        return "no_ocr_text"
    if len(lines) != 1 or lines[0]["confidence"] < 75 or not re.search("[A-Za-z]{2}", lines[0]["english"]):
        return "ocr_requires_review"
    return "single_high_confidence_latin_line"


def ocr_inventory(args) -> Path:
    baseline = {}
    for row in json.loads(args.ocr_new_since.read_bytes()):
        baseline.setdefault(row["sha256"], row)
    current = defaultdict(list)
    for row in json.loads(args.manifest.read_bytes()):
        current[row["sha256"]].append(row)
    protected = protected_hashes(args)
    inputs = {
        "ocr": file_digest(ROOT / "src/rebuilding/artwork_localization.py"),
        "pipeline": file_digest(Path(__file__)),
        "pillow": version("Pillow"),
        "tesseract": file_digest(args.tesseract),
        "eng_traineddata": file_digest(args.tessdata / "eng.traineddata"),
    }
    cache_root, reports = output_directories("ocr-cache")

    def inspect(entry):
        raw_hash, occurrences = entry
        row = occurrences[0]
        png = scanner_png(row)
        png_hash = file_digest(png)
        previous = baseline.get(raw_hash)
        if previous and file_digest(scanner_png(previous)) == png_hash:
            return None
        fields = ("game", "version", "archive_path", "nested_member", "internal_filename", "asset_id")
        if row.get("source_kind") == "BCH":
            fields += ("bch_sha256", "archive_sha256", "member_lz11", "texture_index",
                       "descriptor_offset", "face", "mip_level", "mipmap_count", "data_offset",
                       "data_length", "payload_sha256")
        item = {
            "sha256": raw_hash, "png_sha256": png_hash, "png_path": row["png_path"], "format": row["format"],
            "change": "corrected_preview" if previous else "newly_decoded",
            "occurrences": [{key: ref[key] for key in fields} for ref in occurrences],
        }
        if is_protected(raw_hash, occurrences, protected):
            return dict(item, status="protected", lines=[])

        key = digest(json_bytes([raw_hash, png_hash, inputs]))
        cached = cache_root / (key + ".json")
        if cached.is_file():
            lines = json.loads(cached.read_bytes())
        else:
            with Image.open(png) as image:
                lines = ocr(image.convert("RGBA"), args.tesseract, args.tessdata)
            with tempfile.NamedTemporaryFile(dir=cache_root, delete=False) as staging:
                staging.write(json_bytes(lines))
            Path(staging.name).replace(cached)
        return dict(item, status=ocr_evidence(lines), lines=lines)

    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        textures = [item for item in pool.map(inspect, sorted(current.items())) if item is not None]
    return save_report(reports, {
        "mode": "ocr_inventory", "inputs": inputs, "baseline_manifest": file_digest(args.ocr_new_since),
        "current_manifest": file_digest(args.manifest),
        "counts": dict(Counter(row["status"] for row in textures)),
        "change_counts": dict(Counter(row["change"] for row in textures)), "textures": textures,
    })


def output_directories(cache_name: str) -> tuple[Path, Path]:
    cache = OUTPUT_ROOT / cache_name
    reports = OUTPUT_ROOT / "runs"
    for directory in (cache, reports):
        if directory.resolve() != directory:
            raise ValueError("Output directories must not be redirected by symlinks")
        directory.mkdir(parents=True, exist_ok=True)
    return cache, reports


def save_report(reports: Path, report: dict) -> Path:
    data = json_bytes(report)
    path = reports / (digest(data) + ".json")
    try:
        with path.open("xb") as stream:
            stream.write(data)
    except FileExistsError:
        if path.read_bytes() != data:
            raise ValueError(f"Existing report differs: {path}")
    return path


def run(args) -> Path:
    rows = json.loads(args.manifest.read_bytes())
    groups = defaultdict(list)
    by_id = defaultdict(set)
    protected = protected_hashes(args)
    for row in rows:
        raw_hash = row["sha256"]
        if not re.fullmatch("[a-f0-9]{64}", raw_hash):
            raise ValueError("Invalid source SHA-256 in scanner manifest")
        by_id[row["asset_id"]].add(raw_hash)
        groups[raw_hash].append(row)
    labels = None
    if args.benchmark:
        entries = json.loads(args.benchmark.read_bytes())
        labels = {row["sha256"]: row for row in entries}
        if len(entries) != 30 or len(labels) != 30 or not labels.keys() <= groups.keys():
            raise ValueError("Benchmark requires thirty unique source fingerprints in the selected manifest")
        hashes = sorted(labels)
    elif args.pilot:
        if any(raw_hash not in groups for raw_hash in PILOT_HASHES):
            raise ValueError("The scanner manifest is missing one or more of the ten 3O pilot textures")
        hashes = sorted(PILOT_HASHES)
    else:
        ids = args.asset or sorted(by_id)
        if any(len(by_id[asset]) != 1 for asset in ids):
            raise ValueError("An asset ID is absent or ambiguous in the selected scanner manifest")
        hashes = sorted({next(iter(by_id[asset])) for asset in ids})

    glossary = args.glossary.read_bytes()
    if args.enhanced:
        catalog = json.loads(glossary)
        catalog["categories"].update(json.loads(ARTWORK_GLOSSARY.read_bytes())["categories"])
        glossary = json_bytes(catalog)
    model_files = [args.model / "metadata.json", args.model / "sentencepiece.model",
                   *(path for path in sorted((args.model / "model").rglob("*")) if path.is_file())]
    inputs = {
        "pipeline": {name: file_digest(ROOT / name) for name in (
            "scripts/localize_textures.py", "scripts/scan_milestone3n_artwork.py",
            "scripts/extract_milestone3h_textures.py", "src/extraction/garc.py", "src/extraction/lz11.py",
            "src/rebuilding/artwork_localization.py", "src/rebuilding/textures.py", "src/rebuilding/bclim.py",
        )},
        "dependencies": {name: version(name) for name in ("Pillow", "ctranslate2", "sentencepiece")},
        "font": file_digest(args.font),
        "tesseract": file_digest(args.tesseract),
        "eng_traineddata": file_digest(args.tessdata / "eng.traineddata"),
        "glossary": digest(glossary),
        "model": {path.relative_to(args.model).as_posix(): file_digest(path) for path in model_files},
    }
    selection = None
    if args.enhanced:
        args.style_profiles, references = style_references(groups, args.style_references)
        args.fonts = [args.font, *args.match_font]
        args.paddle_recognizer = None
        inputs["enhanced"] = {
            "device": args.device, "fonts": [{"name": font.name, "sha256": file_digest(font)} for font in args.fonts],
            "rus_traineddata": file_digest(args.tessdata / "rus.traineddata"), "battle_references": references,
            "rendering": file_digest(ROOT / "src/rebuilding/artwork_rendering.py"),
            "etc_encoding": file_digest(ROOT / "src/rebuilding/etc1_encoding.py"),
        }
        if args.selected_3n.is_dir():
            selection = curated_selection(args.selected_3n, groups)
        if args.paddle_model:
            models = {file.relative_to(args.paddle_model).as_posix(): file_digest(file)
                      for file in sorted(args.paddle_model.rglob("*")) if file.is_file()}
            if not models:
                raise ValueError("A populated local PaddleOCR recognition model directory is required")
            inputs["enhanced"]["paddle"] = {"version": version("paddleocr"), "model": models,
                                            "device": args.paddle_device, "name": args.paddle_name}
            args.paddle_recognizer = local_paddle(args.paddle_model, args.paddle_name, args.paddle_device)
    cache_root, reports = output_directories("cache")
    translate = Translator(glossary, args.model, args.device)
    results = []
    for raw_hash in hashes:
        occurrences = groups[raw_hash]
        refs = [{key: row[key] for key in ("game", "version", "archive_path", "nested_member",
                                           "internal_filename", "asset_id")} for row in occurrences]
        item = {"sha256": raw_hash, "occurrences": refs}
        results.append(item)
        protected_asset = is_protected(raw_hash, occurrences, protected)
        if protected_asset and not args.benchmark:
            item.update(status="protected", reason="Manual work or an existing translation shares this hash")
            continue
        row = occurrences[0]
        real_png = scanner_png(row)
        key = digest(json_bytes([raw_hash, file_digest(real_png), inputs, protected_asset,
                                 row["internal_filename"], row.get("source_kind")]))
        destination = cache_root / key
        if not destination.exists():
            with tempfile.TemporaryDirectory(prefix=".pending-", dir=cache_root) as staging:
                stage = Path(staging) / "entry"
                stage.mkdir()
                if args.enhanced:
                    process_enhanced(row, args, translate, stage, protected=protected_asset)
                else:
                    process(row, args, translate, stage)
                try:
                    stage.rename(destination)
                except OSError:
                    if not destination.is_dir():
                        raise
        if destination.resolve() != destination:
            raise ValueError(f"Cache entry was redirected by a symlink: {destination}")
        result = json.loads((destination / "result.json").read_bytes())
        for label in ("before", "after", "draft") if "draft_sha256" in result else ("before", "after"):
            if file_digest(destination / f"{label}.png") != result[f"{label}_sha256"]:
                raise ValueError(f"Cached {label} preview was modified: {destination}")
        item.update(result, preview_directory=destination.relative_to(ROOT).as_posix())
    mode = "benchmark" if args.benchmark else "pilot" if args.pilot else "selection" if args.asset else "batch"
    report = {"inputs": inputs, "mode": mode,
              "counts": dict(Counter(item["status"] for item in results)), "textures": results}
    if selection is not None:
        report["selected_3n"] = dict(selection, benchmark_matches=len(set(hashes) & set(selection["assets"])))
    if labels is not None:
        report["benchmark"] = benchmark_scores(results, labels)
    return save_report(reports, report)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument("--pilot", action="store_true")
    selection.add_argument("--asset", action="append")
    selection.add_argument("--batch", action="store_true")
    selection.add_argument("--benchmark", type=Path, help="Annotated thirty-texture benchmark")
    parser.add_argument("--enhanced", action="store_true", help="Enable enhanced review for explicit assets")
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cpu")
    parser.add_argument("--match-font", type=Path, action="append", default=[])
    parser.add_argument("--style-references", type=Path, default=BATTLE_REFERENCES)
    parser.add_argument("--selected-3n", type=Path, default=OUTPUT / "todo")
    parser.add_argument("--paddle-model", type=Path)
    parser.add_argument("--paddle-name", default="PP-OCRv5_mobile_rec")
    parser.add_argument("--paddle-device", choices=("cpu", "gpu"), default="cpu")
    selection.add_argument("--ocr-new-since", type=Path, metavar="BASELINE_MANIFEST",
                           help="Inventory OCR evidence for new and corrected PNGs")
    parser.add_argument("--jobs", type=int, default=1, help="Number of concurrent OCR inventory workers")
    parser.add_argument("--manifest", type=Path, default=OUTPUT / "texture-manifest.json")
    parser.add_argument("--glossary", type=Path, default=ROOT / "glossary/terms.json")
    parser.add_argument("--protect", action="append", type=Path, default=[])
    parser.add_argument("--tesseract", type=Path, default=shutil.which("tesseract"))
    parser.add_argument("--tessdata", required=True, type=Path)
    parser.add_argument("--model", type=Path)
    parser.add_argument("--font", type=Path)
    args = parser.parse_args()
    if args.tesseract is None:
        parser.error("Provide --tesseract or put Tesseract on PATH")
    args.tesseract = args.tesseract.resolve(strict=True)
    if args.jobs < 1:
        parser.error("--jobs must be positive")
    args.enhanced = args.enhanced or args.benchmark is not None
    if args.enhanced and (args.batch or args.ocr_new_since):
        parser.error("Enhanced localization requires a bounded asset selection or benchmark")
    if args.ocr_new_since:
        print(ocr_inventory(args))
    else:
        if args.model is None or args.font is None:
            parser.error("Texture proposals require --model and --font")
        print(run(args))


if __name__ == "__main__":
    main()
