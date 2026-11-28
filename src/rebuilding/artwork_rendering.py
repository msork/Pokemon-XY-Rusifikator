"""Evidence-based lettering masks and style fitting for offline artwork review."""

from __future__ import annotations

from collections import Counter
from functools import lru_cache
from pathlib import Path
from statistics import median

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

from src.rebuilding.artwork_localization import ReviewRequired, _ROTATIONS, _unrotate_box


def _density(mask: Image.Image) -> float:
    box = mask.getbbox()
    if box is None:
        return 0.0
    return sum(value > 127 for value in mask.crop(box).get_flattened_data()) / ((box[2] - box[0]) * (box[3] - box[1]))


def reference_style(original: Image.Image, edited: Image.Image) -> dict:
    if original.mode != "RGBA" or edited.mode != "RGBA" or original.size != edited.size:
        raise ValueError("Style reference dimensions or mode changed")
    mask = ImageChops.difference(original, edited).convert("RGB")
    channels = mask.split()
    changed = ImageChops.lighter(ImageChops.lighter(*channels[:2]), channels[2])
    changed = ImageChops.lighter(changed, ImageChops.difference(original.getchannel("A"), edited.getchannel("A")))
    changed = changed.point([0] + [255] * 255)
    box = changed.getbbox()
    return {"edit_box": box, "density": round(_density(changed), 4),
            "ink_height": box[3] - box[1] if box else 0,
            "ink_aspect": (box[2] - box[0]) / (box[3] - box[1]) if box else 0,
            "template": _template(changed.crop(box)) if box else []}


@lru_cache(maxsize=192)
def _font(path: Path, size: int):
    return ImageFont.truetype(str(path), size)


