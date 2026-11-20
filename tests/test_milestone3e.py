import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_script(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


builder = load_script("milestone3e_builder", "build_milestone3e_translations.py")
checklist = load_script("milestone3e_checklist", "generate_milestone3e_checklist.py")


class Milestone3ETests(unittest.TestCase):
    def test_replacement_keeps_control_order_and_unapproved_state(self):
        source = {
            "record_id": "gen6:a/0/8/2:0049/00:00000",
            "source_segments": [
                {"text": "Hey, "},
                {"control_words": ["0010", "0002", "0100", "0000"]},
                {"text": "!"},
                {"control_words": ["000A"]},
                {"text": "This way!"},
            ],
        }
        row = {"status": "machine_draft"}
        result = builder.set_translation(row, source, ["Эй, ", "!", "Сюда!"], "test")
        self.assertEqual(result["status"], "machine_draft")
        self.assertEqual(result["review_state"], "assistant_reviewed_pending_human")
        self.assertEqual([segment["control_words"] for segment in result["translation_segments"] if "control_words" in segment],
                         [["0010", "0002", "0100", "0000"], ["000A"]])
        self.assertFalse(result["review_evidence"]["runtime_checked"])

    def test_checklist_control_annotations_keep_original_words(self):
        self.assertEqual(checklist.display([{"text": "A"}, {"control_words": ["0010", "0001", "BE01"]}]),
                         "A[PAGE BREAK: 0010 0001 BE01]")


if __name__ == "__main__":
    unittest.main()
