#!/usr/bin/env python3
"""Inspect and extract the specified Gen VI candidate GARCs into ignored build/."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.extraction.garc import GARC, extract  # noqa: E402
from src.extraction.fonts import cmap_blocks  # noqa: E402
from src.extraction.lz11 import decompress, LZ11Error  # noqa: E402
from src.extraction.messages import MessageError, TextFile  # noqa: E402

DATASETS = {
    "pokemon-x": {"base": ROOT / "workspace/pokemon-x/base", "update-1.5": ROOT / "workspace/pokemon-x/update-1.5"},
    "pokemon-y": {"base": ROOT / "workspace/pokemon-y/base", "update-1.5": ROOT / "workspace/pokemon-y/update-1.5"},
}
CANDIDATES = ("a/0/7/4", "a/0/8/2", "a/1/8/5")
BUILD_ROOT = (ROOT / "build/milestone-2a").resolve()


def inside(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def inspect_one(game: str, version: str, rel: str, source: Path) -> dict[str, object]:
    if not inside(source, ROOT / "workspace"):
        raise RuntimeError(f"Refusing source outside workspace: {source}")
    output = BUILD_ROOT / game / version / rel.replace("/", "_")
    if not inside(output, BUILD_ROOT):
        raise RuntimeError(f"Refusing output outside build root: {output}")
    raw = source.read_bytes()
    archive = GARC.parse(raw)
    rebuilt = archive.rebuild()
    if rebuilt != raw:
        raise RuntimeError(f"No-change GARC rebuild differs for {game}/{version}/{rel}")
    extract(source, output / "members")

    format_counts: dict[str, int] = {}
    text_rows = []
    font_rows = []
    malformed_text = 0
    lz_members = 0
    for member in archive.members:
        data = member.data
        if data[:1] == b"\x11":
            lz_members += 1
            try:
                data = decompress(data)
            except LZ11Error:
                pass
        signature = data[:4].decode("ascii", errors="replace") if len(data) >= 4 else ""
        if data[:4] == b"CFNT":
            kind = "CFNT"
            blocks = cmap_blocks(data)
            mapped = set().union(*(block.mapped_codepoints for block in blocks))
            font_rows.append({
                "entry_id": member.entry_id, "subfile_id": member.subfile_id,
                "size": len(data), "signature": signature, "data_sha256": hashlib.sha256(data).hexdigest(),
                "cmap_blocks": [{"offset": block.offset, "size": block.size, "start": block.start, "end": block.end, "method": block.method} for block in blocks],
                "mapped_codepoint_count": len(mapped),
                "russian_cyrillic_mapped": any(0x0400 <= cp <= 0x052F for cp in mapped),
                "yo_upper_mapped": 0x0401 in mapped, "yo_lower_mapped": 0x0451 in mapped,
            })
        else:
            try:
                text_file = TextFile.parse(data)
                kind = "Gen6_TextFile"
                text_rows.extend({
                    "game": game, "version": version, "archive": rel,
                    "entry_id": member.entry_id, "subfile_id": member.subfile_id,
                    "message_id": line.message_id, "source_member_sha256": hashlib.sha256(member.data).hexdigest(),
                    "text_file_sha256": text_file.source_sha256, "display_text": line.display_text,
                    "tokens": line.tokens, "decoded_words": line.decoded_words,
                    "encrypted_words": line.encrypted_words,
                } for line in text_file.lines)
            except MessageError:
                kind = signature if signature.isprintable() else "opaque"
                if data[:1] == b"\x01":
                    malformed_text += 1
        format_counts[kind] = format_counts.get(kind, 0) + 1

    records_path = output / "messages.jsonl"
    records_path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in text_rows), encoding="utf-8", newline="\n")
    sample_path = output / "english-sample.jsonl"
    sample = [row for row in text_rows if any(ch.isalpha() for ch in row["display_text"])][:20]
    sample_path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in sample), encoding="utf-8", newline="\n")
    font_path = output / "font-candidates.json"
    font_path.write_text(json.dumps(font_rows, indent=2, sort_keys=True), encoding="utf-8", newline="\n")
    return {
        "game": game, "version": version, "romfs_path": rel,
        "source_size": len(raw), "source_sha256": hashlib.sha256(raw).hexdigest(),
        "header_version": 4, "entries": len(archive.entries), "members": len(archive.members),
        "member_formats": format_counts, "lz11_members": lz_members,
        "parsed_message_lines": len(text_rows), "malformed_text_like_members": malformed_text,
        "font_signature_members": len(font_rows), "font_candidates": font_rows,
        "no_change_rebuild_bytes_equal": rebuilt == raw,
        "output": output.relative_to(ROOT).as_posix(),
        "sample": sample_path.relative_to(ROOT).as_posix(),
    }


def main() -> int:
    results = []
    for game, versions in DATASETS.items():
        for version, dataset in versions.items():
            for rel in CANDIDATES:
                source = dataset.joinpath(*rel.split("/"))
                if source.is_file():
                    results.append(inspect_one(game, version, rel, source))
    BUILD_ROOT.mkdir(parents=True, exist_ok=True)
    (BUILD_ROOT / "inspection.json").write_text(json.dumps(results, indent=2, sort_keys=True), encoding="utf-8", newline="\n")
    print(json.dumps(results, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
