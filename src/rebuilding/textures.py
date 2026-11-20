"""Deterministic PNG/BCLIM and embedded-resource helpers for milestone builds."""

from __future__ import annotations

import hashlib
import json
import shutil
import struct
import zlib
from pathlib import Path
from typing import Any

from src.extraction.garc import GARC
from src.extraction.lz11 import decompress as lz11_decompress


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def morton_xy(value: int) -> tuple[int, int]:
    x = y = 0
    for bit in range(3):
        x |= ((value >> (2 * bit)) & 1) << bit
        y |= ((value >> (2 * bit + 1)) & 1) << bit
    return x, y


def _morton_index(x: int, y: int) -> int:
    value = 0
    for bit in range(3):
        value |= ((x >> bit) & 1) << (2 * bit)
        value |= ((y >> bit) & 1) << (2 * bit + 1)
    return value


def _expand5(value: int) -> int:
    return (value << 3) | (value >> 2)


def _decode_pixel(pixel: bytes, fmt: int) -> tuple[int, int, int, int]:
    value = int.from_bytes(pixel, "little")
    if fmt == 9:
        return ((value >> 24) & 255, (value >> 16) & 255, (value >> 8) & 255, value & 255)
    if fmt == 8:
        return tuple(((value >> shift) & 15) * 17 for shift in (12, 8, 4, 0))  # type: ignore[return-value]
    if fmt == 7:
        return (_expand5((value >> 11) & 31), _expand5((value >> 6) & 31),
                _expand5((value >> 1) & 31), 255 if value & 1 else 0)
    raise ValueError(f"Unsupported BCLIM format {fmt}; only RGBA4444/8888 are encoded")


