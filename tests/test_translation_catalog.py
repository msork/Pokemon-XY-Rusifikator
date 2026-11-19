import unittest
import json
from pathlib import Path

from src.translation.catalog import (_segments, duplicate_source_text_stats, missing_translation_variants, species_lookup,
                                    species_name_consistency_errors, validate_species_document,
                                    validate_terms_glossary, validate_translation_rows)


class TranslationCatalogTests(unittest.TestCase):
    def test_committed_species_glossary_has_source_metadata_and_lookup(self):
        root = Path(__file__).resolve().parents[1]
        glossary = json.loads((root / "glossary/pokemon_species_ru.json").read_text(encoding="utf-8"))
        validate_species_document(glossary)
        self.assertEqual(glossary["entry_count"], 721)
        self.assertEqual(glossary["source_revision_id"], 4640552)
        self.assertEqual(glossary["retrieved_date"], "2026-11-19")
        self.assertEqual(glossary["historical_source_counts"], {
            "official_pokemon_handbook": 45,
            "previous_official_pokedex_and_champions_handbook_ii": 64,
        })
        self.assertEqual(species_lookup(glossary, "Bulbasaur")["national_dex_number"], 1)

    def test_committed_terminology_glossary_is_categorized_and_does_not_invent_pending_terms(self):
        root = Path(__file__).resolve().parents[1]
        terms = json.loads((root / "glossary/terms.json").read_text(encoding="utf-8"))
        validate_terms_glossary(terms)
        self.assertGreater(len(terms["categories"]["ui"]), 0)
        self.assertTrue(any(row["status"] == "needs_research" for row in terms["categories"]["moves"]))

    def test_segments_preserve_control_arguments_containing_zero(self):
        self.assertEqual(_segments((ord("A"), 0x0010, 3, 0x1234, 0, 0x5678, ord("B"), 0)), [
            {"text": "A"},
            {"control_words": ["0010", "0003", "1234", "0000", "5678"]},
            {"text": "B"},
        ])

    def test_species_glossary_checks_full_dex_and_unique_lookup(self):
        entries = [{"national_dex_number": i, "english": f"Species{i}", "russian": f"Покемон{i}",
                    "name_status": "established_official_per_source"} for i in range(1, 722)]
        validate_species_document({"entries": entries})
        self.assertEqual(species_lookup({"entries": entries}, "species1")["national_dex_number"], 1)
        self.assertIsNone(species_lookup({"entries": entries}, "absent"))
        entries[-1]["english"] = "Species1"
        with self.assertRaises(ValueError):
            validate_species_document({"entries": entries})

    def test_translation_must_preserve_exact_control_sequence(self):
        source = [{"record_id": "id:1", "source_variant_sha256": "abc", "source_text": "Hello",
                   "control_events": [["0010", "0002", "BE01"]]}]
        valid = [{"record_id": "id:1", "source_variant_sha256": "abc", "status": "machine_draft",
                  "translation_segments": [{"text": "Привет"}, {"control_words": ["0010", "0002", "BE01"]}]}]
        self.assertEqual(validate_translation_rows(source, valid), [])
        valid[0]["translation_segments"].pop()
        self.assertTrue(any("control/placeholder" in error for error in validate_translation_rows(source, valid)))

    def test_missing_translation_report_distinguishes_source_variants(self):
        source = [
            {"record_id": "same", "source_variant_sha256": "x"},
            {"record_id": "same", "source_variant_sha256": "y"},
        ]
        self.assertEqual(missing_translation_variants(source, [{"record_id": "same", "source_variant_sha256": "x"}]), [("same", "y")])

    def test_duplicate_text_is_reported_without_merging_coordinates(self):
        records = [{"record_id": "one", "source_text": "Yes"}, {"record_id": "two", "source_text": "Yes"}, {"record_id": "three", "source_text": "No"}]
        self.assertEqual(duplicate_source_text_stats(records), (1, 2))

    def test_translation_rejects_non_nfc_or_non_bmp(self):
        source = [{"record_id": "id:1", "source_variant_sha256": "abc", "source_text": "A", "control_events": []}]
        rows = [{"record_id": "id:1", "source_variant_sha256": "abc", "status": "machine_draft",
                 "translation_segments": [{"text": "е\u0308"}]}]
        self.assertTrue(any("non-NFC" in error for error in validate_translation_rows(source, rows)))
        rows[0]["translation_segments"] = [{"text": "😀"}]
        self.assertTrue(any("unsupported character" in error for error in validate_translation_rows(source, rows)))

    def test_species_name_consistency_uses_official_mapping(self):
        species = {"entries": [{"english": "Pikachu", "russian": "Пикачу"}]}
        self.assertEqual(species_name_consistency_errors("Pikachu used Thunderbolt.", [{"text": "Пикачу применил атаку."}], species), [])
        self.assertTrue(species_name_consistency_errors("Pikachu appeared.", [{"text": "Появился Пикач"}], species))


if __name__ == "__main__":
    unittest.main()
