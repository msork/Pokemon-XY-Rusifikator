"""Validation helpers for encoded text coverage and measurable layout limits."""

from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Collection


class TextConstraintError(ValueError):
    """Raised when a message exceeds an explicitly configured text constraint."""


@dataclass(frozen=True)
class TextLayout:
    utf16_units: int
    explicit_line_lengths: tuple[int, ...]
    max_explicit_line_length: int
    unsupported_codepoints: tuple[int, ...]


def analyze_text(text: str, supported_codepoints: Collection[int]) -> TextLayout:
    """Count BMP UTF-16 units and explicit line lengths, and report unmapped glyphs.

    Width is measured in codepoints here, not pixels. When font advances are known,
    callers should use CFNT CWDH metrics as an additional estimate.
    """
    units = 0
    for character in text:
        codepoint = ord(character)
        if codepoint > 0xFFFF or 0xD800 <= codepoint <= 0xDFFF:
            raise TextConstraintError(f"Unsupported non-BMP/surrogate character U+{codepoint:04X}")
        units += 1
    lengths = tuple(len(line) for line in text.split("\n"))
    unsupported = tuple(sorted({ord(char) for char in text if char != "\n" and ord(char) not in supported_codepoints}))
    return TextLayout(units, lengths, max(lengths, default=0), unsupported)


def enforce_text_limits(
    text: str,
    *,
    max_utf16_units: int,
    max_explicit_line_codepoints: int | None = None,
) -> TextLayout:
    """Enforce storage/line limits without claiming a pixel-width guarantee."""
    layout = analyze_text(text, range(0x10000))
    if layout.utf16_units > max_utf16_units:
        raise TextConstraintError(f"Text uses {layout.utf16_units} UTF-16 units; limit is {max_utf16_units}")
    if max_explicit_line_codepoints is not None and layout.max_explicit_line_length > max_explicit_line_codepoints:
        raise TextConstraintError(
            f"Explicit line has {layout.max_explicit_line_length} codepoints; limit is {max_explicit_line_codepoints}"
        )
    return layout
