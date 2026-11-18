import struct
import unittest
import hashlib

from src.extraction.fonts import cmap_blocks
from src.extraction.garc import GARC
from src.extraction.lz11 import decompress
from src.extraction.messages import MessageError, TextFile, _rol16, rebuild_identity
from scripts.build_language_screen_poc import replace_message_archive


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


def make_garc(member_data):
    padded = member_data + b"\xff" * ((-len(member_data)) % 4)
    header = bytearray(0x1C)
    header[:4] = b"CRAG"
    fato = b"OTAF" + struct.pack("<IHHI", 16, 1, 0, 0)
    fatb = b"BTAF" + struct.pack("<II", 28, 1) + struct.pack("<I", 1) + struct.pack("<III", 0, len(padded), len(member_data))
    fimg = b"BMIF" + struct.pack("<II", 12, len(padded))
    data_offset = len(header) + len(fato) + len(fatb) + len(fimg)
    raw = header + fato + fatb + fimg + padded
    struct.pack_into("<IHHIIII", raw, 4, 0x1C, 0xFEFF, 0x0400, 4, data_offset, len(raw), len(member_data))
    return bytes(raw)


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

    def test_edited_textfile_repackages_in_garc_copy(self):
        source_text = make_textfile(tuple(map(ord, "CONTINUE")) + (0,))
        source_garc = make_garc(source_text)
        parsed = GARC.parse(source_garc)
        edited_text = TextFile.parse(source_text).rebuild({0: "\u041f\u0440\u0438\u0432\u0435\u0442!"})
        edited_garc = parsed.rebuild({(0, 0): edited_text})
        rebuilt = GARC.parse(edited_garc)
        self.assertEqual(len(rebuilt.members), 1)
        self.assertEqual(TextFile.parse(rebuilt.members[0].data).lines[0].display_text, "\u041f\u0440\u0438\u0432\u0435\u0442!")
        self.assertNotEqual(hashlib.sha256(source_garc).digest(), hashlib.sha256(edited_garc).digest())

    def test_language_screen_probe_rebuilds_exact_target_and_keeps_other_members(self):
        source_text = make_textfile(tuple(map(ord, "Ver. 1.5")) + (0,))
        source_garc = make_garc(source_text)
        edited_garc = replace_message_archive(source_garc, (0, 0), 0, "Ver. 1.5", "ASCII 2C")
        rebuilt = GARC.parse(edited_garc)
        self.assertEqual(len(rebuilt.members), 1)
        self.assertEqual(TextFile.parse(rebuilt.members[0].data).lines[0].display_text, "ASCII 2C")
        self.assertEqual(len(edited_garc), len(source_garc))

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
        self.assertEqual(rebuild_identity(text), bytes(raw))

    def test_textfile_replacement_reencrypts_and_keeps_message_id(self):
        source = TextFile.parse(make_textfile(tuple(map(ord, "CONTINUE")) + (0,)))
        rebuilt = source.rebuild({0: "\u041f\u0440\u0438\u0432\u0435\u0442!"})
        edited = TextFile.parse(rebuilt)
        self.assertEqual(edited.lines[0].message_id, 0)
        self.assertEqual(edited.lines[0].display_text, "\u041f\u0440\u0438\u0432\u0435\u0442!")
        self.assertEqual(edited.rebuild(), rebuilt)

    def test_replacement_rejects_control_and_placeholder_changes(self):
        source = TextFile.parse(make_textfile((0x0010, 1, 0xBE01, 0)))
        with self.assertRaises(MessageError):
            source.rebuild({0: "replacement"})
        self.assertEqual(TextFile.parse(source.rebuild({0: (0x0010, 1, 0xBE01)})).lines[0].tokens, source.lines[0].tokens)

    def test_replacement_rejects_empty_non_bmp_and_bad_message_id(self):
        source = TextFile.parse(make_textfile((ord("A"), 0)))
        for replacement in ("", "\U0001F600"):
            with self.assertRaises(MessageError):
                source.rebuild({0: replacement})
        with self.assertRaises(MessageError):
            source.rebuild({1: "B"})

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
