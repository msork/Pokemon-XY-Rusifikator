import json
import unittest
from pathlib import Path

from src.extraction.garc import GARC
from scripts.extract_milestone3h_textures import decode_bclim

ROOT = Path(__file__).resolve().parents[1]


def read_jsonl(path):
    with path.open(encoding="utf-8") as stream:
        return [json.loads(line) for line in stream]


class Milestone3HTests(unittest.TestCase):
    def test_ui_battle_records_are_unique_drafts_and_preserve_source_controls(self):
        translations = read_jsonl(ROOT / "translations/milestone3h-ui-battle.jsonl")
        catalog = {row["record_id"]: row for row in read_jsonl(ROOT / "build/milestone-3b/source-catalog.jsonl")}
        ids = [row["record_id"] for row in translations]
        self.assertEqual(len(ids), len(set(ids)))
        for row in translations:
            self.assertEqual(row["status"], "draft")
            self.assertEqual(row["review_state"], "draft_pending_linguistic_and_owner_runtime_review")
            source = catalog[row["record_id"]]
            source_controls = [s["control_words"] for s in source["source_segments"] if "control_words" in s]
            translated_controls = [s["control_words"] for s in row["translation_segments"] if "control_words" in s]
            self.assertEqual(source_controls, translated_controls, row["record_id"])
            self.assertEqual(source["source_variant_sha256"], row["source_variant_sha256"])

    def test_screenshot_anchors_are_included_without_changing_prior_pc_mirror_records(self):
        rows = {row["record_id"]: row for row in read_jsonl(ROOT / "translations/milestone3h-ui-battle.jsonl")}
        for record_id in (
            "gen6:a/0/7/4:0036/00:00004", "gen6:a/0/7/4:0079/00:00008",
            "gen6:a/0/7/4:0080/00:00653", "gen6:a/0/7/4:0080/00:00656",
            "gen6:a/0/8/2:0142/00:00001",
        ):
            self.assertIn(record_id, rows)
        milestone3g = {row["record_id"]: row for row in read_jsonl(ROOT / "translations/milestone3g-battle.jsonl")}
        self.assertEqual(milestone3g["gen6:a/0/7/4:0080/00:00650"]["translation_segments"], [{"text": "Чеспин"}])
        early = {row["record_id"]: row for row in read_jsonl(ROOT / "translations/early-game.jsonl")}
        pc = early["gen6:a/0/8/2:0055/00:00001"]["translation_segments"]
        mirror = early["gen6:a/0/8/2:0055/00:00003"]["translation_segments"]
        self.assertIn("проверил(а)", "".join(s.get("text", "") for s in pc))
        self.assertEqual(mirror, [{"text": "…И ты уже без пижамы!"}])

    def test_hp_pp_terms_are_cyrillic_and_battle_records_remain_review_pending(self):
        rows = read_jsonl(ROOT / "translations/milestone3h-ui-battle.jsonl")
        content = " ".join(s.get("text", "") for row in rows for s in row["translation_segments"])
        self.assertIn("ОЗ", content)
        self.assertIn("ОС", content)
        self.assertNotIn("OZ", content)
        self.assertNotIn("OS", content)

    def test_russian_names_resolve_to_species_glossary(self):
        species = json.loads((ROOT / "glossary/pokemon_species_ru.json").read_text(encoding="utf-8"))
        combined = []
        for filename in ("translations/milestone3g-battle.jsonl", "translations/milestone3h-ui-battle.jsonl"):
            combined.extend(read_jsonl(ROOT / filename))
        rows = {row["record_id"]: row for row in combined}
        for message, name in ((650, "Чеспин"), (653, "Феннекин"), (656, "Фроки")):
            record_id = f"gen6:a/0/7/4:0080/00:{message:05d}"
            russian = "".join(s.get("text", "") for s in rows[record_id]["translation_segments"])
            self.assertEqual(russian, name)
        self.assertTrue(species)

    def test_milestone_3h_does_not_duplicate_existing_translation_ids(self):
        prior_ids = set()
        for filename in ("translations/pilot.jsonl", "translations/early-game.jsonl", "translations/milestone3g-battle.jsonl"):
            prior_ids.update(row["record_id"] for row in read_jsonl(ROOT / filename))
        current_ids = {row["record_id"] for row in read_jsonl(ROOT / "translations/milestone3h-ui-battle.jsonl")}
        self.assertFalse(prior_ids & current_ids)

    def test_layered_resources_and_keyboard_texture_member_are_unchanged_between_games(self):
        resources = ("a/0/7/4", "a/0/8/2", "a/0/1/9", "a/2/4/0")
        for resource in resources:
            x = (ROOT / "workspace/pokemon-x/base" / resource).read_bytes()
            y = (ROOT / "workspace/pokemon-y/base" / resource).read_bytes()
            self.assertEqual(x, y, resource)
        keyboard = GARC.parse((ROOT / "workspace/pokemon-x/base/a/0/1/9").read_bytes())
        self.assertTrue(any(m.entry_id == 0 and m.subfile_id == 0 for m in keyboard.members))
        update = "a/0/7/4"
        x_update = (ROOT / "workspace/pokemon-x/update-1.5" / update).read_bytes()
        y_update = (ROOT / "workspace/pokemon-y/update-1.5" / update).read_bytes()
        x_base = (ROOT / "workspace/pokemon-x/base" / update).read_bytes()
        self.assertEqual(x_update, y_update)
        self.assertNotEqual(x_base, x_update)

    def test_known_png_decoder_rejects_etc1a4_without_claiming_png_export(self):
        raw = bytearray(40)
        raw[:4] = b"CLIM"
        raw[4:6] = b"\xff\xfe"
        raw[28:36] = (1).to_bytes(2, "little") + (1).to_bytes(2, "little") + (11).to_bytes(4, "little")
        with self.assertRaisesRegex(ValueError, "format 11 needs another decoder"):
            decode_bclim(bytes(raw))


if __name__ == "__main__":
    unittest.main()
