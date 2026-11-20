import json
import unittest
from pathlib import Path

from src.translation.catalog import expected_translation_controls, terminology_consistency_errors


ROOT = Path(__file__).resolve().parents[1]


def read_rows(path):
    with path.open(encoding="utf-8") as stream:
        return [json.loads(line) for line in stream]


class Milestone3GTests(unittest.TestCase):
    def test_neutral_dialogue_removes_only_gender_selection_events(self):
        early = {row["record_id"]: row for row in read_rows(ROOT / "translations/early-game.jsonl")}
        pc = early["gen6:a/0/8/2:0055/00:00001"]
        mirror = early["gen6:a/0/8/2:0055/00:00003"]
        player_variable = ["0010", "0002", "0100", "0000"]
        gender = ["0010", "0003", "1100", "00FF", "0202"]
        pc_events = [player_variable, gender, gender, ["0010", "0001", "BE01"], ["000A"], ["000A"],
                     ["0010", "0001", "BE01"], ["000A"], ["000A"]]
        mirror_events = [gender]
        for row, events, expected_removed in ((pc, pc_events, 2), (mirror, mirror_events, 1)):
            controls = [segment["control_words"] for segment in row["translation_segments"] if "control_words" in segment]
            self.assertEqual(controls, expected_translation_controls(row, events))
            self.assertEqual(len(row["control_adjustments"]), expected_removed)
        self.assertEqual(pc["translation_segments"][0], {"control_words": player_variable})
        self.assertIn("проверил(а)", pc["translation_segments"][1]["text"])
        self.assertNotIn("Ты", pc["translation_segments"][1]["text"])
        self.assertEqual(mirror["translation_segments"], [{"text": "…И ты уже без пижамы!"}])

    def test_gender_control_exception_cannot_remove_other_events(self):
        row = {"control_adjustments": [{"action": "remove_gender_selection",
                "control_words": ["0010", "0001", "BE01"], "reason": "bad"}]}
        with self.assertRaises(ValueError):
            expected_translation_controls(row, [["0010", "0001", "BE01"]])

    def test_battle_label_drafts_use_cyrillic_abbreviations(self):
        rows = read_rows(ROOT / "translations/milestone3g-battle.jsonl")
        targets = {row["record_id"]: row["translation_segments"][0]["text"] for row in rows}
        self.assertTrue(any(value == "ОЗ" for value in targets.values()))
        self.assertTrue(any(value == "ОС" for value in targets.values()))
        self.assertNotIn("OZ", targets.values())
        self.assertNotIn("OS", targets.values())
        self.assertEqual([ord(ch) for ch in "ОЗ"], [0x041E, 0x0417])
        self.assertEqual([ord(ch) for ch in "ОС"], [0x041E, 0x0421])
        glossary = json.loads((ROOT / "glossary/terms.json").read_text(encoding="utf-8"))
        battle_terms = {term["source"]: term for term in glossary["categories"]["battle_terminology"]}
        self.assertEqual(battle_terms["HP"]["russian_expansion"], "Очки здоровья")
        self.assertEqual(battle_terms["PP"]["russian_expansion"], "Очки силы")
        errors = terminology_consistency_errors("HP PP", [{"text": "ОЗ ОС"}], glossary)
        self.assertEqual(errors, [])
        self.assertTrue(terminology_consistency_errors("HP PP", [{"text": "OZ OS"}], glossary))


if __name__ == "__main__":
    unittest.main()
