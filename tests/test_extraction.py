import struct
import unittest

from src.extraction.fonts import cmap_blocks
from src.extraction.garc import GARC
from src.extraction.lz11 import decompress
from src.extraction.messages import TextFile


class ExtractionTests(unittest.TestCase):
    def test_lz11_literal_stream(self):
        self.assertEqual(decompress(b"\x11\x03\x00\x00\x00ABC"), b"ABC")

    def test_garc_identity_round_trip(self):
        header = bytearray(0x1C)
        header[:4] = b"CRAG"
        struct.pack_into("<IHHIIII", header, 4, 0x1C, 0xFEFF, 0x0400, 4, 0, 0, 0)
        fato = b"OTAF" + struct.pack("<IHHI", 16, 1, 0, 0)
        fatb = b"BTAF" + struct.pack("<II", 28, 1) + struct.pack("<I", 1) + struct.pack("<III", 0, 4, 3)
        data_offset = len(header) + len(fato) + len(fatb) + 12
        fimg = b"BMIF" + struct.pack("<II", 12, 4)
        raw = header + fato + fatb + fimg + b"abc\xff"
        struct.pack_into("<I", raw, 0x10, data_offset)
        struct.pack_into("<I", raw, 0x14, len(raw))
        struct.pack_into("<I", raw, 0x18, 3)
        self.assertEqual(GARC.parse(bytes(raw)).rebuild(), bytes(raw))

    def test_textfile_identity_with_encrypted_line(self):
        # One two-word message encrypted with the Generation VI initial key.
        key = 0x7C89
        encrypted = struct.pack("<2H", ord("A") ^ key, 0 ^ (((key << 3) | (key >> 13)) & 0xFFFF))
        raw = bytearray(0x10 + 4 + 8 + len(encrypted))
        struct.pack_into("<HHIII", raw, 0, 1, 1, len(raw) - 0x10, 0, 0x10)
        struct.pack_into("<I", raw, 0x10, len(raw) - 0x10)
        struct.pack_into("<IHH", raw, 0x14, 12, 2, 0)
        raw[0x1C:] = encrypted
        text = TextFile.parse(bytes(raw))
        self.assertEqual(text.lines[0].display_text, "A")
        self.assertEqual(text.raw, bytes(raw))

    def test_cmap_scan_has_codepoints_and_no_russian_default(self):
        raw = bytearray(0x40)
        raw[:4] = b"CFNT"
        raw[4:6] = b"\xff\xfe"
        struct.pack_into("<I", raw, 0x0C, len(raw))
        raw[0x20:0x24] = b"CMAP"
        struct.pack_into("<IHHHHI", raw, 0x24, 0x20, 0x0400, 0x0451, 2, 0, 0)
        struct.pack_into("<H", raw, 0x34, 2)
        struct.pack_into("<4H", raw, 0x36, 0x0401, 1, 0x0451, 2)
        block = cmap_blocks(bytes(raw))[0]
        self.assertEqual(block.mapped_codepoints, frozenset({0x0401, 0x0451}))


if __name__ == "__main__":
    unittest.main()
