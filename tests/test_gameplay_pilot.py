import hashlib
import json
import struct
import tempfile
import unittest
from pathlib import Path

from src.extraction.garc import GARC
from src.extraction.messages import TextFile, _rol16
from src.rebuilding.installation import backup_targets, rollback_targets
from src.rebuilding.pilot import build_archive, effective_resource, source_variant_hash


def make_textfile(messages):
    rows = []
    key = 0x7C89
    for words in messages:
        encoded = []
        line_key = key
        for word in words:
            encoded.append(word ^ line_key)
            line_key = _rol16(line_key)
        rows.append(struct.pack(f"<{len(encoded)}H", *encoded))
        key = (key + 0x2983) & 0xFFFF
    table_end = 0x10 + 4 + 8 * len(rows)
    output = bytearray(table_end)
    struct.pack_into("<HHIII", output, 0, 1, len(rows), 0, 0, 0x10)
    for index, (words, encoded) in enumerate(zip(messages, rows)):
        relative = len(output) - 0x10
        struct.pack_into("<IHH", output, 0x14 + 8 * index, relative, len(words), 0)
        output.extend(encoded)
    total = len(output) - 0x10
    struct.pack_into("<I", output, 4, total)
    struct.pack_into("<I", output, 0x10, total)
    return bytes(output)


def make_garc(member):
    members = member if isinstance(member, list) else [member]
    padded_members = [value + b"\xff" * ((-len(value)) % 4) for value in members]
    header = bytearray(0x1C)
    header[:4] = b"CRAG"
    offsets = []
    fatb_entries = bytearray()
    data = bytearray()
    for index, (value, padded) in enumerate(zip(members, padded_members)):
        offsets.append(len(fatb_entries))
        fatb_entries.extend(struct.pack("<I", 1))
        start = len(data)
        data.extend(padded)
        fatb_entries.extend(struct.pack("<III", start, len(data), len(value)))
    fato = b"OTAF" + struct.pack("<IHH", 12 + 4 * len(members), len(members), 0) + struct.pack(f"<{len(offsets)}I", *offsets)
    fatb_size = 12 + len(fatb_entries)
    fatb = b"BTAF" + struct.pack("<II", fatb_size, len(members)) + fatb_entries
    fimg = b"BMIF" + struct.pack("<II", 12, len(data))
    data_offset = len(header) + len(fato) + len(fatb) + len(fimg)
    output = header + fato + fatb + fimg + data
    struct.pack_into("<IHHIIII", output, 4, 0x1C, 0xFEFF, 0x0400, 4, data_offset, len(output), max(map(len, members)))
    return bytes(output)