def decode_bclim(raw: bytes) -> tuple[int, int, int, bytes]:
    footer = raw.rfind(b"CLIM")
    if footer < 0 or footer + 40 != len(raw) or raw[footer + 4:footer + 6] != b"\xff\xfe":
        raise ValueError("Invalid or unsupported BCLIM footer")
    width, height, fmt, data_len = struct.unpack_from("<HHII", raw, footer + 28)
    if not width or not height or data_len != footer:
        raise ValueError("Invalid BCLIM dimensions or pixel-data length")
    if fmt not in (8, 9):
        raise ValueError(f"Unsupported BCLIM format {fmt}; only RGBA4444/8888 are supported")
    bpp = 2 if fmt == 8 else 4
    padded_w = 1 << (width - 1).bit_length()
    padded_h = 1 << (height - 1).bit_length()
    if len(raw[:footer]) != padded_w * padded_h * bpp:
        raise ValueError(f"Unexpected padded BCLIM storage for {width}x{height}, format {fmt}")
    tiles_per_row = padded_w // 8
    rgba = bytearray(width * height * 4)
    for index in range(padded_w * padded_h):
        tile = index // 64
        x_local, y_local = morton_xy(index % 64)
        x = (tile % tiles_per_row) * 8 + x_local
        y = (tile // tiles_per_row) * 8 + y_local
        if x >= width or y >= height:
            continue
        start = index * bpp
        rgba_at = (y * width + x) * 4
        rgba[rgba_at:rgba_at + 4] = bytes(_decode_pixel(raw[start:start + bpp], fmt))
    return width, height, fmt, bytes(rgba)


def _encode_pixel(rgba: bytes, fmt: int) -> bytes:
    r, g, b, a = rgba
    if fmt == 9:
        return bytes((a, b, g, r))
    if fmt == 8:
        channels = [round(channel * 15 / 255) for channel in (r, g, b, a)]
        value = (channels[0] << 12) | (channels[1] << 8) | (channels[2] << 4) | channels[3]
        return value.to_bytes(2, "little")
    raise ValueError(f"Unsupported BCLIM format {fmt}")


def encode_bclim(rgba: bytes, width: int, height: int, template: bytes) -> bytes:
    old_width, old_height, fmt, _ = decode_bclim(template)
    if (width, height) != (old_width, old_height) or len(rgba) != width * height * 4:
        raise ValueError("PNG dimensions/RGBA length do not match the source BCLIM")
    footer = template[-40:]
    padded_w = 1 << (width - 1).bit_length()
    padded_h = 1 << (height - 1).bit_length()
    bpp = 2 if fmt == 8 else 4
    pixels = bytearray(template[:-40])  # Retain invisible padded texels exactly.
    tiles_per_row = padded_w // 8
    for y in range(height):
        for x in range(width):
            tile = (y // 8) * tiles_per_row + (x // 8)
            index = tile * 64 + _morton_index(x % 8, y % 8)
            src = (y * width + x) * 4
            encoded = _encode_pixel(rgba[src:src + 4], fmt)
            dst = index * bpp
            pixels[dst:dst + bpp] = encoded
    rebuilt = bytes(pixels) + footer
    if len(rebuilt) != len(template):
        raise ValueError("Encoded BCLIM changed source byte length")
    return rebuilt


def _png_unfilter(data: bytes, width: int, height: int, bpp: int) -> bytes:
    stride = width * bpp
    if len(data) != height * (stride + 1):
        raise ValueError("PNG image data length does not match dimensions")
    result = bytearray(height * stride)
    pos = 0
    for y in range(height):
        filter_type = data[pos]
        pos += 1
        source = data[pos:pos + stride]
        pos += stride
        out = bytearray(stride)
        prior = result[(y - 1) * stride:y * stride] if y else bytes(stride)
        for x, raw_value in enumerate(source):
            left = out[x - bpp] if x >= bpp else 0
            up = prior[x]
            up_left = prior[x - bpp] if x >= bpp else 0
            if filter_type == 0:
                predictor = 0
            elif filter_type == 1:
                predictor = left
            elif filter_type == 2:
                predictor = up
            elif filter_type == 3:
                predictor = (left + up) // 2
            elif filter_type == 4:
                p = left + up - up_left
                pa, pb, pc = abs(p - left), abs(p - up), abs(p - up_left)
                predictor = left if pa <= pb and pa <= pc else (up if pb <= pc else up_left)
            else:
                raise ValueError(f"Unsupported PNG row filter {filter_type}")
            out[x] = (raw_value + predictor) & 255
        result[y * stride:(y + 1) * stride] = out
    return bytes(result)


def read_png_rgba(path: Path) -> tuple[int, int, bytes]:
    raw = path.read_bytes()
    if raw[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"Not a PNG file: {path}")
    pos = 8
    width = height = bit_depth = color_type = interlace = None
    chunks: list[bytes] = []
    saw_iend = False
    first_chunk = True
    while pos < len(raw):
        if pos + 12 > len(raw):
            raise ValueError("Truncated PNG chunk")
        size = struct.unpack_from(">I", raw, pos)[0]
        kind = raw[pos + 4:pos + 8]
        end = pos + 12 + size
        if end > len(raw):
            raise ValueError("PNG chunk exceeds file length")
        payload = raw[pos + 8:pos + 8 + size]
        crc = struct.unpack_from(">I", raw, pos + 8 + size)[0]
        if zlib.crc32(kind + payload) & 0xFFFFFFFF != crc:
            raise ValueError("PNG chunk CRC mismatch")
        if first_chunk and kind != b"IHDR":
            raise ValueError("PNG IHDR must be the first chunk")
        first_chunk = False
        if kind in (b"iCCP", b"sRGB", b"gAMA", b"cHRM"):
            raise ValueError("PNG color-profile metadata is unsupported; export raw RGBA samples")
        if kind == b"IHDR":
            if width is not None or size != 13:
                raise ValueError("Invalid duplicate or malformed PNG IHDR")
            width, height, bit_depth, color_type, comp, filt, interlace = struct.unpack(">IIBBBBB", payload)
            if not width or not height or comp or filt or interlace:
                raise ValueError("PNG must be non-interlaced with standard compression/filter methods")
        elif kind == b"IDAT":
            chunks.append(payload)
        elif kind == b"IEND":
            if size != 0:
                raise ValueError("Malformed PNG IEND")
            saw_iend = True
            if end != len(raw):
                raise ValueError("Unexpected bytes after PNG IEND")
            break
        elif kind[0] & 0x20 == 0:
            raise ValueError(f"Unsupported critical PNG chunk {kind!r}")
        pos = end
    if not saw_iend or width is None or height is None or bit_depth != 8 or color_type != 6:
        raise ValueError("PNG must be complete 8-bit RGBA with IHDR/IDAT/IEND")
    return width, height, _png_unfilter(zlib.decompress(b"".join(chunks)), width, height, 4)


def lz11_literal_compress(raw: bytes) -> bytes:
    size = len(raw)
    if 0 < size <= 0xFFFFFF:
        header = b"\x11" + size.to_bytes(3, "little")
    else:
        header = b"\x11\0\0\0" + size.to_bytes(4, "little")
    output = bytearray(header)
    for start in range(0, size, 8):
        output.append(0)
        output.extend(raw[start:start + 8])
    return bytes(output)


def parse_texture_pack(raw: bytes) -> list[dict[str, Any]]:
    if len(raw) < 4:
        raise ValueError("Texture pack is truncated")
    count = struct.unpack_from("<I", raw)[0]
    if count > 2048 or 4 + count * 128 > len(raw):
        raise ValueError("Unrecognized texture pack index")
    names = [raw[4 + index * 64:4 + (index + 1) * 64].split(b"\0", 1)[0].decode("ascii")
             for index in range(count)]
    image_names = [(index, name) for index, name in enumerate(names) if name.lower().endswith(".bclim")]
    footers = []
    cursor = 0
    while True:
        cursor = raw.find(b"CLIM", cursor)
        if cursor < 0:
            break
        if cursor + 40 <= len(raw):
            try:
                total = struct.unpack_from("<I", raw, cursor + 12)[0]
                width, height, fmt, pixel_len = struct.unpack_from("<HHII", raw, cursor + 28)
                if width and height and total == pixel_len + 40 and cursor >= pixel_len:
                    footers.append((cursor, pixel_len, fmt, width, height))
            except struct.error:
                pass
        cursor += 4
    if len(image_names) != len(footers):
        raise ValueError(f"Texture pack filename/index mismatch: {len(image_names)} names, {len(footers)} BCLIMs")
    result = []
    for (order, name), (footer, pixel_len, fmt, width, height) in zip(image_names, footers):
        start = footer - pixel_len
        end = footer + 40
        result.append({"order": order, "name": name, "start": start, "end": end,
                       "format": fmt, "width": width, "height": height, "data": raw[start:end]})
    return result


def replace_texture_pack(raw: bytes, replacements: dict[str, bytes]) -> bytes:
    if not replacements:
        return raw
    files = parse_texture_pack(raw)
    found = {item["name"] for item in files}
    if replacements.keys() - found:
        raise ValueError(f"Missing texture names: {sorted(replacements.keys() - found)}")
    output = bytearray(raw)
    for item in files:
        replacement = replacements.get(item["name"])
        if replacement is None:
            continue
        if len(replacement) != item["end"] - item["start"]:
            raise ValueError(f"Replacement BCLIM size changed for {item['name']}")
        output[item["start"]:item["end"]] = replacement
    return bytes(output)


def replace_archive_member(archive_bytes: bytes, member_key: tuple[int, int], pack_raw: bytes) -> tuple[bytes, dict[str, Any]]:
    archive = GARC.parse(archive_bytes)
    original_members = {(m.entry_id, m.subfile_id): m for m in archive.members}
    member = original_members.get(member_key)
    if member is None:
        raise ValueError(f"GARC member does not exist: {member_key}")
    compressed = member.data[:1] == b"\x11"
    original_pack = lz11_decompress(member.data) if compressed else member.data
    changed = pack_raw != original_pack
    replacement = member.data if not changed else (lz11_literal_compress(pack_raw) if compressed else pack_raw)
    output = archive.rebuild({member_key: replacement})
    rebuilt = GARC.parse(output)
    rebuilt_members = {(m.entry_id, m.subfile_id): m for m in rebuilt.members}
    if rebuilt.rebuild() != output or set(rebuilt_members) != set(original_members):
        raise ValueError("Rebuilt GARC failed structural round trip")
    for key, old in original_members.items():
        if key != member_key and rebuilt_members[key].data != old.data:
            raise ValueError(f"Unrelated GARC member changed: {key}")
    rebuilt_data = rebuilt_members[member_key].data
    rebuilt_pack = lz11_decompress(rebuilt_data) if compressed else rebuilt_data
    if rebuilt_pack != pack_raw:
        raise ValueError("Rebuilt GARC member does not decompress to requested texture pack")
    return output, {"source_sha256": sha256(archive_bytes), "output_sha256": sha256(output),
                    "source_size": len(archive_bytes), "output_size": len(output),
                    "modified_member": f"{member_key[0]}/{member_key[1]}",
                    "garc_member_count": len(original_members),
                    "unrelated_members_verified_unchanged": len(original_members) - 1,
                    "texture_pack_roundtrip_verified": True, "output_byte_identical_to_source": output == archive_bytes}


def backup_workspace(editing_root: Path, backup_root: Path, expected_names: set[str]) -> Path:
    files = sorted(p for p in editing_root.glob("*.png") if p.is_file())
    if {p.name for p in files} != expected_names:
        raise ValueError("Editing workspace PNG set does not exactly match the 24 canonical images")
    manifest = editing_root / "manifest.json"
    if not manifest.is_file():
        raise ValueError("Editing workspace manifest is missing")
    payloads = {p.name: p.read_bytes() for p in files}
    payloads[manifest.name] = manifest.read_bytes()
    stamp = hashlib.sha256(b"".join(name.encode() + b"\0" + sha256(data).encode() for name, data in sorted(payloads.items()))).hexdigest()[:16]
    backup = backup_root / stamp
    backup.mkdir(parents=True, exist_ok=True)
    for name, data in payloads.items():
        target = backup / name
        if target.exists() and target.read_bytes() != data:
            raise ValueError("Existing backup destination contains unexpected data")
        target.write_bytes(data)
    summary = {"files": {name: sha256(data) for name, data in sorted(payloads.items())}, "backup_id": stamp}
    (backup / "backup-manifest.json").write_text(json.dumps(summary, sort_keys=True, indent=2) + "\n", encoding="utf-8", newline="\n")
    return backup


def restore_workspace(editing_root: Path, backup: Path, expected_names: set[str]) -> None:
    summary = json.loads((backup / "backup-manifest.json").read_text(encoding="utf-8"))
    expected = expected_names | {"manifest.json"}
    if set(summary["files"]) != expected:
        raise ValueError("Backup manifest does not match the canonical editing workspace")
    for name, digest in summary["files"].items():
        data = (backup / name).read_bytes()
        if sha256(data) != digest:
            raise ValueError(f"Backup file hash mismatch: {name}")
    editing_root.mkdir(parents=True, exist_ok=True)
    for name in expected:
        shutil.copyfile(backup / name, editing_root / name)
