import struct
import unittest

from scripts.build_render_validation import GLYPH_SPANS, make_control_preserving_body, split_visible_spans
from src.extraction.fonts import cmap_blocks, font_metrics
from src.extraction.messages import TextFile, _rol16
from src.validation.text_constraints import TextConstraintError, analyze_text, enforce_text_limits


def make_textfile(words):
    key = 0x7C89
    encrypted = []
    for word in words:
        encrypted.append(word ^ key)
        key = _rol16(key)
    payload = struct.pack(f"<{len(encrypted)}H", *encrypted)
    table_end = 0x10 + 4 + 8
    raw = bytearray(table_end + len(payload))
    struct.pack_into("<HHIII", raw, 0, 1, 1, len(raw) - 0x10, 0, 0x10)
    struct.pack_into("<I", raw, 0x10, len(raw) - 0x10)
    struct.pack_into("<IHH", raw, 0x14, table_end - 0x10, len(words), 0)
    raw[table_end:] = payload
    return bytes(raw)


def make_metric_font():
    cmap_offset = 0x40
    cwdh_offset = 0x60
    raw = bytearray(cwdh_offset + 22)
    raw[:4] = b"CFNT"
    raw[4:6] = b"\xff\xfe"
    struct.pack_into("<I", raw, 0x0C, len(raw))
    raw[0x14:0x18] = b"FINF"
    struct.pack_into("<I", raw, 0x18, 0x20)
    struct.pack_into("<BBH", raw, 0x1C, 1, 20, 7)
    struct.pack_into("<bbb", raw, 0x20, 0, 10, 10)
    raw[cmap_offset:cmap_offset + 4] = b"CMAP"
    struct.pack_into("<IHHHHI", raw, cmap_offset + 4, 0x18, 0x41, 0x42, 0, 0, 0)
    struct.pack_into("<H", raw, cmap_offset + 20, 7)
    raw[cwdh_offset:cwdh_offset + 4] = b"CWDH"
    struct.pack_into("<IHHI", raw, cwdh_offset + 4, 22, 7, 8, 0)
    struct.pack_into("<bbb", raw, cwdh_offset + 16, 0, 6, 7)
    struct.pack_into("<bbb", raw, cwdh_offset + 19, 0, 8, 9)
    return bytes(raw)


class ValidationTests(unittest.TestCase):
    def test_cmap_end_is_inclusive_and_cwdh_advance_is_parsed(self):
        metrics = font_metrics(make_metric_font())
        self.assertEqual(metrics.glyph_by_codepoint, {0x41: 7, 0x42: 8})
        self.assertEqual(metrics.advance(0x41), 7)
        self.assertEqual(metrics.advance(0x42), 9)
        self.assertIsNone(metrics.advance(0x43))
        self.assertEqual(metrics.alternate_glyph_index, 7)
        self.assertEqual(metrics.alternate_advance, 7)
        self.assertEqual(metrics.default_width, (0, 10, 10))

    def test_cmap_table_includes_end_index(self):
        raw = bytearray(0x38)
        raw[:4] = b"CFNT"
        raw[4:6] = b"\xff\xfe"
        struct.pack_into("<I", raw, 0x0C, len(raw))
        raw[0x20:0x24] = b"CMAP"
        struct.pack_into("<IHHHHI", raw, 0x24, 0x18, 0x41, 0x42, 1, 0, 0)
        struct.pack_into("<2H", raw, 0x34, 3, 9)
        self.assertEqual(dict(cmap_blocks(bytes(raw))[0].glyph_mappings), {0x41: 3, 0x42: 9})

    def test_unsupported_glyph_report_includes_yo(self):
        layout = analyze_text("AЯё", {ord("A")})
        self.assertEqual(layout.unsupported_codepoints, (0x042F, 0x0451))
        self.assertEqual(layout.utf16_units, 3)

    def test_glyph_patch_covers_full_russian_alphabet_and_specials(self):
        upper = "АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ"
        lower = "абвгдеёжзийклмнопрстуфхцчшщъыьэюя"
        self.assertTrue(any(upper in span for span in GLYPH_SPANS))
        self.assertTrue(any(lower in span for span in GLYPH_SPANS))
        for character in "Ёё0123456789.,!?—«»№₽−©®™":
            self.assertTrue(any(character in span for span in GLYPH_SPANS), f"missing test character {character!r}")
        self.assertEqual(max(map(len, GLYPH_SPANS)), 39)

    def test_text_unit_and_explicit_line_limits(self):
        layout = enforce_text_limits("абв\nгд", max_utf16_units=6, max_explicit_line_codepoints=3)
        self.assertEqual(layout.explicit_line_lengths, (3, 2))
        self.assertEqual(layout.utf16_units, 6)
        with self.assertRaises(TextConstraintError):
            enforce_text_limits("абвг", max_utf16_units=3)
        with self.assertRaises(TextConstraintError):
            enforce_text_limits("абвг", max_utf16_units=8, max_explicit_line_codepoints=3)
        with self.assertRaises(TextConstraintError):
            analyze_text("\U0001F600", set())

    def test_test_message_builder_preserves_all_control_tokens(self):
        words = (10, ord("A"), 10, 10, ord("B"), 0x0010, 2, 0xFF00, 0, ord("C"), 10, ord("D"), 0)
        text = TextFile.parse(make_textfile(words))
        line = text.lines[0]
        spans, controls = split_visible_spans(line)
        self.assertEqual(spans, ["", "A", "", "B", "C", "D"])
        self.assertEqual(len(controls), 5)
        replacement_spans = ("1", "2", "", "3", "4", "5")
        body = make_control_preserving_body(line, replacement_spans)
        rebuilt = TextFile.parse(text.rebuild({0: body}))
        self.assertEqual(rebuilt.lines[0].tokens, line.tokens)
        for character in "12345":
            self.assertIn(character, rebuilt.lines[0].display_text)


if __name__ == "__main__":
    unittest.main()
