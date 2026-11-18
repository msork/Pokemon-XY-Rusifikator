"""Read-only inspection of Nintendo 3DS CFNT/BCFNT character map blocks."""

from __future__ import annotations

from dataclasses import dataclass
import struct


class FontError(ValueError):
    """Raised when a font container or CMAP block is malformed."""


@dataclass(frozen=True)
class CmapBlock:
    offset: int
    size: int
    start: int
    end: int
    method: int
    mapped_codepoints: frozenset[int]


def cmap_blocks(raw: bytes) -> tuple[CmapBlock, ...]:
    """Scan a CFNT for structurally valid CMAP blocks and return mapped codepoints."""
    if len(raw) < 0x14 or raw[:4] != b"CFNT" or raw[4:6] != b"\xff\xfe":
        raise FontError("Expected little-endian CFNT font")
    declared_size = struct.unpack_from("<I", raw, 0x0C)[0]
    if declared_size != len(raw):
        raise FontError("CFNT declared size differs from input size")
    blocks: list[CmapBlock] = []
    pos = 0
    while True:
        pos = raw.find(b"CMAP", pos)
        if pos < 0:
            break
        try:
            block_size, start, end, method, _reserved, _next = struct.unpack_from("<IHHHHI", raw, pos + 4)
            limit = pos + block_size
            if block_size < 0x18 or limit > len(raw) or start > end or method not in (0, 1, 2):
                raise ValueError
            codes: set[int] = set()
            if method == 0:
                if pos + 22 > limit:
                    raise ValueError
                glyph_base = struct.unpack_from("<H", raw, pos + 20)[0]
                codes.update(range(start, end))
                if glyph_base == 0xFFFF:
                    codes.clear()
            elif method == 1:
                count = end - start
                if pos + 20 + count * 2 > limit:
                    raise ValueError
                values = struct.unpack_from(f"<{count}H", raw, pos + 20) if count else ()
                codes.update(start + i for i, glyph in enumerate(values) if glyph != 0xFFFF)
            else:
                if pos + 22 > limit:
                    raise ValueError
                count = struct.unpack_from("<H", raw, pos + 20)[0]
                if pos + 22 + count * 4 > limit:
                    raise ValueError
                for i in range(count):
                    code, glyph = struct.unpack_from("<HH", raw, pos + 22 + i * 4)
                    if glyph != 0xFFFF:
                        codes.add(code)
            blocks.append(CmapBlock(pos, block_size, start, end, method, frozenset(codes)))
        except (struct.error, ValueError):
            pass
        pos += 4
    if not blocks:
        raise FontError("No valid CMAP blocks found")
    return tuple(blocks)
