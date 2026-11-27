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

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.scan_milestone3n_artwork import DATASETS, OUTPUT, _texture_rows, _unpack, digest, file_digest
from src.extraction.garc import GARC
from src.rebuilding.artwork_localization import ReviewRequired, Translator, ocr, render
from src.rebuilding.textures import decode_bclim, encode_bclim

OUTPUT_ROOT = ROOT / "build/offline-textures"
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
    if args.pilot:
        if any(raw_hash not in groups for raw_hash in PILOT_HASHES):
            raise ValueError("The scanner manifest is missing one or more of the ten 3O pilot textures")
        hashes = sorted(PILOT_HASHES)
    else:
        ids = args.asset or sorted(by_id)
        if any(len(by_id[asset]) != 1 for asset in ids):
            raise ValueError("An asset ID is absent or ambiguous in the selected scanner manifest")
        hashes = sorted({next(iter(by_id[asset])) for asset in ids})

    glossary = args.glossary.read_bytes()
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
    cache_root, reports = output_directories("cache")
    translate = Translator(glossary, args.model)
    results = []
    for raw_hash in hashes:
        occurrences = groups[raw_hash]
        refs = [{key: row[key] for key in ("game", "version", "archive_path", "nested_member",
                                           "internal_filename", "asset_id")} for row in occurrences]
        item = {"sha256": raw_hash, "occurrences": refs}
        results.append(item)
        if is_protected(raw_hash, occurrences, protected):
            item.update(status="protected", reason="Manual work or an existing translation shares this hash")
            continue
        row = occurrences[0]
        real_png = scanner_png(row)
        key = digest(json_bytes([raw_hash, file_digest(real_png), inputs]))
        destination = cache_root / key
        if not destination.exists():
            with tempfile.TemporaryDirectory(prefix=".pending-", dir=cache_root) as staging:
                stage = Path(staging) / "entry"
                stage.mkdir()
                process(row, args, translate, stage)
                try:
                    stage.rename(destination)
                except OSError:
                    if not destination.is_dir():
                        raise
        if destination.resolve() != destination:
            raise ValueError(f"Cache entry was redirected by a symlink: {destination}")
        result = json.loads((destination / "result.json").read_bytes())
        for label in ("before", "after"):
            if file_digest(destination / f"{label}.png") != result[f"{label}_sha256"]:
                raise ValueError(f"Cached {label} preview was modified: {destination}")
        item.update(result, preview_directory=destination.relative_to(ROOT).as_posix())
    report = {"inputs": inputs, "mode": "pilot" if args.pilot else "selection" if args.asset else "batch",
              "counts": dict(Counter(item["status"] for item in results)), "textures": results}
    return save_report(reports, report)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument("--pilot", action="store_true")
    selection.add_argument("--asset", action="append")
    selection.add_argument("--batch", action="store_true")
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
    if args.ocr_new_since:
        print(ocr_inventory(args))
    else:
        if args.model is None or args.font is None:
            parser.error("Texture proposals require --model and --font")
        print(run(args))


if __name__ == "__main__":
    main()
