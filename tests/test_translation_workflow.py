from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from src.translation.workflow import export_batch, import_batch
from scripts.report_translation_coverage import build_dashboard
from src.translation.catalog import validate_translation_rows


def source_record(record_id: str = "gen6:a/0/8/2:0001/00:00000") -> dict:
    return {
        "record_id": record_id,
        "source_variant_sha256": "a" * 64,
        "source_text": "Hello!",
        "source_segments": [{"text": "Hello!"}, {"control_words": ["000A"]}],
        "context": "test context",
        "occurrences": [{"dataset": "pokemon-x/base"}, {"dataset": "pokemon-y/base"}],
        "control_events": [["000A"]],
    }


class TranslationWorkflowTests(unittest.TestCase):
    def test_export_and_import_preserve_source_provenance_and_controls(self) -> None:
        source = source_record()
        batch = export_batch([source], {source["record_id"]})
        self.assertEqual(batch[0]["status"], "draft")
        self.assertEqual(batch[0]["translation_segments"], [{"text": ""}, {"control_words": ["000A"]}])
        batch[0]["translation_segments"][0]["text"] = "Привет!"
        clean = import_batch([source], batch, [])[0]
        self.assertNotIn("source_text", clean)
        self.assertEqual(clean["scope"], "shared")
        self.assertEqual(clean["translation_segments"][1], {"control_words": ["000A"]})

    def test_import_rejects_stale_source_and_changed_control(self) -> None:
        source = source_record()
        batch = export_batch([source], {source["record_id"]})
        batch[0]["translation_segments"][0]["text"] = "Привет!"
        batch[0]["translation_segments"][1]["control_words"] = ["0010", "0001", "BE01"]
        with self.assertRaises(ValueError):
            import_batch([source], batch, [])
        batch[0]["source_variant_sha256"] = "b" * 64
        with self.assertRaises(ValueError):
            import_batch([source], batch, [])

    def test_dashboard_tracks_states_and_untranslated_catalog_variants(self) -> None:
        source = source_record()
        source["source_language"] = "en"
        other = source_record("gen6:a/0/8/2:0001/00:00001")
        other["source_variant_sha256"] = "c" * 64
        other["source_language"] = "undetermined"
        translation = {"record_id": source["record_id"], "source_variant_sha256": source["source_variant_sha256"], "status": "approved"}
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            catalog = root / "catalog.jsonl"
            catalog.write_text("".join(json.dumps(r) + "\n" for r in (source, other)), encoding="utf-8")
            translations = root / "translations.jsonl"
            translations.write_text(json.dumps(translation) + "\n", encoding="utf-8")
            report = root / "scan.json"
            report.write_text(json.dumps({"messages": 2, "textfile_members": 1, "oversized_garc_skipped": [{"path": "a/big"}], "non_text_members": 4}), encoding="utf-8")
            result = build_dashboard(catalog, [translations], report)
        self.assertEqual(result["coverage"]["approved"], 1)
        self.assertEqual(result["coverage"]["untranslated_source_variants"], 1)
        self.assertEqual(result["coverage"]["identified_english_variants"], 1)
        self.assertEqual(result["coverage"]["translated_identified_english_variants"], 1)
        self.assertEqual(result["unsupported_or_unclassified"]["oversized_archives_skipped"], 1)

    def test_review_and_approval_states_require_attribution(self) -> None:
        source = source_record()
        row = {
            "record_id": source["record_id"],
            "source_variant_sha256": source["source_variant_sha256"],
            "status": "approved",
            "translation_segments": [{"text": "Привет!"}, {"control_words": ["000A"]}],
            "scope": "shared",
            "version_scope": ["base"],
        }
        errors = validate_translation_rows([source], [row])
        self.assertTrue(any("reviewer attribution" in error for error in errors))
        self.assertTrue(any("approver attribution" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
