#!/usr/bin/env python3
"""Extract selected Gen VI UI BCLIM images as ignored, editable PNG files."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.extraction.garc import GARC
from src.extraction.lz11 import decompress

TITLE_IDS = {"pokemon-x": "0004000000055D00", "pokemon-y": "0004000000055E00"}
TARGETS = {
    "a/0/0/5": {
        "0/0": {"fight_button.bclim", "fight_text.bclim", "bag_button.bclim", "run_button.bclim", "pokemon_button.bclim"},
        "12/0": {"category_ball.bclim", "category_battle.bclim", "category_button.bclim", "category_hp.bclim", "category_status.bclim"},
    },
    "a/2/4/0": {"*": {"fight_text.bclim", "bag_button.bclim", "run_button.bclim", "pokemon_button.bclim", "ally_gauge.bclim", "enemy_gauge.bclim", "move_button.bclim"}},
    "a/2/3/9": {"0/2": {"eng.bclim", *{f"type_icon_{index:02d}_{name}.bclim" for index, name in enumerate((
        "normal", "kakutou", "hikou", "doku", "jimen", "iwa", "mushi", "ghost", "hagane",
        "honoo", "mizu", "kusa", "denki", "esper", "koori", "dragon", "aku", "yousei"))}}},
    "a/0/6/3": {"0/0": set()},
    # Name-entry layout graphics live in member 0/0. Key labels are dynamically
    # rendered; these are the background/button/mode textures, not a Cyrillic
    # input implementation.
    "a/0/1/9": {"0/0": {"base.bclim", "button01.bclim", "button02.bclim", "button02_lb.bclim",
                           "button02_lt.bclim", "cursor.bclim", "icon_delete.bclim", "icon_return.bclim",
                           "line.bclim", "mode03.bclim", "obon.bclim", "plate.bclim", "strinput_bg.bclim"}},
}


def _png_chunk(kind: bytes, payload: bytes) -> bytes:
    body = kind + payload
    return struct.pack(">I", len(payload)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)


def write_png(path: Path, width: int, height: int, rgba: bytes) -> None:
    if len(rgba) != width * height * 4:
        raise ValueError("RGBA byte count does not match dimensions")
    rows = b"".join(b"\x00" + rgba[y * width * 4:(y + 1) * width * 4] for y in range(height))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + _png_chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)) +
                     _png_chunk(b"IDAT", zlib.compress(rows, 9)) + _png_chunk(b"IEND", b""))


def _morton_xy(value: int) -> tuple[int, int]:
    x = y = 0
    for bit in range(3):
        x |= ((value >> (2 * bit)) & 1) << bit
        y |= ((value >> (2 * bit + 1)) & 1) << bit
    return x, y


def _expand5(value: int) -> int:
    return (value << 3) | (value >> 2)


def _color(pixel: bytes, fmt: int) -> tuple[int, int, int, int]:
    if fmt == 9:
        value = int.from_bytes(pixel, "little")
        return ((value >> 24) & 255, (value >> 16) & 255, (value >> 8) & 255, value & 255)
    value = int.from_bytes(pixel, "little")
    if fmt == 8:
        return (((value >> 12) & 15) * 17, ((value >> 8) & 15) * 17, ((value >> 4) & 15) * 17, (value & 15) * 17)
    if fmt == 7:
        return (_expand5((value >> 11) & 31), _expand5((value >> 6) & 31), _expand5((value >> 1) & 31), 255 if value & 1 else 0)
    raise ValueError(f"Unsupported image format {fmt}; PNG not emitted")


def decode_bclim(raw: bytes) -> tuple[int, int, int, bytes]:
    clim = raw.rfind(b"CLIM")
    if clim < 0 or clim + 40 != len(raw):
        raise ValueError("BCLIM footer not at expected final 40-byte position")
    if raw[clim + 4:clim + 6] != b"\xff\xfe":
        raise ValueError("Unsupported BCLIM byte order")
    width, height, fmt, data_length = struct.unpack_from("<HHII", raw, clim + 28)
    if not width or not height or data_length != clim:
        if data_length != clim:
            raise ValueError(f"BCLIM pixel region length {data_length} does not end at footer offset {clim}")
        raise ValueError("Invalid BCLIM dimensions")
    if fmt not in (7, 8, 9):
        raise ValueError(f"BCLIM format {fmt} needs another decoder")
    data = raw[:data_length]
    bytes_per_pixel = 4 if fmt == 9 else 2
    padded_w = 1 << (width - 1).bit_length()
    padded_h = 1 << (height - 1).bit_length()
    if fmt == 9 and padded_w * padded_h > len(data) // 4:
        padded_w = (width + 7) & ~7
        padded_h = (height + 7) & ~7
    if len(data) != padded_w * padded_h * bytes_per_pixel:
        raise ValueError(f"Unsupported padded BCLIM dimensions: {width}x{height}, format {fmt}, bytes {len(data)}")
    tiles_per_row = padded_w // 8
    rgba = bytearray(width * height * 4)
    tile_pixel_bytes = 64 * bytes_per_pixel
    for index in range(padded_w * padded_h):
        tile = index // 64
        tx, ty = _morton_xy(index % 64)
        x = (tile % tiles_per_row) * 8 + tx
        y = (tile // tiles_per_row) * 8 + ty
        if x >= width or y >= height:
            continue
        at = tile * tile_pixel_bytes + (index % 64) * bytes_per_pixel
        rgba_at = (y * width + x) * 4
        rgba[rgba_at:rgba_at + 4] = bytes(_color(data[at:at + bytes_per_pixel], fmt))
    return width, height, fmt, bytes(rgba)


def _bundle(raw: bytes) -> list[tuple[str, bytes]]:
    if len(raw) < 4:
        raise ValueError("Truncated packed resource")
    count = struct.unpack_from("<I", raw)[0]
    if count > 2048 or 4 + count * 128 > len(raw):
        raise ValueError("Unrecognized packed-resource name/index table")
    names = [raw[4 + i * 64:4 + (i + 1) * 64].split(b"\0", 1)[0].decode("ascii") for i in range(count)]
    image_names = [name for name in names if name.lower().endswith(".bclim")]
    clims = []
    cursor = 0
    while True:
        cursor = raw.find(b"CLIM", cursor)
        if cursor < 0:
            break
        if cursor + 40 <= len(raw):
            try:
                total_length = struct.unpack_from("<I", raw, cursor + 12)[0]
                width, height, fmt, data_length = struct.unpack_from("<HHII", raw, cursor + 28)
                if total_length == data_length + 40 and width and height and cursor >= data_length:
                    clims.append((cursor, width, height, fmt))
            except struct.error:
                pass
        cursor += 4
    if len(image_names) != len(clims):
        raise ValueError(f"BCLIM names ({len(image_names)}) do not match CLIM records ({len(clims)})")
    return [(name, raw[pos - struct.unpack_from("<I", raw, pos + 36)[0]:pos + 40]) for name, (pos, *_rest) in zip(image_names, clims)]


def extract(root: Path, output: Path) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    rows: list[dict[str, object]] = []
    unsupported: list[dict[str, object]] = []
    for game, title_id in TITLE_IDS.items():
        base = root / "workspace" / game / "base"
        for resource, member_rules in TARGETS.items():
            archive_path = base.joinpath(*resource.split("/"))
            archive_raw = archive_path.read_bytes()
            archive_hash = hashlib.sha256(archive_raw).hexdigest()
            archive = GARC.parse(archive_raw)
            for member in archive.members:
                key = f"{member.entry_id}/{member.subfile_id}"
                requested = member_rules.get(key, member_rules.get("*"))
                if requested is None:
                    continue
                expanded = decompress(member.data) if member.data[:1] == b"\x11" else member.data
                for name, bclim in _bundle(expanded):
                    if name not in requested:
                        continue
                    try:
                        width, height, fmt, rgba = decode_bclim(bclim)
                    except ValueError as error:
                        if "needs another decoder" not in str(error):
                            raise
                        clim = bclim.rfind(b"CLIM")
                        width, height, fmt = struct.unpack_from("<HHI", bclim, clim + 28)
                        unsupported.append({"game": game, "title_id": title_id, "resource": resource,
                                            "member": key, "internal_filename": name, "width": width,
                                            "height": height, "bclim_format": fmt,
                                            "source_archive_sha256": archive_hash,
                                            "source_bclim_sha256": hashlib.sha256(bclim).hexdigest(),
                                            "reason": str(error)})
                        continue
                    rel = Path(game) / title_id / resource.replace("/", "_") / f"member-{member.entry_id:04d}-{member.subfile_id:02d}" / f"{name}.png"
                    write_png(output / rel, width, height, rgba)
                    rows.append({"game": game, "title_id": title_id, "resource": resource, "member": key,
                                 "internal_filename": name, "output": rel.as_posix(), "width": width, "height": height,
                                 "bclim_format": fmt, "source_archive_sha256": archive_hash,
                                 "source_bclim_sha256": hashlib.sha256(bclim).hexdigest(),
                                 "png_sha256": hashlib.sha256((output / rel).read_bytes()).hexdigest()})
    return rows, unsupported


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "build/milestone-3h/texture-editing")
    args = parser.parse_args()
    rows, unsupported = extract(ROOT, args.output)
    manifest = {"generator": "scripts/extract_milestone3h_textures.py", "assets": rows,
                "unsupported_assets": unsupported}
    (args.output / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"output": args.output.relative_to(ROOT).as_posix(), "images": len(rows),
                      "unsupported": len(unsupported)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
