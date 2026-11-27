from __future__ import annotations

import struct
import unittest

from src.rebuilding.bclim import UnsupportedBclim, decode_bclim, encode_bclim


def fixture(width: int, height: int, fmt: int, payload: bytes) -> bytes:
    return payload + struct.pack("<4sHHIII4sIHHII", b"CLIM", 0xFEFF, 20, 0x02020000,
                                 len(payload) + 40, 1, b"imag", 16, width, height, fmt, len(payload))


def pixel(image: bytes, width: int, x: int, y: int) -> tuple[int, ...]:
    pos = (y * width + x) * 4
    return tuple(image[pos:pos + 4])


class BclimTests(unittest.TestCase):
    def test_direct_and_four_bit_formats_preserve_padding_and_require_exact_edits(self):
        # Encoded samples are listed in file order, including implicit output channels.
        cases = (
            (0, b"\x42", (66, 66, 66, 255), (17, 17, 17, 255)),
            (1, b"\x42", (0, 0, 0, 66), (0, 0, 0, 17)),
            (2, b"\xa3", (170, 170, 170, 51), (34, 34, 34, 255)),
            (3, b"\xa3\x72", (114, 114, 114, 163), (34, 34, 34, 1)),
            (4, b"\x33\xaa", (170, 51, 0, 255), (41, 82, 0, 255)),
            (5, b"\x1f\xfc", (255, 130, 255, 255), (0, 255, 0, 255)),
            (6, b"\x44\x66\x99", (153, 102, 68, 255), (8, 9, 10, 255)),
            (7, b"\x41\xf8", (255, 8, 0, 255), (0, 0, 255, 0)),
            (8, b"\x2f\x9a", (153, 170, 34, 255), (0, 17, 34, 51)),
            (9, b"\x33\x22\x11\x00", (0, 17, 34, 51), (1, 2, 3, 4)),
            (12, b"\xba", (170, 170, 170, 255), (102, 102, 102, 255)),
            (13, b"\xba", (0, 0, 0, 170), (0, 0, 0, 102)),
        )
        for fmt, prefix, old, new in cases:
            with self.subTest(fmt=fmt):
                size = 32 if fmt >= 12 else 64 * len(prefix)
                raw = fixture(1, 1, fmt, prefix + bytes([0xA5]) * (size - len(prefix)))
                self.assertEqual(decode_bclim(raw), (1, 1, fmt, bytes(old)))
                self.assertEqual(encode_bclim(bytes(old), 1, 1, raw), raw)
                result = encode_bclim(bytes(new), 1, 1, raw)
                self.assertEqual(decode_bclim(result), (1, 1, fmt, bytes(new)))
                self.assertEqual(result[len(prefix):], raw[len(prefix):])
                if fmt >= 12:
                    self.assertEqual(result[0] & 0xF0, 0xB0)
        with self.assertRaisesRegex(ValueError, "exactly"):
            encode_bclim(bytes((1, 2, 3, 255)), 1, 1, fixture(1, 1, 0, bytes(64)))

    def test_rgba8_tile_stride_and_clipped_texels(self):
        # A 17×9 visible crop uses three 8×8 tiles across and two down.
        raw = fixture(17, 9, 9, b"".join(bytes((255, 0, 0, red)) * 64 for red in range(6)))
        width, height, fmt, rgba = decode_bclim(raw)
        self.assertEqual((width, height, fmt), (17, 9, 9))
        self.assertEqual(pixel(rgba, width, 16, 0), (2, 0, 0, 255))
        self.assertEqual(pixel(rgba, width, 8, 8), (4, 0, 0, 255))
        self.assertEqual(pixel(rgba, width, 16, 8), (5, 0, 0, 255))

    def test_etc_individual_selectors_and_block_order(self):
        # R1=1, R2=2, G1=3, G2=4, B1=5, B2=6. Set selectors
        # 3 at (0,1) and 1 at (1,0) to check the column-major bitplanes.
        block = bytes.fromhex("1200020000563412")
        blocks = [block, bytes.fromhex("0000000000000044"),
                  bytes.fromhex("0000000000005500"), bytes.fromhex("0000000000660000")]
        raw = fixture(8, 8, 10, b"".join(blocks))
        rgba = decode_bclim(raw)[3]
        self.assertEqual(pixel(rgba, 8, 0, 0), (19, 53, 87, 255))
        self.assertEqual(pixel(rgba, 8, 0, 1), (9, 43, 77, 255))
        self.assertEqual(pixel(rgba, 8, 1, 0), (25, 59, 93, 255))
        self.assertEqual(pixel(rgba, 8, 2, 0), (36, 70, 104, 255))
        self.assertEqual(pixel(rgba, 8, 4, 0), (70, 2, 2, 255))
        self.assertEqual(pixel(rgba, 8, 0, 4), (2, 87, 2, 255))
        self.assertEqual(pixel(rgba, 8, 4, 4), (2, 2, 104, 255))
        self.assertEqual(encode_bclim(rgba, 8, 8, raw), raw)
        changed = bytes((9, 43, 77, 255)) + rgba[4:]
        edited = encode_bclim(changed, 8, 8, raw)
        self.assertEqual(edited[:4], bytes.fromhex("13000300"))
        self.assertEqual(edited[4:], raw[4:])
        self.assertEqual(decode_bclim(edited)[3], changed)
        with self.assertRaisesRegex(UnsupportedBclim, "original block codebook"):
            encode_bclim(b"\0" + rgba[1:], 8, 8, raw)

    def test_etc_differential_flipped_split_and_alpha_only_round_trip(self):
        # Khronos differential example uses bases (28,4,3), deltas (-4,2,0).
        rgb_block = bytes.fromhex("00000000031822e4")
        alpha_block = bytes.fromhex("1032547698badcfe")
        raw = fixture(3, 3, 11, (alpha_block + rgb_block) * 4)
        rgba = decode_bclim(raw)[3]
        self.assertEqual(pixel(rgba, 3, 0, 0), (233, 35, 26, 0))
        self.assertEqual(pixel(rgba, 3, 1, 0), (233, 35, 26, 68))
        self.assertEqual(pixel(rgba, 3, 0, 2), (200, 51, 26, 34))
        self.assertEqual(encode_bclim(rgba, 3, 3, raw), raw)
        changed = rgba[:3] + b"\xff" + rgba[4:]
        edited = encode_bclim(changed, 3, 3, raw)
        self.assertEqual(edited[0], 0x1F)
        self.assertEqual(edited[1:], raw[1:])
        self.assertEqual(decode_bclim(edited)[3], changed)
        for invalid in (b"\0" + rgba[1:], rgba[:3] + b"\x01" + rgba[4:]):
            with self.assertRaises(UnsupportedBclim):
                encode_bclim(invalid, 3, 3, raw)

    def test_palette_high_nibble_first_and_palette_indices_are_preserved(self):
        # Index 2 duplicates index 1. No-op and unrelated edits retain the
        # original index even when the decoded color has another encoding.
        data = bytes.fromhex("02000300000001f801f820") + bytes(118 - 1)
        raw = fixture(2, 1, 7, data)
        red, clear = bytes((255, 0, 0, 255)), bytes(4)
        self.assertEqual(decode_bclim(raw)[3], red + clear)
        self.assertEqual(encode_bclim(red + clear, 2, 1, raw), raw)
        edited = encode_bclim(red + red, 2, 1, raw)
        self.assertEqual(edited[10], 0x21)
        self.assertEqual(decode_bclim(edited)[3], red + red)
        with self.assertRaisesRegex(ValueError, "existing palette color"):
            encode_bclim(red + b"\xff" * 4, 2, 1, raw)

    def test_palette_uses_byte_indices_above_sixteen_colors(self):
        palette = bytes(32) + b"\x3f\x00"
        raw = fixture(1, 1, 7, b"\x02\0\x11\0" + palette + bytes((16,)) + bytes(89))
        self.assertEqual(decode_bclim(raw)[3], bytes((0, 0, 255, 255)))

    def test_rejects_bad_headers_unknown_layouts_and_differential_overflow(self):
        with self.assertRaises(UnsupportedBclim):
            decode_bclim(fixture(1, 1, 22, bytes(64)))
        with self.assertRaisesRegex(ValueError, "imag"):
            decode_bclim(fixture(1, 1, 0, bytes(64)).replace(b"imag", b"abcd"))
        with self.assertRaisesRegex(UnsupportedBclim, "storage"):
            decode_bclim(fixture(1, 1, 0, bytes(63)))
        with self.assertRaisesRegex(ValueError, "five-bit range"):
            decode_bclim(fixture(1, 1, 10, bytes.fromhex("0000000002000007") + bytes(24)))


if __name__ == "__main__":
    unittest.main()
