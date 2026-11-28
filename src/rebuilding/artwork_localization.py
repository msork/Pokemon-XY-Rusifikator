"""Offline OCR, glossary lookup and conservative texture lettering."""
from __future__ import annotations

from collections import Counter, defaultdict
import csv
from io import BytesIO, StringIO
import json
import os
from pathlib import Path
import re
import subprocess
import unicodedata

from PIL import Image, ImageDraw, ImageFont


class ReviewRequired(ValueError):
    """The texture cannot be edited safely with the current heuristics."""


def ocr(image: Image.Image, executable: Path, tessdata: Path) -> list[dict]:
    """Read sparse text on light and dark composites and keep the stronger pass."""
    scale = max(1, min(4, 1600 // max(image.size)))
    border = 12
    passes = []
    for backdrop in (255, 0):
        canvas = Image.new("L", (image.width * scale + 2 * border, image.height * scale + 2 * border), 255)
        composite = Image.new("RGBA", image.size, (backdrop,) * 3 + (255,))
        composite.alpha_composite(image)
        gray = composite.convert("L").resize((image.width * scale, image.height * scale), Image.Resampling.BICUBIC)
        if backdrop == 0:
            gray = gray.point(lambda value: 255 - value)
        canvas.paste(gray, (border, border))
        lines = []
        for line in _read_lines(canvas, executable, tessdata, "eng", 11):
            x, y, right, bottom = (v - border for v in line["box"])
            lines.append({"english": line["text"], "confidence": line["confidence"],
                          "box": [max(0, x // scale), max(0, y // scale),
                                  min(image.width, -(-right // scale)), min(image.height, -(-bottom // scale))]})
        passes.append(lines)
    return max(passes, key=lambda lines: sum(
        max(0, line["confidence"] - 55) * len(line["english"]) for line in lines
    ))


def glossary_key(text: str) -> str:
    return "".join(character for character in unicodedata.normalize("NFKD", text.casefold())
                   if not unicodedata.combining(character))


def required_artwork_terms(source: str, enforced: dict[str, str]) -> dict[str, str]:
    tokens = set(re.findall(r"[a-z]+", glossary_key(source)))
    return {word.upper(): enforced[word] for word in sorted(tokens & enforced.keys())}


def translate_stat_label(source: str, required: dict[str, str]) -> str | None:
    """Translate bare stat abbreviations while preserving their separators and values."""
    if not required or not re.fullmatch(r"[a-zA-Z0-9\s./%:+−–-]+", source):
        return None
    tokens = re.findall(r"[a-zA-Z]+", source)
    if any(token.upper() not in required for token in tokens):
        return None
    return re.sub(r"[a-zA-Z]+", lambda match: required[match[0].upper()], source)


def validate_artwork_translation(source: str, russian: str, required: dict[str, str]) -> None:
    if not re.search("[А-Яа-яЁё]", russian) or any(
        character.isalpha() and not re.fullmatch("[А-Яа-яЁё]", character) for character in russian
    ) or not russian.isprintable():
        raise ReviewRequired("Translation contains unsupported text")
    words = Counter(re.findall("[А-Яа-яЁё]+", russian.upper()))
    source_words = Counter(re.findall(r"[a-zA-Z]+", source.upper()))
    if any(words[target.upper()] != source_words[term] for term, target in required.items()):
        raise ReviewRequired("Translation does not preserve the required stat abbreviations")
    if re.findall(r"\d+", source) != re.findall(r"\d+", russian):
        raise ReviewRequired("Translation does not preserve the original numbers")


class Translator:
    def __init__(self, glossary: bytes, model_dir: Path, device: str = "cpu"):
        import ctranslate2
        import sentencepiece

        categories = json.loads(glossary)["categories"]
        self.terms = defaultdict(set)
        self.contextual_terms = defaultdict(lambda: defaultdict(set))
        for category, records in categories.items():
            for record in records:
                key = glossary_key(record["source"])
                self.terms[key].add(record["russian"])
                self.contextual_terms[key][category].add(record["russian"])
        self.ui_labels = defaultdict(set)
        self.ui_context = defaultdict(lambda: defaultdict(set))
        for category, records in categories.items():
            for record in records:
                key = text_key(record["source"])
                self.ui_labels[key].add(record["russian"])
                self.ui_context[key][category].add(record["russian"])
        metadata = json.loads((model_dir / "metadata.json").read_bytes())
        if (metadata["from_code"], metadata["to_code"]) != ("en", "ru"):
            raise ValueError("Expected a direct English-to-Russian Argos model")
        self.tokenizer = sentencepiece.SentencePieceProcessor(model_file=str(model_dir / "sentencepiece.model"))
        self.model = ctranslate2.Translator(str(model_dir / "model"), device=device, intra_threads=1)

    def __call__(self, english: str, context: tuple[str, ...] = (), *, draft=None,
                 enforced: dict[str, str] | None = None) -> tuple[str, str]:
        required = required_artwork_terms(english, enforced or {})
        key = glossary_key(english)
        terms = self.terms.get(key)
        for category in context:
            match = self.contextual_terms.get(key, {}).get(category)
            if match:
                terms = match
                break
        if terms is None and context:
            label = text_key(english)
            terms = self.ui_labels.get(label)
            for category in context:
                match = self.ui_context.get(label, {}).get(category)
                if match:
                    terms = match
                    break
        literal = translate_stat_label(english, required)
        if terms:
            if len(terms) != 1 or None in terms:
                raise ReviewRequired("The glossary requires terminology review")
            russian, = terms
            method = "glossary"
        elif literal:
            russian, method = literal, "glossary"
        elif draft:
            russian = draft(english, context, required)
            method = "local_llm"
        else:
            result, = self.model.translate_batch([self.tokenizer.encode(english.lower() if english.isupper() else english, out_type=str)], beam_size=4)
            russian = self.tokenizer.decode(result.hypotheses[0])
            method = "offline_model"
        russian = russian.upper() if english.isupper() else russian
        if enforced is not None:
            validate_artwork_translation(english, russian, required)
            return russian, method
        if not re.search("[А-Яа-яЁё]", russian) or any(
            character.isalpha() and not re.fullmatch("[А-Яа-яЁё]", character) for character in russian
        ) or not russian.isprintable():
            raise ReviewRequired("Translation contains unsupported text")
        return russian, method


def check_russian_spelling(text: str, executable: Path, dictionary: Path) -> list[str]:
    """Return dictionary misses, excluding the project's explicit UI terms."""
    known = {"покедекс", "покемон", "покемоны", "покемонов", "покерус", "покэрус", "мега",
             "оз", "ос", "оп", "сп", "ур"}
    words = {word.casefold() for word in re.findall("[А-Яа-яЁё]+", text)} - known
    if not words:
        return []
    output = subprocess.run(
        [str(executable), "-d", str(dictionary.resolve()), "-i", "UTF-8", "-l"],
        input="\n".join(sorted(words)) + "\n", text=True, encoding="utf-8", timeout=20,
        capture_output=True, check=True,
    )
    if output.stderr.strip():
        raise ValueError(f"Russian spelling dictionary error: {output.stderr.strip()}")
    return sorted(set(output.stdout.splitlines()))


def render(image: Image.Image, box: list[int], russian: str, font_path: Path) -> Image.Image:
    """Replace lettering only where a flat background and its palette can be inferred."""
    x0, y0, x1, y1 = box
    outer = (max(0, x0 - 3), max(0, y0 - 3), min(image.width, x1 + 3), min(image.height, y1 + 3))
    crop = image.crop(outer)
    width, height = crop.size
    if width < 5 or height < 5:
        raise ReviewRequired("Text region is too small")
    # Ignore hidden RGB when classifying transparent pixels. Preserve it in the output.
    pixels = [p if p[3] else (0, 0, 0, 0) for p in crop.get_flattened_data()]
    edge = {p for i, p in enumerate(pixels) if i % width in (0, width - 1) or i // width in (0, height - 1)}
    if len(edge) != 1:
        raise ReviewRequired("Text touches artwork or a nonuniform background")
    background, = edge
    colors = Counter(pixels)
    del colors[background]
    foreground_rgb = {color[:3] for color in colors}
    alpha_levels = sorted({0, *(color[3] for color in colors)})
    monochrome_sprite = background[3] == 0 and len(foreground_rgb) == 1 and alpha_levels[-1] == 255
    opaque_ramp = (background[3] == 255 and len(colors) > 2 and
                   max(background[:3]) - min(background[:3]) == 0 and
                   all(color[3] == 255 and max(color[:3]) - min(color[:3]) <= 17 for color in colors) and
                   (all(min(color[:3]) >= background[0] for color in colors) or
                    all(max(color[:3]) <= background[0] for color in colors)))
    if not (monochrome_sprite or opaque_ramp) and (
        len(colors) not in (1, 2) or any(color[3] != 255 for color in colors) or background[3] not in (0, 255)
    ):
        raise ReviewRequired("Text has a complex palette or partial alpha")
    fill, *rest = colors
    outline = None
    if rest and not (monochrome_sprite or opaque_ramp):
        # An outline must surround the interior color on all four sides.
        for candidate, stroke in (tuple(colors), tuple(reversed(colors))):
            if all(all(pixels[i + offset] in (candidate, stroke) for offset in (-1, 1, -width, width))
                   for i, p in enumerate(pixels) if p == candidate):
                fill, outline = candidate, stroke
                break
        if outline is None:
            raise ReviewRequired("Cannot distinguish outline from adjacent artwork")
    ink = Image.new("L", crop.size)
    ink.putdata([255 if p != background else 0 for p in pixels])
    left, top, right, bottom = ink.getbbox()
    margins = (x0 - outer[0], y0 - outer[1], x1 - outer[0], y1 - outer[1])
    if any(abs(a - b) > 2 for a, b in zip((left, top, right, bottom), margins)):
        raise ReviewRequired("Foreground extent differs from the OCR bounds")
    # Empty space surrounding the detected lettering is preserved.
    stroke_width = int(outline is not None)
    for size in range(2 * (bottom - top), 5, -1):
        font = ImageFont.truetype(str(font_path), size)
        bounds = font.getbbox(russian, stroke_width=stroke_width)
        text_width, text_height = bounds[2] - bounds[0], bounds[3] - bounds[1]
        if text_width <= right - left and text_height <= bottom - top:
            break
    else:
        raise ReviewRequired("Cyrillic lettering does not fit at a legible size")
    position = (left + (right - left - text_width) // 2 - bounds[0],
                top + (bottom - top - text_height) // 2 - bounds[1])
    if background[3] == 0:
        alpha = crop.getchannel("A")
        alpha.paste(0, (0, 0, width, height), ink)
        crop.putalpha(alpha)
    else:
        crop.paste(background, (0, 0, width, height), ink)
    if monochrome_sprite or opaque_ramp:
        mask = Image.new("L", crop.size)
        ImageDraw.Draw(mask).text(position, russian, font=font, fill=255)
        if monochrome_sprite:
            mask = mask.point([min(alpha_levels, key=lambda alpha: abs(alpha - value)) for value in range(256)])
            color, = foreground_rgb
            letters = Image.new("RGBA", crop.size, color + (255,))
            letters.putalpha(mask)
        else:
            palette = [background, *colors]
            fill = max(colors, key=lambda color: abs(sum(color[:3]) - sum(background[:3])))
            lookup = [
                min(palette, key=lambda color: sum(
                    (sample - (bg + (fg - bg) * level / 255)) ** 2
                    for sample, bg, fg in zip(color[:3], background[:3], fill[:3])
                ))
                for level in range(256)
            ]
            letters = Image.new("RGBA", crop.size)
            letters.putdata([lookup[level] for level in mask.get_flattened_data()])
        crop.paste(letters, mask=mask.point([0] + [255] * 255))
    else:
        for color, stroke in ([(outline, 1)] if outline else []) + [(fill, 0)]:
            mask = Image.new("1", crop.size)
            ImageDraw.Draw(mask).text(position, russian, font=font, fill=1, stroke_width=stroke)
            crop.paste(color, (0, 0, width, height), mask)
    output = image.copy()
    output.paste(crop, outer[:2])
    return output


def _read_lines(canvas: Image.Image, executable: Path, tessdata: Path, language: str, psm: int) -> list[dict]:
    buffer = BytesIO()
    canvas.save(buffer, format="PNG")
    result = subprocess.run(
        [str(executable), "stdin", "stdout", "--tessdata-dir", str(tessdata),
         "-l", language, "--psm", str(psm), "-c", "tessedit_create_tsv=1"],
        input=buffer.getvalue(), capture_output=True, check=True, timeout=60,
        env={**os.environ, "OMP_THREAD_LIMIT": "1"},
    )
    groups = defaultdict(list)
    for word in csv.DictReader(StringIO(result.stdout.decode("utf-8")), delimiter="\t", quoting=csv.QUOTE_NONE):
        if word["level"] == "5" and word["text"].strip():
            groups[tuple(word[key] for key in ("block_num", "par_num", "line_num"))].append(word)
    return [{
        "text": " ".join(w["text"] for w in words),
        "confidence": min(float(w["conf"]) for w in words),
        "box": [min(int(w["left"]) for w in words), min(int(w["top"]) for w in words),
                max(int(w["left"]) + int(w["width"]) for w in words),
                max(int(w["top"]) + int(w["height"]) for w in words)],
    } for words in groups.values()]


def _unrotate_box(box: list[int], width: int, height: int, angle: int) -> list[int]:
    l, t, r, b = box
    if angle == 90:
        return [width - b, l, width - t, r]
    if angle == 180:
        return [width - r, height - b, width - l, height - t]
    if angle == 270:
        return [t, height - r, b, height - l]
    return box


OCR_PASSES = (
    ("light", 0, 11), ("dark", 0, 11), ("light-contrast", 0, 6), ("dark-contrast", 0, 6),
    ("alpha", 0, 11), ("dark-contrast", 0, 7), ("light-contrast", 90, 11),
    ("light-contrast", 180, 11), ("light-contrast", 270, 11),
)
_ROTATIONS = {90: Image.Transpose.ROTATE_90, 180: Image.Transpose.ROTATE_180, 270: Image.Transpose.ROTATE_270}


def _ocr_canvas(image: Image.Image, kind: str, angle: int) -> tuple[Image.Image, int]:
    from PIL import ImageOps

    if angle:
        image = image.transpose(_ROTATIONS[angle])
    if kind == "alpha":
        gray = ImageOps.invert(image.getchannel("A"))
    else:
        dark = kind.startswith("dark")
        fill = 0 if dark else 255
        plane = Image.new("RGBA", image.size, (fill, fill, fill, 255))
        plane.alpha_composite(image)
        gray = plane.convert("L")
        if dark:
            gray = ImageOps.invert(gray)
    if kind.endswith("contrast"):
        gray = ImageOps.autocontrast(gray, cutoff=0.5)
    scale = max(1, min(6, 1600 // max(gray.size)))
    return ImageOps.expand(gray.resize((gray.width * scale, gray.height * scale), Image.Resampling.LANCZOS),
                           border=12, fill=255), scale


def _intersection(a, b) -> int:
    return max(0, min(a[2], b[2]) - max(a[0], b[0])) * max(0, min(a[3], b[3]) - max(a[1], b[1]))


def _area(b) -> int:
    return (b[2] - b[0]) * (b[3] - b[1])


def _same_region(a, b) -> bool:
    return _intersection(a, b) >= 0.55 * max(_area(a), _area(b))


def text_key(text: str) -> str:
    label = glossary_key(text)
    label = re.sub(r"(?:\b[a-z]\.){2,}", lambda match: match[0].replace(".", ""), label)
    label = re.sub(r"(?<=[a-z])(?=[0-9])|(?<=[0-9])(?=[a-z])", " ", label)
    return " ".join(re.findall(r"[^\W_]+", label, flags=re.UNICODE))


def _vote_key(text: str) -> str:
    key = text_key(text)
    compact = key.replace(" ", "")
    return compact if compact in _UI_WORDS and len(key.split()) > 1 else key


def _ink_windows(image: Image.Image):
    """Isolate sparse high-contrast or chromatic lettering from busy artwork."""
    from PIL import ImageOps

    if image.width * image.height > 240_000:
        return
    pixels = image.get_flattened_data()
    filters = (
        ("light-ink", lambda r, g, b: min(r, g, b) >= 190),
        ("dark-ink", lambda r, g, b: max(r, g, b) <= 72),
        ("red-ink", lambda r, g, b: r - max(g, b) >= 56),
        ("green-ink", lambda r, g, b: g - max(r, b) >= 44),
        ("blue-ink", lambda r, g, b: b - max(r, g) >= 44),
    )
    w, h = image.size
    for name, match in filters:
        mask = Image.new("L", image.size)
        bits = bytes(255 if a >= 96 and match(r, g, b) else 0 for r, g, b, a in pixels)
        mask.putdata(bits)
        runs = []
        start = None
        for y in range(h + 1):
            has_ink = y < h and bits[y * w:(y + 1) * w].count(255) >= 2
            if has_ink and start is None:
                start = y
            elif not has_ink and start is not None:
                if y - start >= 4:
                    runs.append((start, y))
                start = None
        if len(runs) > 8:
            continue
        for y, bottom in runs:
            band = mask.crop((0, y, w, bottom))
            bounds = band.getbbox()
            if bounds is None:
                continue
            glyphs = band.crop(bounds)
            if glyphs.width < max(8, glyphs.height * 1.15) or glyphs.histogram()[255] > 0.74 * glyphs.width * glyphs.height:
                continue
            scale = max(1, min(8, 1600 // max(glyphs.size)))
            gray = ImageOps.invert(glyphs).resize((glyphs.width * scale, glyphs.height * scale),
                                                 Image.Resampling.BICUBIC)
            yield name, (bounds[0], y), ImageOps.expand(gray, border=12, fill=255), scale, 7

    # A saturated foreground can span two stacked baselines. Retain the
    # two-dimensional layout when thin decorative curves bridge row bands.
    for channel, name in enumerate(("red", "green", "blue")):
        for minimum, psm in ((140, 11), (140, 6), (165, 6)):
            mask = Image.new("L", image.size)
            mask.putdata([255 if rgba[3] >= 110 and rgba[channel] >= minimum
                          and all(rgba[channel] - rgba[other] >= 70 for other in range(3) if other != channel)
                          else 0 for rgba in pixels])
            bounds = mask.getbbox()
            if bounds is None:
                continue
            glyphs = mask.crop(bounds)
            if min(glyphs.size) < 8 or glyphs.histogram()[255] > 0.5 * glyphs.width * glyphs.height:
                continue
            scale = max(1, min(7, 1600 // max(glyphs.size)))
            frame = ImageOps.invert(glyphs).resize((glyphs.width * scale, glyphs.height * scale),
                                                   Image.Resampling.BICUBIC)
            yield f"{name}-core-{minimum}/{psm}", bounds[:2], ImageOps.expand(frame, border=12, fill=255), scale, psm


def tesseract_observations(image: Image.Image, executable: Path, tessdata: Path, language: str) -> list[dict]:
    """Collect Tesseract readings in native RGBA coordinates."""
    candidates = []
    for kind, angle, psm in OCR_PASSES:
        if language == "rus" and (angle or psm == 11 and kind == "alpha"):
            continue
        if kind == "alpha" and image.getchannel("A").getextrema()[0] == 255:
            continue
        frame, scale = _ocr_canvas(image, kind, angle)
        rotated_size = (image.height, image.width) if angle in (90, 270) else image.size
        for line in _read_lines(frame, executable, tessdata, language, psm):
            left, top, right, bottom = [v - 12 for v in line["box"]]
            w, h = rotated_size
            scaled = [max(0, left // scale), max(0, top // scale),
                      min(w, -(-right // scale)), min(h, -(-bottom // scale))]
            box = _unrotate_box(scaled, *image.size, angle)
            if box[0] >= box[2] or box[1] >= box[3] or line["confidence"] < 25 or not text_key(line["text"]):
                continue
            candidates.append(dict(line, box=box, rotation=angle, pass_name=f"{kind}/{psm}"))
    if language == "eng":
        for kind, (x, y), frame, scale, psm in _ink_windows(image):
            for line in _read_lines(frame, executable, tessdata, language, psm):
                if line["confidence"] < 25 or not text_key(line["text"]):
                    continue
                l, t, r, b = (value - 12 for value in line["box"])
                box = [max(0, x + l // scale), max(0, y + t // scale),
                       min(image.width, x - (-r // scale)), min(image.height, y - (-b // scale))]
                if box[0] < box[2] and box[1] < box[3]:
                    candidates.append(dict(line, box=box, rotation=0, pass_name=kind))
    # A tight native crop helps single-line status badges that Tesseract
    # otherwise treats as border noise or fragments.
    if language == "eng":
        for box, angle in _compact_windows(image):
            crop = image.crop(box)
            if angle:
                crop = crop.transpose(_ROTATIONS[angle])
            for kind in ("light-contrast", "dark-contrast"):
                frame, scale = _ocr_canvas(crop, kind, 0)
                for line in _read_lines(frame, executable, tessdata, language, 7):
                    if line["confidence"] < 25 or not text_key(line["text"]):
                        continue
                    l, t, r, b = (value - 12 for value in line["box"])
                    local = [max(0, l // scale), max(0, t // scale),
                             min(crop.width, -(-r // scale)), min(crop.height, -(-b // scale))]
                    if _area(local) <= 0 or local[0] >= local[2] or local[1] >= local[3]:
                        continue
                    native = _unrotate_box(local, box[2] - box[0], box[3] - box[1], angle)
                    native = [n + box[i % 2] for i, n in enumerate(native)]
                    candidates.append(dict(line, box=native, rotation=angle, pass_name=f"compact-{kind}/7"))
    return candidates


def _compact_windows(image: Image.Image):
    w, h = image.size
    if w * h > 32_000:
        return
    alpha = image.getchannel("A").point(lambda value: 255 if value >= 85 else 0)
    bounds = alpha.getbbox()
    if bounds is None:
        return
    l, t, r, b = bounds
    if r - l >= 1.7 * (b - t) and 5 <= b - t <= 65:
        yield bounds, 0
        if b - t <= 18 and r - l >= 72:
            # UI strips often carry a short label beside a long horizontal bar.
            yield (l, t, min(r, l + 42), b), 0
    if b - t >= 1.7 * (r - l) and 5 <= r - l <= 65:
        yield bounds, 90
        yield bounds, 270


def paddle_observations(image: Image.Image, candidates: list[dict], paddle) -> list[dict]:
    """Read independent compact/ink windows as well as Tesseract regions."""
    windows = []
    for line in sorted(candidates, key=lambda row: -row["confidence"]):
        box, angle = line["box"], line["rotation"]
        if not any(angle == old_angle and _same_region(box, old_box) for old_box, old_angle, _ in windows):
            windows.append((box, angle, None))
        if len(windows) == 12:
            break
    for box, angle in _compact_windows(image):
        if (box, angle, None) not in windows:
            windows.append((box, angle, None))
    w, h = image.size
    if 18 <= w <= 100 and 6 <= h <= 18:
        for inset in (1, 3, 5):
            windows.append(((inset, 1, w - inset, h - 1), 0, None))
    elif 35 <= w <= 128 and 24 <= h <= 80:
        # A short caption often sits below a central emblem.
        windows.append(((w * 12 // 100, h * 54 // 100, w * 88 // 100, h * 95 // 100), 0, None))

    # Region widths exclude the zero padding introduced by preprocessing.
    # Keep color-binary rasters as alternate recognizer inputs.
    ink_boxes = []
    for _, (x, y), frame, scale, psm in _ink_windows(image):
        if psm != 7:
            continue
        width, height = (frame.width - 24) // scale, (frame.height - 24) // scale
        box = (x, y, x + width, y + height)
        if width < height * 1.35 or min(width, height) < 4:
            continue
        if any(_same_region(box, earlier) for earlier in ink_boxes):
            continue
        ink_boxes.append(box)
        windows.append((box, 0, frame.convert("RGBA")))
        if len(ink_boxes) == 6:
            break
    results = []
    for box, angle, isolated in windows:
        crop = image.crop(box)
        if angle:
            crop = crop.transpose(_ROTATIONS[angle])
        answer = paddle(isolated if isolated is not None else crop)
        if answer is None:
            continue
        text, confidence = answer
        if confidence >= 50 and text_key(text):
            results.append(dict(text=text, confidence=confidence, box=list(box), rotation=angle, pass_name="paddle"))
    return results


def merge_ocr_observations(candidates: list[dict]) -> list[dict]:
    """Return spatial consensus. Multiple Paddle crops count as one pass."""
    groups: list[list[dict]] = []
    for line in sorted(candidates, key=lambda row: (-row["confidence"], row["box"], row["text"])):
        def equivalent(group):
            previous = group[0]
            if _same_region(previous["box"], line["box"]):
                return True
            return (previous["rotation"] == line["rotation"]
                    and _vote_key(previous["text"]) == _vote_key(line["text"])
                    and _intersection(previous["box"], line["box"]) >= 0.6 * min(_area(previous["box"]), _area(line["box"])))

        matched = next((group for group in groups if equivalent(group)), None)
        if matched is None:
            groups.append([line])
        else:
            matched.append(line)
    results = []
    for group in groups:
        votes = defaultdict(list)
        for observation in group:
            votes[(_vote_key(observation["text"]), observation["rotation"])].append(observation)
        def support(batch):
            best = {}
            for row in batch:
                name = row["pass_name"]
                best[name] = max(best.get(name, 0), row["confidence"])
            distinct = sorted(best.values(), reverse=True)
            return (sum(max(0, conf - 50) for conf in distinct[:4]), distinct[0])

        ranked = sorted(votes.values(), key=support, reverse=True)
        hypotheses = []
        for batch in ranked[:3]:
            winner = max(batch, key=lambda row: row["confidence"])
            # Prefer a token-local Tesseract box to Paddle's crop boundary.
            positioned = [row for row in batch if row["pass_name"] != "paddle" and row["confidence"] >= 55]
            if positioned:
                winner = dict(winner, box=max(positioned, key=lambda row: row["confidence"])["box"])
            passes = sorted({row["pass_name"] for row in batch if row["confidence"] >= 65})
            opposition = max((max(row["confidence"] for row in other) for other in ranked if other is not batch),
                             default=0)
            hypotheses.append(dict(winner, passes=passes, competing_confidence=opposition))
        results.append(dict(hypotheses[0], alternatives=hypotheses[1:]))
    return sorted(results, key=lambda line: (line["box"][1], line["box"][0], -line["confidence"]))


def multi_pass_ocr(image: Image.Image, executable: Path, tessdata: Path,
                   language: str = "eng", paddle=None) -> list[dict]:
    candidates = tesseract_observations(image, executable, tessdata, language)
    if paddle is not None:
        candidates.extend(paddle_observations(image, candidates, paddle))
    return merge_ocr_observations(candidates)


def local_paddle(model: Path, name: str, device: str):
    os.environ["PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK"] = "True"
    from paddleocr import TextRecognition
    import numpy as np

    engine = TextRecognition(model_name=name, model_dir=str(model), device=device, cpu_threads=1)
    def recognize(image: Image.Image):
        frame, _ = _ocr_canvas(image, "dark-contrast", 0)
        for result in engine.predict(np.asarray(frame.convert("RGB")), batch_size=1):
            data = result.json["res"]
            return data["rec_text"], 100 * data["rec_score"]
        return None
    return recognize


_UI_WORDS = frozenset("""
    all appearance asleep bag battle burned button champion cleared color compare congratulations
    cry dark decorate dragon draw electric exp fairy fainted fight fighting fire flying frozen ghost
    grass ground habitat high hp ice internet kalos league lose mega mountain national new normal
    speed attack defense special sp def atk ko
    paralysis play poison poisoned pokedex pokemon pokerus psychic push results rock run score
    shape shift start steel switch type victory water win evolution coastal
""".split())


def _overlapping_line(a: dict, b: dict) -> bool:
    if a["rotation"] != b["rotation"]:
        return _same_region(a["box"], b["box"])
    box_a, box_b = a["box"], b["box"]
    overlap = _intersection(box_a, box_b)
    if overlap >= 0.65 * min(_area(box_a), _area(box_b)):
        return True
    x0, y0, x1, y1 = box_a
    l, t, r, bottom = box_b
    # Eliminate fragments on the same baseline when a larger OCR crop
    # contains the shorter phrase. Keep genuinely stacked lines separate.
    if a["rotation"] in (90, 270):
        x0, y0, x1, y1 = y0, x0, y1, x1
        l, t, r, bottom = t, l, bottom, r
    shared_words = set(_vote_key(a["text"]).split()) & set(_vote_key(b["text"]).split())
    return bool(shared_words and min(y1, bottom) - max(y0, t) >= 0.5 * min(y1 - y0, bottom - t)
                and min(x1, r) - max(x0, l) >= 0.45 * min(x1 - x0, r - l))


def classify_english(lines: list[dict], filename: str, vocabulary: set[str]) -> tuple[str, list[dict]]:
    stem = filename.casefold()
    if stem.startswith("the_end_txt") or re.search(r"(?:^|_)(fra|ger|ita|jpn|kor|spa)(?:\d+)?\.", stem):
        return "other_language_or_locale", []
    foreign = {"drucke", "drucken", "appuyez", "pulsa", "sur", "des", "der", "und"}
    if any(line["confidence"] >= 75 and foreign.intersection(text_key(line["text"]).split()) for line in lines):
        return "other_language_or_locale", []
    usable = []
    candidates = [candidate for line in lines for candidate in (line, *line.get("alternatives", ()))]
    lexicon = _UI_WORDS | vocabulary

    def rank(row):
        words = _vote_key(row["text"]).split()
        supported = sum(word in lexicon or word.isdigit() for word in words) / max(1, len(words))
        return -min(2, len(row["passes"])), -supported, -len(words), -row["confidence"], row["box"]

    for line in sorted(candidates, key=rank):
        tokens = text_key(line["text"]).split()
        words = set(tokens)
        collapsed = "".join(tokens)
        if len(tokens) > 1 and collapsed in (_UI_WORDS | vocabulary) and tokens[0] not in _UI_WORDS:
            line = dict(line, text=collapsed.upper() if line["text"].isupper() else collapsed)
            words = {collapsed}
        if not any(re.fullmatch(r"[a-z]{2,}", s) for s in words):
            continue
        if words & foreign:
            continue
        if line["confidence"] < 60 or not (words & (_UI_WORDS | vocabulary)):
            continue
        if any(_overlapping_line(line, kept) for kept in usable):
            continue
        usable.append(line)
    usable.sort(key=lambda row: (row["box"][1], row["box"][0]))
    if not usable:
        return "unconfirmed", []
    strong = all(row["confidence"] >= 75 and len(row["passes"]) >= 2
                 and row["competing_confidence"] < row["confidence"] + 5 for row in usable)
    if not strong:
        return "english_review", usable
    if any(row["rotation"] for row in usable):
        return "rotated_english", usable
    return ("multiline_english" if len(usable) > 1 else "english"), usable
