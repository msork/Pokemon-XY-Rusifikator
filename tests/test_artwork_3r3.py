from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import Mock

from scripts.localize_textures import cached_ocr_stage, compare_vision
from src.rebuilding.artwork_localization import (
    ReviewRequired, Translator, required_artwork_terms, validate_artwork_translation,
)
from src.rebuilding.artwork_models import LocalArtworkModel


class Artwork3R3Tests(TestCase):
    def setUp(self):
        self.enforced = {"hp": "ОЗ", "pp": "ОС"}

    def test_stat_abbreviations_keep_values_and_separators_without_a_model(self):
        translator = Translator.__new__(Translator)
        translator.terms = translator.contextual_terms = {}
        translator.ui_labels = translator.ui_context = {}
        draft = Mock(side_effect=AssertionError("A glossary-only label called the model"))
        self.assertEqual(translator("HP 10 / PP 5", ("ui",), draft=draft, enforced=self.enforced),
                         ("ОЗ 10 / ОС 5", "glossary"))
        self.assertEqual(required_artwork_terms("SHOP UPPER", self.enforced), {})

    def test_contextual_draft_must_keep_numbers_and_each_required_stat(self):
        source = "Restore 10 HP and 5 PP"
        required = required_artwork_terms(source, self.enforced)
        validate_artwork_translation(source, "Восстановить 10 ОЗ и 5 ОС", required)
        self.assertEqual(required, {"HP": "ОЗ", "PP": "ОС"})
        with self.assertRaisesRegex(ReviewRequired, "stat abbreviations"):
            validate_artwork_translation(source, "Восстановить 10 ОЗ и 5 ОЗ", required)
        with self.assertRaisesRegex(ReviewRequired, "original numbers"):
            validate_artwork_translation(source, "Восстановить 5 ОЗ и 10 ОС", required)
        with self.assertRaisesRegex(ReviewRequired, "unsupported text"):
            validate_artwork_translation(source, "Восстановить 10 HP и 5 ОС", required)

    def test_vision_agreement_respects_locales_and_preserves_spatial_evidence(self):
        alternative = {"text": "TYPE 2", "confidence": 80}
        line = {"text": "TYPE Z", "confidence": 89, "alternatives": [alternative]}
        self.assertEqual(compare_vision("TYPE Z", [line], [line], "english")["agreement"], "classical_lines")
        self.assertEqual(compare_vision("TYPE 2", [line], [line], "english")["agreement"], "classical_alternative")
        self.assertEqual(compare_vision("TYPE 3", [line], [line], "english")["agreement"], "partial_classical_support")
        self.assertEqual(compare_vision("GER", [line], [], "other_language_or_locale")["agreement"], "locale_excluded")
        self.assertEqual(compare_vision("TYPE 2", [], [], "unconfirmed")["agreement"], "unconfirmed")
        self.assertNotIn("box", compare_vision("TYPE 2", [line], [line], "english"))

    def test_stage_cache_reuses_completed_calls_and_retries_failures(self):
        with TemporaryDirectory() as directory:
            cache = Path(directory)
            worker = Mock(side_effect=[RuntimeError("model unavailable"), "SCORE"])
            with self.assertRaises(RuntimeError):
                cached_ocr_stage(cache, ["weights-sha", "device", "image"], worker)
            self.assertEqual(cached_ocr_stage(cache, ["weights-sha", "device", "image"], worker), "SCORE")
            self.assertEqual(cached_ocr_stage(cache, ["weights-sha", "device", "image"], worker), "SCORE")
            self.assertEqual(worker.call_count, 2)

    def test_truncated_model_completion_is_ignored(self):
        model = LocalArtworkModel.__new__(LocalArtworkModel)
        model._request = Mock(return_value=(200, {"choices": [
            {"message": {"content": "ОЗ"}, "finish_reason": "length"},
        ]}))
        self.assertEqual(model.translate("HP", ("ui",), {"HP": "ОЗ"}), "")
        body = model._request.call_args.args[1]
        self.assertEqual(body["temperature"], 0)
        self.assertIn("ОЗ", body["messages"][0]["content"])