def _glyphs(text: str, path: Path, size: int, tracking: int) -> Image.Image:
    font = _font(path, size)
    mask = Image.new("L", (max(16, int(font.getlength(text)) + len(text) * abs(tracking) + size * 2),
                           size * 3))
    draw = ImageDraw.Draw(mask)
    if tracking == 0:
        draw.text((size, size // 3), text, font=font, fill=255)
    else:
        x = size
        for glyph in text:
            draw.text((x, size // 3), glyph, font=font, fill=255)
            x += font.getlength(glyph) + tracking
    bounds = mask.getbbox()
    if bounds is None:
        raise ReviewRequired("The selected font produced no visible lettering")
    return mask.crop(bounds)


def _shape_similarity(a: Image.Image, b: Image.Image) -> float:
    a = a.resize((48, 16), Image.Resampling.BOX)
    b = b.resize((48, 16), Image.Resampling.BOX)
    error = sum(abs(x - y) for x, y in zip(a.get_flattened_data(), b.get_flattened_data()))
    return 1 - error / (48 * 16 * 255)


def _slant(mask: Image.Image) -> float:
    """Estimate stroke lean from horizontal ink centroids across central rows."""
    frame = mask.resize((64, 24), Image.Resampling.BOX)
    samples = frame.get_flattened_data()

    def centroid(top, bottom):
        weights = [sum(samples[y * 64 + x] for y in range(top, bottom)) for x in range(64)]
        total = sum(weights)
        return sum(x * value for x, value in enumerate(weights)) / total if total else 31.5

    return (centroid(5, 10) - centroid(14, 19)) / 64


def _template(mask: Image.Image) -> list[int]:
    """Small native-ink registration template, without copying reference art."""
    return list(mask.resize((24, 10), Image.Resampling.BOX).get_flattened_data())


def match_references(ink: Image.Image, references: list[dict]) -> list[tuple[float, dict]]:
    target = _template(ink)
    aspect = ink.width / ink.height
    matches = []
    for reference in references:
        values = reference.get("template")
        if not values:
            continue
        native_height = reference["ink_height"] / ink.height
        if not 0.58 <= native_height <= 1.7:
            continue
        similarity = 1 - sum(abs(a - b) for a, b in zip(target, values)) / (len(target) * 255)
        ratio = reference["ink_aspect"] / aspect
        score = 0.65 * similarity + 0.2 * min(ratio, 1 / ratio) + 0.15 * min(native_height, 1 / native_height)
        if score >= 0.55:
            matches.append((score, reference))
    return sorted(matches, key=lambda pair: (-pair[0], pair[1].get("name", "")))[:3]


def _choose_lettering(ink: Image.Image, original: str, russian: str, fonts: list[Path],
                      target: tuple[int, int], references: list[dict]) -> tuple[Image.Image, dict]:
    width, height = target
    if height < 7:
        raise ReviewRequired("Native lettering area is below seven pixels")
    matches = match_references(ink, references)
    own_density = _density(ink)
    density = (own_density + median(ref["density"] for _, ref in matches)) / 2 if matches else own_density
    best = None
    source_slant = _slant(ink)
    for font in fonts:
        for tracking in (-1, 0, 1):
            latin = _glyphs(original, font, max(8, round(height * 1.25)), tracking)
            aspect = min(latin.width / latin.height, ink.width / ink.height) / max(
                latin.width / latin.height, ink.width / ink.height)
            slant_fit = max(0, 1 - 6 * abs(_slant(latin) - source_slant))
            match = 0.65 * _shape_similarity(ink, latin) + 0.18 * aspect + 0.17 * slant_fit
            for size in range(max(9, 2 * height), 6, -1):
                mask = _glyphs(russian, font, size, tracking)
                width_scale = min(1.0, width / mask.width)
                if width_scale >= 0.88 and mask.height <= height:
                    if width_scale < 1:
                        mask = mask.resize((width, mask.height), Image.Resampling.LANCZOS)
                    legibility = mask.height / height
                    glyph_density = 1 - abs(_density(mask) - density)
                    score = 0.48 * match + 0.32 * legibility + 0.20 * glyph_density - 0.12 * (1 - width_scale)
                    if best is None or score > best[0]:
                        best = (score, mask, font.name, tracking, match, legibility, glyph_density, slant_fit, width_scale)
                    break
    if best is None or best[5] < 0.66 or best[1].height < 7:
        raise ReviewRequired("Cyrillic lettering would lose too much height")
    score, mask, font, tracking, match, height_fit, density_fit, slant_fit, width_scale = best
    return mask, {"font": font, "tracking": tracking, "shape_match": round(match, 3),
                  "height_fit": round(height_fit, 3), "density_match": round(density_fit, 3),
                  "slant_match": round(slant_fit, 3),
                  "visual_score": round(score, 3), "width_scale": round(width_scale, 3),
                  "matched_references": [{"name": ref.get("name"), "similarity": round(value, 3)}
                                         for value, ref in matches]}


def _equal_background(pixel, bg) -> bool:
    return pixel == bg or pixel[3] == bg[3] == 0


def _inspect_lettering(crop: Image.Image, expected: tuple[int, int, int, int]):
    width, height = crop.size
    source = crop.get_flattened_data()
    background = []
    mask = Image.new("L", crop.size)
    mask_pixels = []
    models = set()
    for y in range(height):
        row = source[y * width:(y + 1) * width]
        left, right = row[0], row[-1]
        if left[3] == right[3] == 0 and row[1][3] == row[-2][3] == 0:
            predicted = [left] * width
            models.add("transparent")
        elif left[3] == right[3] and all(pixel[3] == left[3] for pixel in row):
            predicted = [tuple(round(a + (b - a) * x / (width - 1)) for a, b in zip(left, right))
                         for x in range(width)]
            edge = (1, 2, -3, -2) if left != right and width >= 7 else (1, -2)
            if any(row[x] != predicted[x] for x in edge):
                raise ReviewRequired("Background gradient does not match the observed edge samples")
            models.add("row-sampled" if left == right else "linear-gradient")
        else:
            raise ReviewRequired("Text crosses artwork or the backing alpha cannot be recovered")
        background.extend(predicted)
        mask_pixels.extend(0 if _equal_background(pixel, bg) else 255 for pixel, bg in zip(row, predicted))
    if "transparent" in models and len(models) != 1:
        raise ReviewRequired("Detected artwork intersects a transparency boundary")
    mask.putdata(mask_pixels)
    bounds = mask.getbbox()
    if bounds is None or any(abs(x - y) > 3 for x, y in zip(bounds, expected)):
        raise ReviewRequired("Recovered lettering mask disagrees with OCR bounds")
    if bounds[1] == 0 or bounds[3] == height or _density(mask) > 0.88:
        raise ReviewRequired("Lettering mask reaches an artwork boundary or is too dense")
    model = "linear-gradient" if "linear-gradient" in models else next(iter(models))
    if model == "linear-gradient" and _density(mask) > 0.65:
        raise ReviewRequired("Gradient model has too little unchanged support between glyphs")
    return source, background, mask, bounds, model


def _common_rgb(colors: list[tuple]) -> tuple[int, int, int]:
    return Counter(color[:3] for color in colors).most_common(1)[0][0]


def _representative_face(samples: list[tuple]) -> tuple[int, int, int]:
    # Select the brighter portion of the inner stroke so a dark border
    # does not become the fill on thin or antialiased letters.
    visible = sorted(samples, key=lambda color: sum(color[:3]))
    return _common_rgb(visible[len(visible) * 2 // 3:])


def _palette_coverage(source, revised, old_mask, new_mask) -> float:
    def histogram(pixels, mask):
        counts = Counter()
        for pixel, active in zip(pixels, mask):
            if active and pixel[3] >= 51:
                counts[tuple(channel // 32 for channel in pixel[:3])] += pixel[3]
        return counts

    before = histogram(source, old_mask)
    after = histogram(revised, new_mask)
    covered = 0
    for color, count in before.items():
        if any(max(abs(a - b) for a, b in zip(color, other)) <= 1 for other in after):
            covered += count
    return covered / sum(before.values()) if before else 0.0


def _effects(source, ink: Image.Image, bounds):
    w, h = ink.size
    inside = ink.filter(ImageFilter.MinFilter(3))
    internal = inside.get_flattened_data()
    ink_pixels = ink.get_flattened_data()
    edge = [p for i, p in enumerate(source) if p[3] and ink_pixels[i] and not internal[i]]
    core = [p for i, p in enumerate(source) if internal[i] and p[3]]
    visible = core or [p for i, p in enumerate(source) if p[3] and ink_pixels[i]]
    fill = _representative_face(visible)
    border = _common_rgb(edge) if edge else fill
    color_gap = sum(abs(a - b) for a, b in zip(fill, border))
    outline = border if core and color_gap >= 64 and sum(p[:3] == border for p in edge) >= 0.22 * len(edge) else None
    row_colors = []
    for y in range(bounds[1], bounds[3]):
        samples = [source[i] for i in range(y * w, (y + 1) * w) if internal[i] and source[i][3]]
        row_colors.append(_representative_face(samples) if samples else None)
    available = [i for i, color in enumerate(row_colors) if color is not None]
    if len(available) >= 3:
        sampled = [row_colors[min(available, key=lambda row: abs(row - y))] for y in range(len(row_colors))]
        gradient = [tuple(round(median(color[channel] for color in sampled[max(0, y - 1):y + 2]))
                          for channel in range(3)) for y in range(len(row_colors))]
    else:
        gradient = [fill] * (bounds[3] - bounds[1])
    shadow = None
    if outline:
        shades = Counter(p[:3] for p in edge if p[:3] not in (fill, outline))
        footprint = {(i % w, i // w) for i, value in enumerate(ink_pixels) if value}
        for shade, count in shades.most_common(3):
            locations = {(i % w, i // w) for i, pixel in enumerate(source)
                         if ink_pixels[i] and pixel[:3] == shade}
            if count < 4 or not locations:
                continue
            front = footprint - locations

            def agreement(offset):
                dx, dy = offset
                displaced = {(x + dx, y + dy) for x, y in front
                             if 0 <= x + dx < w and 0 <= y + dy < h} - front
                return len(displaced & locations) / len(displaced | locations)

            offsets = [(dx, dy) for dx in range(-3, 4) for dy in range(0, 4) if dx or dy]
            offset = max(offsets, key=agreement)
            if agreement(offset) >= 0.65:
                shadow = (offset, shade)
                break
    return inside, gradient, outline, shadow


def _matched_opacity(coverage, old_alpha, floor: int) -> dict[int, int]:
    """Map mask intensity ranks onto measured, representable source alpha levels."""
    layers = Counter(value for value in coverage if value >= floor)
    source = sorted(value for value in old_alpha if value)
    if not layers or not source:
        return {}
    total = sum(layers.values())
    seen = 0
    values = {}
    for intensity, count in sorted(layers.items()):
        rank = ((2 * seen + count) * len(source)) // (2 * total)
        values[intensity] = source[min(rank, len(source) - 1)]
        seen += count
    return values


def _sprite_opacity(glyph, rim, drop, source, ink_values, bounds):
    footprint = ImageChops.lighter(ImageChops.lighter(glyph, rim), drop)
    active_alpha = [pixel[3] for pixel, active in zip(source, ink_values) if active and pixel[3]]
    weak = [pixel for pixel, active in zip(source, ink_values) if active and 0 < pixel[3] < 136]
    # Use the native profile only when the source has a measured soft fringe.
    if not weak or len(weak) < len(active_alpha) * 0.12 or len(set(active_alpha)) <= 2:
        return None, None, None
    blur = footprint.filter(ImageFilter.GaussianBlur(0.9 if len(weak) < len(active_alpha) / 3 else 1.2))
    width = glyph.width
    combined = bytes(max(core, soft // 2) if bounds[0] <= i % width < bounds[2]
                     and bounds[1] <= i // width < bounds[3] else 0
                     for i, (core, soft) in enumerate(zip(footprint.get_flattened_data(),
                                                          blur.get_flattened_data())))
    opacity = _matched_opacity(combined, active_alpha, 20)
    tint = _common_rgb(weak)
    return combined, opacity, tint


def _detached_ink(alpha: Image.Image, box, silhouette) -> bool:
    if silhouette is None:
        return False
    w, h = alpha.size
    if min(w, h) < 3:
        return False
    pixels = alpha.get_flattened_data()
    corners = (pixels[0], pixels[w - 1], pixels[-w], pixels[-1])
    if any(corners):
        return False
    top = pixels[:w]
    bottom = pixels[-w:]
    sides = [pixels[y * w + x] for y in range(1, h - 1) for x in (0, w - 1)]
    edge_clear = sum(value == 0 for value in (*top, *bottom, *sides)) / (2 * (w + h) - 4)
    l, t, r, b = box
    a, c, d, e = silhouette
    if edge_clear < 0.6 or not all(-2 <= distance <= max(9, (b - t) // 4)
                                  for distance in (l - a, t - c, d - r, e - b)):
        return False
    # Every connected alpha island must touch the OCR text box. In particular,
    # a decorative dot outside the recognized lettering is not erased.
    remaining = {i for i, opacity in enumerate(pixels) if opacity}
    while remaining:
        stack = [remaining.pop()]
        overlaps = False
        while stack:
            index = stack.pop()
            y, x = divmod(index, w)
            overlaps |= l <= x < r and t <= y < b
            for ny in range(max(0, y - 1), min(h, y + 2)):
                for nx in range(max(0, x - 1), min(w, x + 2)):
                    neighbor = ny * w + nx
                    if neighbor in remaining:
                        remaining.remove(neighbor)
                        stack.append(neighbor)
        if not overlaps:
            return False
    return True


def _paint_line(image: Image.Image, box: list[int], english: str, russian: str,
                fonts: list[Path], references: list[dict], fmt: int):
    w, h = image.size
    left, top, right, bottom = box
    alpha = image.getchannel("A")
    silhouette = alpha.getbbox()
    if _detached_ink(alpha, box, silhouette):
        left, top, right, bottom = silhouette
        outer = (left - 5, top - 4, right + 5, bottom + 4)
    else:
        outer = (max(0, left - 5), max(0, top - 4), min(w, right + 5), min(h, bottom + 4))
    crop = image.crop(outer)
    expected = (left - outer[0], top - outer[1], right - outer[0], bottom - outer[1])
    if min(crop.size) < 5:
        raise ReviewRequired("Text crop is too small")
    source, background, ink, bounds, background_model = _inspect_lettering(crop, expected)
    inside, gradient, outline, shadow = _effects(source, ink, bounds)
    bw, bh = bounds[2] - bounds[0], bounds[3] - bounds[1]
    guard = int(outline is not None)
    dx, dy = shadow[0] if shadow else (0, 0)
    available = (bw - 2 * guard - abs(dx), bh - 2 * guard - dy)
    mask, profile = _choose_lettering((inside if inside.getbbox() else ink).crop(bounds), english,
                                       russian, fonts, available, references)
    # Keep the source centre for centred labels and the nearer canvas edge for
    # left/right-aligned UI labels.
    source_center = outer[0] + (bounds[0] + bounds[2]) / 2
    if source_center < w * 0.34:
        alignment, margin = "left", 0
    elif source_center > w * 0.66:
        alignment, margin = "right", available[0] - mask.width
    else:
        alignment, margin = "center", (available[0] - mask.width) // 2
    start_x = bounds[0] + guard + max(0, -dx) + margin
    start_y = bounds[1] + guard + (available[1] - mask.height) // 2
    glyph = Image.new("L", crop.size)
    glyph.paste(mask, (start_x, start_y))
    rim = glyph.filter(ImageFilter.MaxFilter(3)) if outline else Image.new("L", crop.size)
    drop = Image.new("L", crop.size)
    if shadow:
        drop.paste(rim, (dx, dy))
    ink_values = ink.get_flattened_data()
    glyph_values = glyph.get_flattened_data()
    rim_values = rim.get_flattened_data()
    drop_values = drop.get_flattened_data()
    alpha_levels = sorted({0, *(p[3] for i, p in enumerate(source) if ink_values[i])})
    visible_alpha = max(alpha_levels)
    sprite = background_model == "transparent"
    soft, opacity, glow_color = _sprite_opacity(glyph, rim, drop, source, ink_values, bounds) if sprite else (None, None, None)
    crop_result = []
    edits = []
    for i, old in enumerate(source):
        y = i // crop.width
        color = background[i] if ink_values[i] else old
        if sprite and ink_values[i]:
            color = old[:3] + (0,)
        level = glyph_values[i]
        layers = []
        if soft is not None and soft[i]:
            layers.append((glow_color, soft[i]))
        if drop_values[i]:
            layers.append((shadow[1], drop_values[i]))
        if rim_values[i]:
            layers.append((outline, rim_values[i]))
        if level:
            row = min(len(gradient) - 1, max(0, (y - start_y) * len(gradient) // mask.height))
            layers.append((gradient[row], level))
        for rgb, coverage in layers:
            if sprite:
                if opacity is not None:
                    value = opacity.get(soft[i], 0)
                else:
                    value = min(alpha_levels, key=lambda level: abs(level - visible_alpha * coverage / 255))
                if value >= color[3] and value:
                    color = (*rgb, value)
            else:
                color = tuple(round(a + (b - a) * coverage / 255) for a, b in zip(color[:3], rgb)) + (old[3],)
        if fmt in (8, 11) and color != old:
            if fmt == 8:
                color = tuple(round(channel / 17) * 17 for channel in color)
            else:
                color = color[:3] + (round(color[3] / 17) * 17,)
        crop_result.append(color)
        edits.append(255 if color != old else 0)
    crop.putdata(crop_result)
    edit = Image.new("L", crop.size)
    edit.putdata(edits)
    painted = ([value >= 20 for value in soft] if soft is not None
               else [bool(a or b or c) for a, b, c in zip(glyph_values, rim_values, drop_values)])
    profile["palette_coverage"] = round(_palette_coverage(source, crop_result, ink_values, painted), 3)
    profile["width_fit"] = round((mask.width + 2 * guard + abs(dx)) / bw, 3)
    if sprite:
        def soft_share(samples, active):
            alpha = [pixel[3] for pixel, allowed in zip(samples, active) if allowed and pixel[3]]
            return sum(value < 170 for value in alpha) / len(alpha) if alpha else 0

        profile["soft_alpha_drift"] = round(abs(soft_share(source, ink_values) - soft_share(crop_result, painted)), 3)
    else:
        profile["soft_alpha_drift"] = 0.0
    profile.update(background=background_model, gradient=len(set(gradient)) > 1,
                   outline=bool(outline), shadow=bool(shadow), glow=soft is not None, alignment=alignment,
                   region=[outer[0] + v if i % 2 == 0 else outer[1] + v for i, v in enumerate(bounds)])
    return crop, edit, outer[:2], profile


def render_enhanced(image: Image.Image, lines: list[dict], fonts: list[Path], references: list[dict], fmt: int):
    result = image.copy()
    mask = Image.new("L", image.size)
    profiles = []
    for line in lines:
        rotation = line["rotation"]
        work = image.transpose(_ROTATIONS[rotation]) if rotation else image
        box = _unrotate_box(line["box"], *work.size, (360 - rotation) % 360)
        crop, edit, offset, profile = _paint_line(work, box, line["text"], line["russian"], fonts, references, fmt)
        overlay = work.copy()
        overlay.paste(crop, offset)
        layer = Image.new("L", work.size)
        layer.paste(edit, offset)
        if rotation:
            inverse = _ROTATIONS[(360 - rotation) % 360]
            overlay, layer = (part.transpose(inverse) for part in (overlay, layer))
        if ImageChops.multiply(mask, layer).getbbox():
            raise ReviewRequired("Recovered lettering masks overlap")
        result.paste(overlay, mask=layer)
        mask = ImageChops.lighter(mask, layer)
        profile["region"] = _unrotate_box(profile["region"], *image.size, rotation)
        profiles.append(profile)
    return result, mask, profiles
