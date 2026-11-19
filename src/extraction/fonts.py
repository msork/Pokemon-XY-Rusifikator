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
    glyph_mappings: tuple[tuple[int, int], ...]


@dataclass(frozen=True)
class CwdhBlock:
    offset: int
    size: int
    start_glyph: int
    end_glyph: int
    widths: tuple[tuple[int, int, int], ...]


@dataclass(frozen=True)
class FontMetrics:
    glyph_by_codepoint: dict[int, int]
    widths_by_glyph: dict[int, tuple[int, int, int]]
    alternate_glyph_index: int | None = None
    default_width: tuple[int, int, int] | None = None

    @property
    def mapped_codepoints(self) -> frozenset[int]:
        return frozenset(self.glyph_by_codepoint)

    def advance(self, codepoint: int) -> int | None:
        """Return CWDH character advance; None means the font has no map/width."""
        glyph = self.glyph_by_codepoint.get(codepoint)
        if glyph is None:
            return None
        width = self.widths_by_glyph.get(glyph)
        return width[2] if width is not None else None

    @property
    def alternate_advance(self) -> int | None:
        """Return the CFNT alternate-character advance, if its width is known."""
        if self.alternate_glyph_index is None:
            return None
        width = self.widths_by_glyph.get(self.alternate_glyph_index)
        return width[2] if width is not None else None


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
            mappings: dict[int, int] = {}
            if method == 0:
                if pos + 22 > limit:
                    raise ValueError
                glyph_base = struct.unpack_from("<H", raw, pos + 20)[0]
                if glyph_base != 0xFFFF:
                    mappings.update((code, glyph_base + code - start) for code in range(start, end + 1))
            elif method == 1:
                count = end - start + 1
                if pos + 20 + count * 2 > limit:
                    raise ValueError
                values = struct.unpack_from(f"<{count}H", raw, pos + 20) if count else ()
                mappings.update((start + i, glyph) for i, glyph in enumerate(values) if glyph != 0xFFFF)
            else:
                if pos + 22 > limit:
                    raise ValueError
                count = struct.unpack_from("<H", raw, pos + 20)[0]
                if pos + 22 + count * 4 > limit:
                    raise ValueError
                for i in range(count):
                    code, glyph = struct.unpack_from("<HH", raw, pos + 22 + i * 4)
                    if glyph != 0xFFFF and start <= code <= end:
                        mappings[code] = glyph
            blocks.append(CmapBlock(pos, block_size, start, end, method, frozenset(mappings), tuple(sorted(mappings.items()))))
        except (struct.error, ValueError):
            pass
        pos += 4
    if not blocks:
        raise FontError("No valid CMAP blocks found")
    return tuple(blocks)


def cwdh_blocks(raw: bytes) -> tuple[CwdhBlock, ...]:
    """Read structurally valid CWDH glyph-width blocks from a CFNT."""
    if len(raw) < 0x14 or raw[:4] != b"CFNT" or raw[4:6] != b"\xff\xfe":
        raise FontError("Expected little-endian CFNT font")
    blocks: list[CwdhBlock] = []
    pos = 0
    while True:
        pos = raw.find(b"CWDH", pos)
        if pos < 0:
            break
        try:
            size, start, end, _next = struct.unpack_from("<IHHI", raw, pos + 4)
            count = end - start + 1
            limit = pos + size
            if size < 16 or start > end or limit > len(raw) or 16 + count * 3 > size:
                raise ValueError
            widths = tuple(struct.unpack_from("<bbb", raw, pos + 16 + i * 3) for i in range(count))
            blocks.append(CwdhBlock(pos, size, start, end, widths))
        except (struct.error, ValueError):
            pass
        pos += 4
    if not blocks:
        raise FontError("No valid CWDH blocks found")
    return tuple(blocks)


def font_metrics(raw: bytes) -> FontMetrics:
    """Combine CMAP glyph mappings and CWDH advances, honoring first-match order."""
    glyph_by_codepoint: dict[int, int] = {}
    for block in cmap_blocks(raw):
        for codepoint, glyph in block.glyph_mappings:
            glyph_by_codepoint.setdefault(codepoint, glyph)
    widths_by_glyph: dict[int, tuple[int, int, int]] = {}
    for block in cwdh_blocks(raw):
        for index, widths in enumerate(block.widths, block.start_glyph):
            widths_by_glyph.setdefault(index, widths)
    finf = raw.find(b"FINF")
    if finf >= 0 and finf + 16 <= len(raw):
        alternate_glyph_index = struct.unpack_from("<H", raw, finf + 10)[0]
        default_width = struct.unpack_from("<bbb", raw, finf + 12)
    else:
        alternate_glyph_index = None
        default_width = None
    return FontMetrics(glyph_by_codepoint, widths_by_glyph, alternate_glyph_index, default_width)
