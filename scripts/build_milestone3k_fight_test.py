#!/usr/bin/env python3
"""Prepare and build a disposable Russian FIGHT-label texture proof."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.build_milestone3i_textures import _effective, _member_pack
from scripts.extract_milestone3h_textures import TITLE_IDS, write_png
from src.extraction.garc import GARC
from src.rebuilding.textures import (decode_bclim, encode_bclim, parse_texture_pack,
                                     read_png_rgba, replace_archive_member, replace_texture_pack, sha256)

CANONICAL = ROOT / "build/milestone-3i/editing/fight_text.bclim.png"
TEST_ROOT = ROOT / "build/milestone-3k/fight-artwork-test"
PNG_PATH = TEST_ROOT / "fight_text.bclim.png"
MANIFEST_PATH = TEST_ROOT / "manifest.json"
RESOURCE = "a/2/4/0"
MEMBER_KEY = (0, 2)
TEXTURE_NAME = "fight_text.bclim"
GLYPHS = {
    "\u0411": ("11111", "10000", "10000", "11110", "10001", "10001", "11110"),
    "\u041e": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "\u0418": ("10001", "10011", "10101", "10101", "11001", "10001", "10001"),
}
BREVE = ("00100", "01010")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def render_boi(source_rgba: bytes, width: int, height: int) -> bytes:
    """Replace only the source word pixels with a compact, red, pixel-style label."""
    rgba = bytearray(source_rgba)
    # The source label's antialiased red/dark pixels have green below 200; the pale
    # pink/white source backing is retained. Clearing is constrained to its ink mask.
    for offset in range(0, len(rgba), 4):
        if rgba[offset + 3] and rgba[offset + 1] < 200:
            rgba[offset:offset + 4] = b"\xff\xee\xee\x00"

    scale, gap = 3, 1
    cell_width = len(GLYPHS["\u0411"][0])
    word_units = cell_width * 3 + gap * 2
    origin_x = (width - word_units * scale) // 2
    glyph_y = 15

    def paint_pixel(px: int, py: int, color: tuple[int, int, int, int]) -> None:
        if 0 <= px < width and 0 <= py < height:
            i = (py * width + px) * 4
            rgba[i:i + 4] = bytes(color)

    def paint_pattern(pattern: tuple[str, ...], x0: int, y0: int) -> None:
        filled = {(x * scale + dx, y * scale + dy)
                  for y, row in enumerate(pattern) for x, bit in enumerate(row) if bit == "1"
                  for dy in range(scale) for dx in range(scale)}
        outline = {(x + dx, y + dy) for x, y in filled
                   for dx in (-1, 0, 1) for dy in (-1, 0, 1)}
        for x, y in outline - filled:
            paint_pixel(x0 + x, y0 + y, (68, 0, 0, 255))
        for x, y in filled:
            paint_pixel(x0 + x, y0 + y, (153, 0, 0, 255))

    for index, character in enumerate("\u0411\u041e\u0419"):
        x = origin_x + index * (cell_width + gap) * scale
        if character == "\u0419":
            paint_pattern(BREVE, x, 9)
        paint_pattern(GLYPHS["\u0418"] if character == "\u0419" else GLYPHS[character], x, glyph_y)
    return bytes(rgba)


def prepare_png(test_root: Path = TEST_ROOT, source_path: Path = CANONICAL) -> dict[str, object]:
    source_png = source_path.read_bytes()
    width, height, source_rgba = read_png_rgba(source_path)
    rendered = render_boi(source_rgba, width, height)
    destination = test_root / "fight_text.bclim.png"
    test_root.mkdir(parents=True, exist_ok=True)
    write_png(destination, width, height, rendered)
    read_width, read_height, result_rgba = read_png_rgba(destination)
    if (read_width, read_height) != (width, height) or result_rgba != rendered:
        raise ValueError("Disposable Russian label PNG failed RGBA read-back")
    # Preserve an RGBA image with real transparent background and opaque glyph pixels.
    alpha = rendered[3::4]
    if 0 not in alpha or 255 not in alpha:
        raise ValueError("Disposable artwork lost transparent background or opaque label pixels")
    display_path = (destination.relative_to(ROOT).as_posix() if ROOT.resolve() in destination.resolve().parents
                    else destination.name)
    return {"source_png_sha256": sha(source_png), "test_png_sha256": sha(destination.read_bytes()),
            "width": width, "height": height, "rgba8": True, "label": "\u0411\u041e\u0419",
            "canonical_png_modified": False, "test_png": display_path}


def build_candidate(test_root: Path = TEST_ROOT,
                    output_root: Path = ROOT / "build/milestone-3k/image-candidate") -> dict[str, object]:
    png = test_root / "fight_text.bclim.png"
    if not png.is_file():
        raise FileNotFoundError("Run --prepare first to create the disposable PNG")
    manifest = json.loads((test_root / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("label") != "\u0411\u041e\u0419" or manifest.get("canonical_png_modified") is not False:
        raise ValueError("Unexpected or unsafe disposable artwork manifest")
    width, height, rgba = read_png_rgba(png)
    if (width, height) != (manifest["width"], manifest["height"]):
        raise ValueError("Disposable PNG dimensions changed")
    if sha(png.read_bytes()) != manifest["test_png_sha256"]:
        raise ValueError("Disposable PNG differs from its recorded hash; re-run --prepare to reset it")

    output_records = []
    for game, title_id in TITLE_IDS.items():
        source_path, version = _effective(game, RESOURCE)
        source_archive = source_path.read_bytes()
        if version != "base":
            raise ValueError(f"Unexpected effective texture resource version for {game}: {version}")
        pack, _compressed_member, _was_compressed = _member_pack(source_archive, MEMBER_KEY)
        source_textures = parse_texture_pack(pack)
        source_texture = next(row for row in source_textures if row["name"] == TEXTURE_NAME)
        sw, sh, fmt, _pixels = decode_bclim(source_texture["data"])
        if (sw, sh) != (width, height) or fmt != 8:
            raise ValueError(f"fight_text source dimensions/format changed: {sw}x{sh} format {fmt}")
        encoded = encode_bclim(rgba, width, height, source_texture["data"])
        rw, rh, rfmt, decoded = decode_bclim(encoded)
        if (rw, rh, rfmt) != (width, height, fmt):
            raise ValueError("Rebuilt BCLIM metadata mismatch")
        if max((abs(a - b) for a, b in zip(rgba, decoded)), default=0) > 8:
            raise ValueError("Rebuilt BCLIM pixels exceed RGBA4444 quantization tolerance")
        patched_pack = replace_texture_pack(pack, {TEXTURE_NAME: encoded})
        for before in source_textures:
            after = next(row for row in parse_texture_pack(patched_pack) if row["name"] == before["name"])
            if before["name"] != TEXTURE_NAME and after["data"] != before["data"]:
                raise ValueError(f"Unrelated texture changed: {before['name']}")
        rebuilt_archive, archive_proof = replace_archive_member(source_archive, MEMBER_KEY, patched_pack)
        original = GARC.parse(source_archive)
        rebuilt = GARC.parse(rebuilt_archive)
        old_members = {(m.entry_id, m.subfile_id): m.data for m in original.members}
        new_members = {(m.entry_id, m.subfile_id): m.data for m in rebuilt.members}
        if old_members.keys() != new_members.keys():
            raise ValueError("GARC member coordinates changed")
        for key, data in old_members.items():
            if key != MEMBER_KEY and new_members[key] != data:
                raise ValueError(f"Unrelated GARC member changed: {key}")
        if rebuilt.rebuild() != rebuilt_archive:
            raise ValueError("Rebuilt GARC no-change round trip failed")

        destination = output_root / game / "romfs" / Path(*RESOURCE.split("/"))
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(rebuilt_archive)
        output_records.append({"game": game, "title_id": title_id, "resource": RESOURCE,
                               "source_version": version, "source_sha256": sha(source_archive),
                               "output_path": destination.relative_to(output_root).as_posix(),
                               "output_sha256": sha(rebuilt_archive), "png_sha256": sha(png.read_bytes()),
                               "bclim_format": fmt, "dimensions": [width, height],
                               "modified_texture": TEXTURE_NAME, "garc_members": len(old_members),
                               "unchanged_garc_members_verified": len(old_members) - 1,
                               "unchanged_textures_verified": len(source_textures) - 1,
                               "max_channel_delta": max(abs(a - b) for a, b in zip(rgba, decoded)),
                               **archive_proof})
    result = {"milestone": "3K", "build_state": "disposable_uninstalled_battle_art_test",
              "installed": False, "runtime_tested": False, "original_assets_modified": False,
              "canonical_png_modified": False, "manifest": manifest, "games": output_records}
    output_root.mkdir(parents=True, exist_ok=True)
    (output_root / "manifest.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n",
                                                encoding="utf-8", newline="\n")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--prepare", action="store_true")
    modes.add_argument("--build", action="store_true")
    args = parser.parse_args()
    if args.prepare:
        metadata = prepare_png()
        MANIFEST_PATH.write_text(json.dumps(metadata, sort_keys=True, indent=2) + "\n",
                                 encoding="utf-8", newline="\n")
        result = metadata
    else:
        result = build_candidate()
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
