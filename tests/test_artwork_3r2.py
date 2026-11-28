from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from PIL import Image, ImageDraw

from scripts.localize_textures import cached_ocr_stage
from src.rebuilding.artwork_localization import check_russian_spelling, classify_english, merge_ocr_observations
from src.rebuilding.artwork_rendering import (
    _detached_ink, _inspect_lettering, _matched_opacity, match_references, reference_style,
)


def reading(text, box, confidence, name):
    return {"text": text, "box": box, "confidence": confidence, "rotation": 0, "pass_name": name}


class Artwork3R2Tests(unittest.TestCase):
    def test_ocr_consensus_does_not_double_count_paddle_or_a_partial_line(self):
        observations = [
            reading("PUSH START BUTTON", [2, 5, 81, 19], 92, "tesseract-light"),
            reading("PUSH START BUTTON", [2, 5, 79, 19], 98, "paddle"),
            reading("PUSH", [2, 5, 31, 19], 99, "paddle"),
            reading("PUSH", [2, 5, 28, 18], 98, "paddle"),
        ]
        lines = merge_ocr_observations(observations)
        label, selected = classify_english(lines, "prompt.bclim", set())
        self.assertEqual(label, "english")
        self.assertEqual([row["text"] for row in selected], ["PUSH START BUTTON"])
        self.assertEqual(selected[0]["box"], [2, 5, 81, 19])
        self.assertEqual(selected[0]["passes"], ["paddle", "tesseract-light"])
        paddle_only = [row for row in observations if row["pass_name"] == "paddle"]
        self.assertEqual(classify_english(merge_ocr_observations(paddle_only), "prompt.bclim", set())[0],
                         "english_review")

    def test_template_matching_prefers_native_ink_shape(self):
        original = Image.new("RGBA", (60, 24))
        first = original.copy()
        second = original.copy()
        draw = ImageDraw.Draw(first)
        for x in (5, 12, 22, 31):
            draw.rectangle((x, 5, x + 2, 17), fill="white")
        ImageDraw.Draw(second).rectangle((5, 5, 33, 17), fill="white")
        a = dict(reference_style(original, first), name="strokes")
        b = dict(reference_style(original, second), name="rectangle")
        ink = first.getchannel("A")
        matches = match_references(ink.crop(ink.getbbox()), [b, a])
        self.assertEqual(matches[0][1]["name"], "strokes")
        self.assertAlmostEqual(matches[0][0], 1)

    def test_detached_ink_rejects_unrelated_alpha_island(self):
        mask = Image.new("L", (32, 28))
        draw = ImageDraw.Draw(mask)
        draw.rectangle((7, 3, 10, 24), fill=255)
        draw.rectangle((19, 3, 22, 24), fill=255)
        box = (7, 6, 23, 21)
        self.assertTrue(_detached_ink(mask, box, mask.getbbox()))
        draw.point((4, 4), fill=17)
        self.assertFalse(_detached_ink(mask, box, mask.getbbox()))

    def test_recovers_linear_backing_with_same_translucency(self):
        image = Image.new("RGBA", (41, 21))
        draw = ImageDraw.Draw(image)
        for x in range(41):
            draw.line((x, 0, x, 20), fill=(30 + x * 2, 20 + x, 10, 187))
        before = image.tobytes()
        for x in (10, 20, 28):
            draw.rectangle((x, 6, x + 1, 14), fill=(240, 210, 110, 187))
        _, recovered, mask, bounds, kind = _inspect_lettering(image, (10, 6, 30, 15))
        self.assertEqual(kind, "linear-gradient")
        self.assertEqual(bounds, (10, 6, 30, 15))
        self.assertEqual(bytes(channel for pixel in recovered for channel in pixel), before)
        self.assertEqual(mask.histogram()[255], 54)

    def test_soft_fringe_uses_original_representable_alpha_and_keeps_rank(self):
        values = _matched_opacity([0, 22, 22, 31, 70, 150, 255], [17, 34, 68, 170, 238, 255], 20)
        self.assertTrue(set(values.values()) <= {17, 34, 68, 170, 238, 255})
        self.assertNotIn(0, values)
        self.assertEqual(list(values.values()), sorted(values.values()))

    def test_russian_spelling_holds_misses_and_allows_named_project_terms(self):
        with patch("src.rebuilding.artwork_localization.subprocess.run") as command:
            command.return_value.stdout = "ошипка\n"
            command.return_value.stderr = ""
            self.assertEqual(check_russian_spelling("Мега Покедекс Ошипка", Path("hunspell"), Path("ru_RU")),
                             ["ошипка"])
            self.assertEqual(command.call_args.kwargs["input"], "ошипка\n")

    def test_ocr_stage_cache_reuses_same_observation_without_loading_model(self):
        with TemporaryDirectory() as temp:
            directory = Path(temp)
            with patch("builtins.print") as compute:
                compute.return_value = [{"text": "START"}]
                first = cached_ocr_stage(directory, ["eng", "model-hash"], compute)
                second = cached_ocr_stage(directory, ["eng", "model-hash"], compute)
                self.assertEqual(first, second)
                compute.assert_called_once()


if __name__ == "__main__":
    unittest.main()
