from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts import build_milestone3j_text_candidate as text_candidate
from scripts.build_milestone3i_textures import EDITING, validate_editing_workspace
from scripts.build_milestone3j_contact_sheets import render_sheet
from src.rebuilding.pilot import effective_resource
from src.translation.catalog import read_jsonl

ROOT = Path(__file__).resolve().parents[1]


class Milestone3JTests(unittest.TestCase):
    def test_integrated_catalog_has_all_expected_unique_records(self):
        rows, summary = text_candidate.collect_translations()
        self.assertEqual(len(rows), 227)
        self.assertEqual(summary["record_count"], summary["unique_id_count"])
        self.assertEqual(summary["duplicate_ids"], summary["source_hash_conflicts"], 0)
        self.assertEqual({entry["record_count"] for entry in summary["input_files"]}, {12, 127, 33, 55})

    def test_duplicate_id_is_rejected_even_when_source_hash_matches(self):
        row = read_jsonl(ROOT / "translations/pilot.jsonl")[0]
        with tempfile.TemporaryDirectory() as temp:
            left, right = Path(temp) / "left.jsonl", Path(temp) / "right.jsonl"
            left.write_text(json.dumps(row) + "\n", encoding="utf-8")
            right.write_text(json.dumps(row) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "duplicate record ID"):
                text_candidate.collect_translations((left, right))

    def test_duplicate_id_with_changed_source_hash_is_rejected(self):
        row = read_jsonl(ROOT / "translations/pilot.jsonl")[0]
        conflicting = dict(row, source_variant_sha256="0" * 64)
        with tempfile.TemporaryDirectory() as temp:
            left, right = Path(temp) / "left.jsonl", Path(temp) / "right.jsonl"
            left.write_text(json.dumps(row) + "\n", encoding="utf-8")
            right.write_text(json.dumps(conflicting) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "source-hash conflict"):
                text_candidate.collect_translations((left, right))

    def test_effective_resource_prefers_update_and_falls_back_to_base(self):
        with tempfile.TemporaryDirectory() as temp:
            base, update = Path(temp) / "base", Path(temp) / "update"
            base.write_bytes(b"base")
            self.assertEqual(effective_resource(base, update), (base, "base"))
            update.write_bytes(b"update")
            self.assertEqual(effective_resource(base, update), (update, "update-1.5"))

    def test_canonical_png_workspace_is_rgba_sized_transparent_and_compatible(self):
        before = {path.name: text_candidate.sha256(path.read_bytes()) for path in EDITING.glob("*.png")}
        report = validate_editing_workspace(EDITING)
        after = {path.name: text_candidate.sha256(path.read_bytes()) for path in EDITING.glob("*.png")}
        self.assertEqual(report["assets_validated"], 24)
        self.assertEqual(before, after)
        self.assertTrue(all(item["rgba8"] and item["transparent_pixels"] and item["opaque_pixels"]
                            and item["bclim_format"] in (8, 9) for item in report["assets"]))

    def test_reference_sheets_embed_source_pngs_and_do_not_change_them(self):
        manifest = json.loads((EDITING / "manifest.json").read_text(encoding="utf-8"))
        before = {path.name: text_candidate.sha256(path.read_bytes()) for path in EDITING.glob("*.png")}
        english = render_sheet(manifest, language="en")
        russian = render_sheet(manifest, language="ru")
        after = {path.name: text_candidate.sha256(path.read_bytes()) for path in EDITING.glob("*.png")}
        self.assertIn(b"FIGHT", english)
        self.assertIn(b"POK\xc3\x89MON", english)
        self.assertIn("\u0411\u041e\u0419".encode(), russian)
        self.assertIn("\u041f\u041e\u041a\u0415\u041c\u041e\u041d\u042b".encode(), russian)
        self.assertEqual(english.count(b"data:image/png;base64,"), 24)
        self.assertEqual(russian.count(b"data:image/png;base64,"), 24)
        self.assertEqual(before, after)

    def test_integrated_build_reproduces_candidate_hashes_and_proofs(self):
        with tempfile.TemporaryDirectory() as temp:
            report = text_candidate.build_text_candidate(Path(temp) / "candidate")
        self.assertEqual(report["translation_records"], 227)
        self.assertFalse(report["installed"])
        self.assertFalse(report["runtime_tested"])
        for game_data in report["games"].values():
            self.assertGreater(game_data["translations_applied"], 90)
            self.assertEqual({item["resource"] for item in game_data["resources"]}, {"a/0/7/4", "a/0/8/2"})
            for item in game_data["resources"]:
                expected_version = "update-1.5" if item["resource"] == "a/0/7/4" else "base"
                self.assertEqual(item["source_version"], expected_version)
                self.assertGreater(item["unrelated_members_verified_unchanged"], 0)
                self.assertTrue(item["output_sha256"])

    def test_generated_candidate_rollback_removes_only_candidate_files(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "candidate"
            target = output / "pokemon-x/romfs/a/0/7/4"
            target.parent.mkdir(parents=True)
            target.write_bytes(b"generated")
            (output / "manifest.json").write_text(json.dumps({
                "milestone": "3J", "build_state": "unapproved_integrated_runtime_candidate"
            }), encoding="utf-8")
            self.assertEqual(text_candidate.rollback_text_candidate(output),
                             ["pokemon-x/romfs/a/0/7/4 (generated candidate removed)"])
            self.assertFalse(target.exists())


if __name__ == "__main__":
    unittest.main()