class GameplayPilotTests(unittest.TestCase):
    def test_update_resource_wins_and_missing_update_falls_back_to_base(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            base = root / "base/a/0/7/4"
            update = root / "update-1.5/a/0/7/4"
            base.parent.mkdir(parents=True)
            update.parent.mkdir(parents=True)
            base.write_bytes(b"base")
            update.write_bytes(b"update")
            self.assertEqual(effective_resource(base, update), (update, "update-1.5"))
            update.unlink()
            self.assertEqual(effective_resource(base, update), (base, "base"))

    def test_translation_application_preserves_controls_and_every_unrelated_record(self):
        variable = (0x0010, 2, 0x0100, 0)
        text = make_textfile([
            tuple(map(ord, "Hello, ")) + variable + tuple(map(ord, "!")) + (0,),
            tuple(map(ord, "UNCHANGED")) + (0,),
        ])
        unrelated_text = make_textfile([tuple(map(ord, "OTHER MEMBER")) + (0,)])
        source = make_garc([text, unrelated_text])
        original_archive = GARC.parse(source)
        source_line = TextFile.parse(original_archive.members[0].data).lines[0]
        translation = {
            "record_id": "gen6:a/0/8/2:0000/00:00000",
            "source_variant_sha256": source_variant_hash(source_line.decoded_words),
            "scope": "shared", "version_scope": ["base"], "status": "validated",
            "translation_segments": [
                {"text": "Привет, "}, {"control_words": ["0010", "0002", "0100", "0000"]},
                {"text": "!"},
            ],
        }
        output, proof = build_archive(source, "a/0/8/2", "pokemon-x", "base", [translation])
        rebuilt = GARC.parse(output)
        target = TextFile.parse(rebuilt.members[0].data)
        self.assertEqual(target.lines[0].display_text, "Привет, [VAR 0100(0000)]!")
        self.assertEqual(target.lines[0].tokens, source_line.tokens)
        self.assertEqual(target.lines[1].decoded_words, TextFile.parse(text).lines[1].decoded_words)
        self.assertEqual(proof["unrelated_members_verified_unchanged"], 1)
        self.assertEqual(proof["untranslated_messages_verified_unchanged"], 1)
        self.assertEqual(rebuilt.members[1].data, unrelated_text)
        self.assertEqual(GARC.parse(output).rebuild(), output)
        self.assertEqual(build_archive(source, "a/0/8/2", "pokemon-x", "base", [translation])[0], output)
        self.assertEqual(hashlib.sha256(source).hexdigest(), proof["source_sha256"])

    def test_game_specific_hashes_select_x_and_y_records_independently(self):
        x_source = make_garc(make_textfile([tuple(map(ord, "X-only")) + (0,)]))
        y_source = make_garc(make_textfile([tuple(map(ord, "Y-only")) + (0,)]))
        x_line = TextFile.parse(GARC.parse(x_source).members[0].data).lines[0]
        y_line = TextFile.parse(GARC.parse(y_source).members[0].data).lines[0]
        self.assertNotEqual(source_variant_hash(x_line.decoded_words), source_variant_hash(y_line.decoded_words))
        common = {"record_id": "gen6:a/0/8/2:0000/00:00000", "scope": "x", "version_scope": ["base"],
                  "status": "validated", "translation_segments": [{"text": "Текст X"}]}
        x_row = dict(common, source_variant_sha256=source_variant_hash(x_line.decoded_words))
        y_row = dict(common, scope="y", source_variant_sha256=source_variant_hash(y_line.decoded_words),
                     translation_segments=[{"text": "Текст Y"}])
        x_output, _ = build_archive(x_source, "a/0/8/2", "pokemon-x", "base", [x_row, y_row])
        y_output, _ = build_archive(y_source, "a/0/8/2", "pokemon-y", "base", [x_row, y_row])
        self.assertEqual(TextFile.parse(GARC.parse(x_output).members[0].data).lines[0].display_text, "Текст X")
        self.assertEqual(TextFile.parse(GARC.parse(y_output).members[0].data).lines[0].display_text, "Текст Y")

    def test_machine_drafts_require_explicit_build_opt_in(self):
        source = make_garc(make_textfile([tuple(map(ord, "Source")) + (0,)]))
        line = TextFile.parse(GARC.parse(source).members[0].data).lines[0]
        row = {"record_id": "gen6:a/0/8/2:0000/00:00000",
               "source_variant_sha256": source_variant_hash(line.decoded_words),
               "scope": "shared", "version_scope": ["base"], "status": "machine_draft",
               "translation_segments": [{"text": "Перевод"}]}
        with self.assertRaisesRegex(ValueError, "explicit inclusion"):
            build_archive(source, "a/0/8/2", "pokemon-x", "base", [row])

    def test_non_nfc_translation_is_rejected(self):
        source = make_garc(make_textfile([tuple(map(ord, "Source")) + (0,)]))
        line = TextFile.parse(GARC.parse(source).members[0].data).lines[0]
        row = {"record_id": "gen6:a/0/8/2:0000/00:00000",
               "source_variant_sha256": source_variant_hash(line.decoded_words),
               "scope": "shared", "version_scope": ["base"], "status": "validated",
               "translation_segments": [{"text": "е\u0308"}]}
        with self.assertRaisesRegex(ValueError, "NFC"):
            build_archive(source, "a/0/8/2", "pokemon-x", "base", [row])

    def test_rollback_restores_only_listed_targets(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            mod = root / "mods"
            backup = root / "backup"
            old_path = "0004000000055D00/romfs/a/0/7/4"
            new_path = "0004000000055D00/romfs/a/0/8/2"
            unrelated = mod / "0004000000055D00/romfs/a/9/9/9"
            old = mod / old_path
            old.parent.mkdir(parents=True)
            old.write_bytes(b"prior patch")
            unrelated.parent.mkdir(parents=True)
            unrelated.write_bytes(b"unrelated")
            manifest = backup_targets(mod, backup, [old_path, new_path])
            old.write_bytes(b"new pilot")
            new = mod / new_path
            new.parent.mkdir(parents=True)
            new.write_bytes(b"new pilot")
            unrelated.write_bytes(b"changed independently")
            restored = rollback_targets(mod, backup, manifest)
            self.assertEqual(set(restored), {old_path, new_path})
            self.assertEqual(old.read_bytes(), b"prior patch")
            self.assertFalse(new.exists())
            self.assertEqual(unrelated.read_bytes(), b"changed independently")

    def test_rollback_refuses_modified_backup_and_path_escape(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            mod = root / "mods"
            backup = root / "backup"
            relative = "title/romfs/a/0/7/4"
            target = mod / relative
            target.parent.mkdir(parents=True)
            target.write_bytes(b"original")
            manifest = backup_targets(mod, backup, [relative])
            (backup / relative).write_bytes(b"corrupt")
            with self.assertRaises(ValueError):
                rollback_targets(mod, backup, manifest)
            with self.assertRaises(ValueError):
                backup_targets(mod, root / "backup-2", ["../outside"])


if __name__ == "__main__":
    unittest.main()
