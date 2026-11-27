#!/usr/bin/env python3
"""Read-only discovery and export of BCLIM textures in X/Y base and 1.5 RomFS."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import mmap
from pathlib import Path, PurePosixPath
import re
import struct
import sys
from collections import Counter, defaultdict

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.bch_inventory import BchInventory
from scripts.extract_milestone3h_textures import write_png
from src.rebuilding.bclim import UnsupportedBclim, decode_bclim
from src.extraction.garc import GARC
from src.extraction.lz11 import decompress as lz11_decompress
from src.rebuilding.textures import parse_texture_pack

DATASETS = (("pokemon-x", "base"), ("pokemon-x", "update-1.5"),
            ("pokemon-y", "base"), ("pokemon-y", "update-1.5"))
OUTPUT = ROOT / "build/milestone-3n/editing"
SCAN_OUTPUT = ROOT / "build/offline-textures/inventory"
TOKENS = {
    "keyboard": ("key", "input", "strinput", "keyboard", "kana", "alphabet"),
    "battle": ("battle", "fight", "bag_button", "run_button", "pokemon_button", "gauge", "type_icon"),
    "pokedex": ("dex", "pokedex", "zukan"),
    "menu": ("menu", "option", "select", "button", "command"),
    "map_sign": ("map", "sign", "route", "town", "city"),
    "logo_title": ("logo", "title", "start", "opening"),
    "social": ("pss", "friend", "amie", "super", "training", "trainer", "card"),
    "shop_bag": ("shop", "bag", "item", "category", "shop"),
}
FIELDS = ("game", "version", "archive_path", "nested_member", "internal_filename", "dimensions",
          "format", "sha256", "detected_english_text", "suggested_russian_translation",
          "confidence", "png_path", "asset_id", "source_kind", "translation_queue_status",
          "pending_translation")
M3I_EXCLUSIONS = {
    ("a/2/4/0", "fight_text.bclim"), ("a/2/4/0", "bag_button.bclim"),
    ("a/2/4/0", "pokemon_button.bclim"), ("a/2/4/0", "run_button.bclim"),
    ("a/2/4/0", "ally_gauge.bclim"), ("a/2/4/0", "enemy_gauge.bclim"),
    *(('a/2/3/9', f'type_icon_{index:02d}_{name}.bclim') for index, name in enumerate((
        'normal', 'kakutou', 'hikou', 'doku', 'jimen', 'iwa', 'mushi', 'ghost', 'hagane',
        'honoo', 'mizu', 'kusa', 'denki', 'esper', 'koori', 'dragon', 'aku', 'yousei'))),
}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_digest(path: Path) -> str:
    digestor = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digestor.update(block)
    return digestor.hexdigest()


def category_for(archive_path: str, filename: str) -> str:
    text = f"{archive_path}/{filename}".lower()
    for category, tokens in TOKENS.items():
        if any(token in text for token in tokens):
            return category
    return "unclassified_manual_review"


def _unpack(raw: bytes) -> tuple[bytes, bool]:
    if raw[:1] == b"\x11":
        return lz11_decompress(raw), True
    return raw, False


def _bclim_at_end(raw: bytes) -> bytes | None:
    footer = raw.rfind(b"CLIM")
    if footer < 0 or footer + 40 != len(raw):
        return None
    try:
        data_len = struct.unpack_from("<I", raw, footer + 36)[0]
        if data_len != footer:
            return None
        return raw
    except struct.error:
        return None


def _texture_rows(raw: bytes) -> tuple[list[dict], list[str]]:
    rows: list[dict] = []
    errors: list[str] = []
    try:
        textures = parse_texture_pack(raw)
    except (ValueError, UnicodeError, struct.error) as exc:
        textures = []
        if b"CLIM" in raw:
            errors.append(f"texture-pack index parse: {type(exc).__name__}: {exc}")
    if textures:
        rows.extend(textures)
    else:
        standalone = _bclim_at_end(raw)
        if standalone is not None:
            rows.append({"name": "[standalone].bclim", "data": standalone})
    return rows, errors


def _record_bch(data: bytes, archive: str, member: str, stats: Counter, diagnostics: list[dict],
                bch: BchInventory | None = None, was_lz11: bool = False) -> None:
    if not data.startswith(b"BCH\0"):
        return
    if bch is None:
        stats["unsupported_bch_containers"] += 1
        diagnostics.append({"archive_path": archive, "nested_member": member,
                            "reason": "BCH container header; embedded textures unsupported",
                            "sha256": digest(data)})
    else:
        stats["bch_headers"] += 1
        diagnostics.append({"archive_path": archive, "nested_member": member,
                            "bch_sha256": bch.inspect(data), "member_lz11": was_lz11})


def _walk_archive(raw: bytes, archive_path: str, member_prefix: str = "", depth: int = 0,
                  max_depth: int = 6, bch: BchInventory | None = None) -> tuple[list[dict], Counter, list[dict]]:
    textures: list[dict] = []
    stats: Counter = Counter()
    failures: list[dict] = []
    if depth > max_depth:
        failures.append({"archive_path": archive_path, "nested_member": member_prefix,
                         "reason": "maximum nested-container depth exceeded"})
        return textures, stats, failures
    try:
        archive = GARC.parse(raw)
    except (ValueError, struct.error) as exc:
        failures.append({"archive_path": archive_path, "nested_member": member_prefix,
                         "reason": f"GARC parse: {type(exc).__name__}: {exc}"})
        return textures, stats, failures
    stats["garc_archives"] += 1
    stats["garc_members"] += len(archive.members)
    for member in archive.members:
        member_id = f"{member.entry_id}/{member.subfile_id}"
        path_id = f"{member_prefix}/{member_id}".strip("/")
        was_lz = False
        try:
            decoded, was_lz = _unpack(member.data)
            if was_lz:
                stats["lz11_members"] += 1
        except (ValueError, struct.error) as exc:
            failures.append({"archive_path": archive_path, "nested_member": path_id,
                             "reason": f"LZ11 decode: {type(exc).__name__}: {exc}"})
            decoded = member.data
        if decoded.startswith(b"CRAG"):
            nested, nested_stats, nested_failures = _walk_archive(decoded, archive_path, path_id, depth + 1, max_depth, bch)
            textures.extend(nested)
            stats.update(nested_stats)
            failures.extend(nested_failures)
            continue
        _record_bch(decoded, archive_path, path_id, stats, failures, bch, was_lz)
        packs, pack_errors = _texture_rows(decoded)
        for message in pack_errors:
            failures.append({"archive_path": archive_path, "nested_member": path_id, "reason": message})
        if packs:
            stats["texture_packs"] += 1
        textures.extend(_source_texture(texture, path_id) for texture in packs)
    return textures, stats, failures


def _walk_large_archive(path: Path, archive_path: str, game: str, version: str,
                        records: list[dict], canonical_by_hash: dict[str, tuple[str, str, int, int, int]],
                        png_root: Path, bch: BchInventory | None = None) -> tuple[Counter, list[dict]]:
    """Read GARC v4 descriptors from a read-only mmap and process bounded members one at a time."""
    stats: Counter = Counter({"garc_archives": 1, "streamed_garc_archives": 1})
    failures: list[dict] = []
    with path.open("rb") as stream, mmap.mmap(stream.fileno(), 0, access=mmap.ACCESS_READ) as raw:
        if raw[:4] != b"CRAG" or len(raw) < 0x1C:
            return stats, [{"archive_path": archive_path, "nested_member": "", "reason": "invalid large GARC signature/header"}]
        header_len, bom, garc_version, chunks, data_offset, file_size, _largest = struct.unpack_from("<IHHIIII", raw, 4)
        pos = 0x1C
        if (header_len, bom, garc_version, chunks, file_size) != (0x1C, 0xFEFF, 0x0400, 4, len(raw)) or raw[pos:pos+4] != b"OTAF":
            return stats, [{"archive_path": archive_path, "nested_member": "", "reason": "unsupported/invalid large GARC header"}]
        fato_size, entry_count = struct.unpack_from("<IH", raw, pos+4)
        fatb = pos + fato_size
        if fato_size != 12 + 4 * entry_count or raw[fatb:fatb+4] != b"BTAF":
            return stats, [{"archive_path": archive_path, "nested_member": "", "reason": "invalid large GARC FATO/FATB bounds"}]
        fatb_size, reported_files = struct.unpack_from("<II", raw, fatb+4)
        fatb_end = fatb + fatb_size
        if fatb_end > data_offset or fatb_size < 12:
            return stats, [{"archive_path": archive_path, "nested_member": "", "reason": "large GARC FATB exceeds declared section bounds"}]
        q = fatb + 12
        total_members = 0
        for entry_id in range(entry_count):
            expected_offset = q - (fatb + 12)
            fato_offset = struct.unpack_from("<I", raw, pos + 12 + entry_id * 4)[0]
            if fato_offset != expected_offset:
                failures.append({"archive_path": archive_path, "nested_member": str(entry_id),
                                 "reason": "FATO entry offset does not match FATB descriptor"})
            vector = struct.unpack_from("<I", raw, q)[0]
            q += 4
            for sub_id in range(32):
                if not vector & (1 << sub_id):
                    continue
                start, end, length = struct.unpack_from("<III", raw, q)
                q += 12
                total_members += 1
                member_path = f"{entry_id}/{sub_id}"
                if not (start <= end and length <= end - start and data_offset + end <= len(raw)):
                    failures.append({"archive_path": archive_path, "nested_member": member_path,
                                     "reason": "GARC member data bounds are invalid"})
                    continue
                if length > 128 * 1024 * 1024:
                    stats["oversize_members_not_materialized"] += 1
                    failures.append({"archive_path": archive_path, "nested_member": member_path,
                                     "reason": f"member {length} bytes exceeds the 128 MiB bounded inspection limit",
                                     "size": length})
                    continue
                data = bytes(raw[data_offset+start:data_offset+start+length])
                decoded = data
                was_lz = False
                try:
                    if data[:1] == b"\x11":
                        decoded, was_lz = _unpack(data)
                        stats["lz11_members"] += 1
                except (ValueError, struct.error) as exc:
                    failures.append({"archive_path": archive_path, "nested_member": member_path,
                                     "reason": f"LZ11 decode: {type(exc).__name__}: {exc}"})
                if decoded.startswith(b"CRAG"):
                    nested, nested_stats, nested_errors = _walk_archive(decoded, archive_path, member_path, 1, bch=bch)
                    for texture in nested:
                        _append_texture(records, canonical_by_hash, png_root, game, version, archive_path, texture, stats, failures)
                    stats.update(nested_stats)
                    failures.extend(nested_errors)
                    continue
                _record_bch(decoded, archive_path, member_path, stats, failures, bch, was_lz)
                packs, pack_errors = _texture_rows(decoded)
                failures.extend({"archive_path": archive_path, "nested_member": member_path, "reason": item}
                                for item in pack_errors)
                if packs:
                    stats["texture_packs"] += 1
                for texture in packs:
                    _append_texture(records, canonical_by_hash, png_root, game, version, archive_path,
                                    _source_texture(texture, member_path), stats, failures)
        stats["garc_members"] += total_members
        if q != fatb_end or data_offset >= len(raw):
            failures.append({"archive_path": archive_path, "nested_member": "", "reason": "large GARC descriptor bounds did not terminate at FATB end"})
        if reported_files not in (total_members, entry_count):
            failures.append({"archive_path": archive_path, "nested_member": "", "reason": "GARC FATB count does not match entries or members"})
        fimg = fatb_end
        if (raw[fimg:fimg+4] != b"BMIF" or fimg + 12 != data_offset
                or struct.unpack_from("<I", raw, fimg+4)[0] != 12
                or struct.unpack_from("<I", raw, fimg+8)[0] != len(raw) - data_offset):
            failures.append({"archive_path": archive_path, "nested_member": "", "reason": "GARC BMIF bounds/count do not match archive tail"})
    return stats, failures


def _base_rows(output: Path, bch: BchInventory | None) -> tuple[list[dict], dict, list[dict]]:
    records: list[dict] = []
    totals: Counter = Counter()
    failures: list[dict] = []
    png_root = output / "png"
    png_root.mkdir(parents=True, exist_ok=True)
    canonical_by_hash: dict[str, tuple[str, str, int, int, int]] = {}
    archive_cache: dict[str, dict] = {}
    seen_archive_hashes: set[str] = set()
    cache_file = output / "scan-archive-cache-v3.jsonl"
    if bch is not None:
        # BCH detection re-inspects each distinct archive. The per-run cache
        # still reuses identical archive contents across games and versions.
        cache_file = None
    if cache_file is not None and cache_file.exists():
        for line in cache_file.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            cached_record = json.loads(line)
            archive_cache[cached_record["sha256"]] = cached_record
            for row in cached_record["rows"]:
                if not (ROOT / row["png_path"]).is_file():
                    raise ValueError("Cached scanner PNG is missing. Scan to a fresh output directory.")
                canonical_by_hash.setdefault(row["sha256"], (
                    row["asset_id"], row["png_path"], row["width"], row["height"], row["format"],
                ))
    for game, version in DATASETS:
        root = ROOT / "workspace" / game / version
        if not root.is_dir():
            raise FileNotFoundError(f"Required read-only RomFS dataset missing: {root}")
        for path in sorted(item for item in root.rglob("*") if item.is_file()):
            totals["source_files"] += 1
            relative = path.relative_to(root).as_posix()
            size = path.stat().st_size
            totals["source_bytes"] += size
            with path.open("rb") as source_stream:
                prefix = source_stream.read(4)
            if prefix == b"CRAG":
                archive_sha256 = file_digest(path)
                if archive_sha256 in seen_archive_hashes:
                    totals["identical_garc_archives_reused"] += 1
                seen_archive_hashes.add(archive_sha256)
                totals["source_archive_bytes_sha256_verified"] += size
                cached = archive_cache.get(archive_sha256)
                if cached is not None:
                    for original in cached["rows"]:
                        reused = dict(original)
                        reused.update({"game": game, "version": version, "archive_path": relative})
                        records.append(reused)
                    totals["archive_cache_hits"] += 1
                    totals.update(cached["stats"])
                    failures.extend({**row, "game": game, "version": version, "archive_path": relative}
                                    for row in cached["failures"])
                    continue
                records_start = len(records)
                stats, errors = _walk_large_archive(path, relative, game, version, records,
                                                    canonical_by_hash, png_root, bch)
                totals.update(stats)
                for row in errors:
                    if "bch_sha256" in row:
                        row["archive_sha256"] = archive_sha256
                failures.extend({"game": game, "version": version, **row} for row in errors)
                cached_rows = [dict(row) for row in records[records_start:]]
                archive_cache[archive_sha256] = {"sha256": archive_sha256, "rows": cached_rows,
                                                 "stats": dict(stats), "failures": errors}
                if cache_file is not None:
                    with cache_file.open("a", encoding="utf-8", newline="\n") as cache_stream:
                        cache_stream.write(json.dumps(archive_cache[archive_sha256],
                                                      ensure_ascii=False, sort_keys=True) + "\n")
                continue
            if size > 128 * 1024 * 1024:
                totals["oversize_non_garc_files_not_parsed"] += 1
                failures.append({"game": game, "version": version, "archive_path": relative,
                                 "nested_member": "", "reason": f"oversize non-GARC source ({size} bytes) not parsed"})
                continue
            raw = path.read_bytes()
            totals["non_garc_source_bytes_scanned"] += len(raw)
            scan_data = raw
            was_lz = False
            try:
                if raw[:1] == b"\x11":
                    scan_data, was_lz = _unpack(raw)
                    totals["lz11_files"] += 1
            except (ValueError, struct.error) as exc:
                totals["top_level_decompression_failures"] += 1
                failures.append({"game": game, "version": version, "archive_path": relative,
                                 "nested_member": "", "reason": f"top-level LZ11 decode: {type(exc).__name__}: {exc}"})
            for signature, label in ((b"BCH", "bch_magic_occurrences"), (b"CFNT", "cfnt_magic_occurrences"),
                                     (b"CGFX", "cgfx_magic_occurrences"), (b"BCMDL", "bcmdl_magic_occurrences"),
                                     (b"CLIM", "clim_magic_occurrences")):
                totals[label] += raw.count(signature)
            if bch is not None:
                bch.record_incidental(raw, game, version, relative)
            if scan_data.startswith(b"BCH\0"):
                hits = []
                _record_bch(scan_data, relative, "", totals, hits, bch, was_lz)
                failures.extend(dict(hit, game=game, version=version, archive_sha256=digest(raw)) for hit in hits)
            if scan_data.startswith(b"CRAG"):
                textures, stats, errors = _walk_archive(scan_data, relative, bch=bch)
                totals.update(stats)
                for row in errors:
                    if "bch_sha256" in row:
                        row["archive_sha256"] = digest(raw)
                        row["outer_lz11"] = was_lz
                failures.extend({"game": game, "version": version, **row} for row in errors)
                for texture in textures:
                    _append_texture(records, canonical_by_hash, png_root, game, version, relative, texture, totals, failures)
            elif path.suffix.lower() == ".bclim" or _bclim_at_end(scan_data) is not None:
                totals["standalone_bclim_candidates"] += 1
                _append_texture(records, canonical_by_hash, png_root, game, version, relative,
                                {"nested_member": "", "internal_filename": path.name, "raw": scan_data,
                                 "source_kind": "standalone BCLIM"}, totals, failures)
    totals["archive_content_hashes_unique"] = len(seen_archive_hashes)
    return records, dict(totals), failures


def _source_texture(texture: dict, member: str) -> dict:
    return {"nested_member": member, "internal_filename": texture["name"],
            "raw": texture["data"], "source_kind": "BCLIM"}


def _append_texture(records: list[dict], canonical_by_hash: dict[str, tuple[str, str, int, int, int]], png_root: Path,
                    game: str, version: str, archive: str, texture: dict, stats: Counter, failures: list[dict]) -> None:
    raw = texture["raw"]
    tex_hash = digest(raw)
    stats["bclim_members"] += 1
    if tex_hash not in canonical_by_hash:
        try:
            width, height, fmt, rgba = decode_bclim(raw)
        except ValueError as exc:
            status = "unsupported" if isinstance(exc, UnsupportedBclim) else "failed"
            stats[f"{status}_bclim"] += 1
            fmt = struct.unpack_from("<I", raw, len(raw) - 8)[0] if raw[-40:-36] == b"CLIM" else None
            failures.append({"game": game, "version": version, "archive_path": archive, "nested_member": texture["nested_member"],
                             "internal_filename": texture["internal_filename"], "format": fmt,
                             "bclim_status": status, "reason": f"BCLIM decode: {exc}", "sha256": tex_hash})
            return
        asset_id = f"T{len(canonical_by_hash) + 1:06d}"
        safe_name = re.sub(r"[^A-Za-z0-9_.-]+", "_", texture["internal_filename"])
        png_path = png_root / f"{asset_id}_{tex_hash[:12]}_{safe_name}.png"
        write_png(png_path, width, height, rgba)
        canonical_by_hash[tex_hash] = (asset_id, png_path.relative_to(ROOT).as_posix(), width, height, fmt)
    asset_id, relative_png, width, height, fmt = canonical_by_hash[tex_hash]
    stats["decoded_bclim"] += 1
    filename = texture["internal_filename"]
    category = category_for(archive, filename)
    resource = archive if archive in {"a/2/4/0", "a/2/3/9"} else ""
    source_member = texture["nested_member"].split("/")[-2:]
    known_translated = (resource, filename) in M3I_EXCLUSIONS and source_member == ["0", "2"]
    english_markers = [term for term in re.findall(r"[A-Za-z]{3,}", filename)
                       if term.lower() not in {"bclim", "icon", "button", "normal"}]
    confidence = "medium" if english_markers or category != "unclassified_manual_review" else "low"
    records.append({"game": game, "version": version, "archive_path": archive,
                    "nested_member": texture["nested_member"], "internal_filename": filename,
                    "dimensions": f"{width}x{height}",
                    "width": width, "height": height, "format": fmt,
                    "sha256": tex_hash,
                    "detected_english_text": "filename tokens: " + ", ".join(english_markers) if english_markers else "not OCR-verified; visual review required",
                    "suggested_russian_translation": "", "confidence": confidence,
                    "png_path": relative_png, "asset_id": asset_id, "source_kind": texture["source_kind"],
                    "category": category, "suspected_english_artwork": True,
                    "translation_queue_status": "excluded_already_translated_m3i" if known_translated else "manual_review_pending",
                    "pending_translation": not known_translated})


def _save_contact_sheets(rows: list[dict], output: Path, tile: tuple[int, int] = (220, 170),
                         per_sheet: int = 80) -> list[str]:
    from PIL import Image, ImageDraw, ImageFont

    sheet_dir = output / "contact-sheets"
    sheet_dir.mkdir(parents=True, exist_ok=True)
    groups: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        groups[row["category"]].append(row)
    outputs = []
    font = ImageFont.load_default()
    for category, group in sorted(groups.items()):
        group.sort(key=lambda row: row["asset_id"])
        for batch_no, start in enumerate(range(0, len(group), per_sheet), 1):
            batch = group[start:start + per_sheet]
            columns = 4
            rows_count = (len(batch) + columns - 1) // columns
            sheet = Image.new("RGBA", (columns * tile[0], rows_count * tile[1]), (238, 238, 238, 255))
            draw = ImageDraw.Draw(sheet)
            for offset, item in enumerate(batch):
                x, y = (offset % columns) * tile[0], (offset // columns) * tile[1]
                image = Image.open(ROOT / item["png_path"]).convert("RGBA")
                image.thumbnail((tile[0] - 12, tile[1] - 54), Image.Resampling.NEAREST)
                sheet.alpha_composite(image, (x + (tile[0] - image.width) // 2, y + 4))
                label = f"{item['asset_id']} | {item['game'][-1].upper()} {item['version']}"
                filename = item["internal_filename"]
                draw.text((x + 4, y + tile[1] - 46), label[:34], fill=(0, 0, 0, 255), font=font)
                draw.text((x + 4, y + tile[1] - 31), filename[:34], fill=(0, 0, 0, 255), font=font)
                draw.text((x + 4, y + tile[1] - 16), f"{item['width']}x{item['height']} {item['format']}",
                          fill=(0, 0, 0, 255), font=font)
            name = f"{category}-{batch_no:03d}.png"
            target = sheet_dir / name
            sheet.save(target, format="PNG", optimize=False)
            outputs.append(target.relative_to(ROOT).as_posix())
    return outputs


def unsupported_formats(failures: list[dict]) -> dict:
    groups = defaultdict(list)
    for row in failures:
        reason = row["reason"]
        if reason.startswith("BCH container header"):
            groups["BCH header"].append(row)
        elif reason.startswith("BCLIM decode"):
            fmt = row.get("format")
            groups[f"BCLIM {fmt}" if fmt is not None else "BCLIM unknown format"].append(row)
    return {label: {"occurrences": len(rows), "locations": rows} for label, rows in sorted(groups.items())}


def _generated_output(output: Path) -> Path:
    output = output.resolve()
    if ROOT / "build" not in output.parents:
        raise ValueError("Scanner output must be in a dedicated directory under build/")
    if any(path.is_symlink() for path in output.rglob("*")):
        raise ValueError("Scanner output must not contain symlinks")
    return output


def scan(output: Path = SCAN_OUTPUT, *, include_bch: bool = False) -> dict:
    output = _generated_output(output)
    bch = BchInventory(output, ROOT) if include_bch else None
    records, totals, failures = _base_rows(output, bch)
    if bch is not None:
        occurrences = [row for row in failures if "bch_sha256" in row]
        failures = [row for row in failures if "bch_sha256" not in row]
        bch_report = bch.publish(occurrences)
        for game, version in DATASETS:
            bch_report["container_occurrences_by_dataset"].setdefault(f"{game}/{version}", {"headers": 0})
    hash_counts = Counter(row["sha256"] for row in records)
    for row in records:
        row["deduplicated_source_count"] = hash_counts[row["sha256"]]
    contact_sheets = _save_contact_sheets(list({row["asset_id"]: row for row in records}.values()), output)
    json_path = output / "texture-manifest.json"
    csv_path = output / "texture-manifest.csv"
    json_path.write_text(json.dumps(records, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
                         encoding="utf-8", newline="\n")
    with csv_path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=(*FIELDS, "width", "height", "category",
                                                     "suspected_english_artwork", "deduplicated_source_count"))
        writer.writeheader()
        writer.writerows(records)
    unique = len({row["asset_id"] for row in records})
    bclim_by_dataset = {}
    for game, version in DATASETS:
        counts = Counter({"decoded": 0, "unsupported": 0, "failed": 0})
        counts["decoded"] = sum((row["game"], row["version"]) == (game, version) for row in records)
        counts.update(row["bclim_status"] for row in failures
                      if "bclim_status" in row and (row["game"], row["version"]) == (game, version))
        bclim_by_dataset[f"{game}/{version}"] = dict(counts)
    for status in ("decoded", "unsupported", "failed"):
        totals.setdefault(f"{status}_bclim", 0)
    report = {"milestone": "3Q" if include_bch else "3P", "bclim_by_dataset": bclim_by_dataset, "source_datasets": [
        {"game": game, "version": version, "path": (ROOT / "workspace" / game / version).relative_to(ROOT).as_posix()}
        for game, version in DATASETS], "coverage": totals, "texture_provenance_rows": len(records),
        "unique_bclim_images_by_raw_sha256": unique, "duplicates_collapsed_for_png": len(records) - unique,
        "pending_translation_texture_occurrences": sum(row["pending_translation"] for row in records),
        "excluded_milestone3i_texture_occurrences": sum(not row["pending_translation"] for row in records),
        "unsupported_or_failed_count": len(failures), "failures": failures,
        "ocr": {"performed": False, "reason": "Discovery uses filename hints. Run localize_textures.py for OCR and proposal generation."},
        "scope_warning": "Not exhaustive: only top-level GARC files, direct/nested GARC members, LZ11-decompressed members, and recognized standalone BCLIM were parsed. Other archive/container/compression/texture/layout formats and BCH-embedded textures remain unresolved.",
        "output_root": output.relative_to(ROOT).as_posix(), "json_manifest": json_path.relative_to(ROOT).as_posix(),
        "csv_manifest": csv_path.relative_to(ROOT).as_posix(), "contact_sheets": contact_sheets,
        "pngs_metadata_free_rgba": True}
    if bch is not None:
        report["bch"] = bch_report
        report["scope_warning"] = ("Recognizes BCH headers at inspected file and expanded GARC member starts. "
                                   "Other container layouts and BCH nested inside unrecognized data remain outside coverage.")
    (output / "scan-report.json").write_text(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
                                              encoding="utf-8", newline="\n")
    (output / "unsupported-formats.json").write_text(
        json.dumps(unsupported_formats(failures), sort_keys=True, indent=2) + "\n", encoding="utf-8", newline="\n")
    return report


def annotate_existing(output: Path = OUTPUT) -> dict:
    """Add M3I exclusion metadata after a scan run whose worker started before this feature existed."""
    output = _generated_output(output)
    manifest = output / "texture-manifest.json"
    rows = json.loads(manifest.read_text(encoding="utf-8"))
    for row in rows:
        resource = row["archive_path"] if row["archive_path"] in {"a/2/4/0", "a/2/3/9"} else ""
        member = row["nested_member"].split("/")[-2:]
        excluded = (resource, row["internal_filename"]) in M3I_EXCLUSIONS and member == ["0", "2"]
        row["translation_queue_status"] = "excluded_already_translated_m3i" if excluded else "manual_review_pending"
        row["pending_translation"] = not excluded
    manifest.write_text(json.dumps(rows, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
                        encoding="utf-8", newline="\n")
    fields = (*FIELDS, "width", "height", "category", "suspected_english_artwork", "deduplicated_source_count")
    with (output / "texture-manifest.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    report_path = output / "scan-report.json"
    if report_path.exists():
        report = json.loads(report_path.read_text(encoding="utf-8"))
        report["pending_translation_texture_occurrences"] = sum(row["pending_translation"] for row in rows)
        report["excluded_milestone3i_texture_occurrences"] = sum(not row["pending_translation"] for row in rows)
        report["contact_sheets"] = _save_contact_sheets(list({row["asset_id"]: row for row in rows}.values()), output)
        report_path.write_text(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
                               encoding="utf-8", newline="\n")
    return {"rows": len(rows), "pending": sum(row["pending_translation"] for row in rows),
            "excluded": sum(not row["pending_translation"] for row in rows)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--bch", action="store_true", help="Validate BCH and export its PICA surfaces")
    parser.add_argument("--annotate-existing", action="store_true",
                        help="Add queue/exclusion metadata to completed manifests without rescanning assets")
    args = parser.parse_args()
    if args.annotate_existing:
        print(json.dumps(annotate_existing(args.output or OUTPUT), sort_keys=True, indent=2))
        return 0
    if args.bch and args.output is None:
        parser.error("--bch requires a dedicated --output directory under build/")
    result = scan(args.output or SCAN_OUTPUT, include_bch=args.bch)
    if args.bch:
        print(json.dumps(result["bch"], indent=2, sort_keys=True))
    print(json.dumps({key: result[key] for key in ("coverage", "texture_provenance_rows",
          "unique_bclim_images_by_raw_sha256", "duplicates_collapsed_for_png", "unsupported_or_failed_count",
          "json_manifest", "csv_manifest", "output_root")}, ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
