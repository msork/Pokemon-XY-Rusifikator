"""Deterministic ETC1 block search with exact constraints on protected texels."""

from __future__ import annotations

from collections import Counter
from functools import lru_cache
from itertools import product

from src.rebuilding.bclim import ETC_MODIFIERS, _etc_colors


def _channel(value: int, modifier: int) -> int:
    return min(255, max(0, value + modifier))


@lru_cache(maxsize=512)
def _fit_subblock(samples: tuple, bits: int):
    """Rank endpoint/table pairs, keeping exact matches for locked samples."""
    expand = (lambda v: v * 17) if bits == 4 else (lambda v: (v << 3) | (v >> 2))
    histogram = Counter(samples)
    locked = [rgb for rgb, frozen in histogram if frozen]
    colors = locked or [rgb for rgb, _ in histogram]
    editable = [rgb for rgb, frozen in samples if not frozen]
    center = editable or colors
    mean = tuple(round(sum(color[c] for color in center) / len(center)) for c in range(3))
    scale = (1 << bits) - 1
    results = []
    for table, modifiers in enumerate(ETC_MODIFIERS):
        endpoints = set()
        targets = locked[:1] if locked else [mean, *colors]
        for rgb in targets:
            for diff in modifiers:
                axes = []
                for axis, component in enumerate(rgb):
                    nearest = min(scale, max(0, round((component - diff) * scale / 255)))
                    values = range(max(nearest - 1, 0), min(nearest + 1, scale) + 1)
                    if locked:
                        exact = [v for v in range(scale + 1) if _channel(expand(v), diff) == component]
                        near = sorted(exact, key=lambda v: abs(expand(v) + diff - mean[axis]))[:4]
                        values = sorted(set(near + exact[:1] + exact[-1:]))
                    axes.append(values)
                if locked:
                    # Sample broad clipped intervals at their ends and near
                    # the editable pixels' mean. Every retained value is exact.
                    endpoints.update(product(*axes))
                else:
                    endpoints.add(tuple(min(scale, max(0, round((c - diff) * scale / 255))) for c in rgb))
                    if rgb == mean:
                        endpoints.update(product(*axes))
        for endpoint in sorted(endpoints):
            palette = [tuple(_channel(expand(value), m) for value in endpoint) for m in modifiers]
            if any(rgb not in palette for rgb in locked):
                continue
            choices = {}
            error = 0
            for (rgb, frozen), count in histogram.items():
                scores = [sum((a - b) ** 2 for a, b in zip(rgb, candidate)) for candidate in palette]
                eligible = [i for i in range(4) if all(abs(a - b) <= 12 for a, b in zip(rgb, palette[i]))]
                if not eligible:
                    break
                selected = min(eligible, key=scores.__getitem__)
                choices[rgb, frozen] = selected
                error += scores[selected] * count
            else:
                selectors = tuple(choices[sample] for sample in samples)
                results.append((error, endpoint, table, selectors))
    return sorted(results)


@lru_cache(maxsize=256)
def compress_rgb_block(samples: tuple[tuple[tuple[int, int, int], bool], ...]) -> int:
    """Encode 16 column-major RGB samples, or raise if no safe candidate fits."""
    if len(samples) != 16:
        raise ValueError("ETC1 requires sixteen RGB samples")
    best = None
    for flip in (0, 1):
        split = tuple(tuple(i for i in range(16) if ((i % 4 if flip else i // 4) // 2) == half)
                      for half in (0, 1))
        for bits in (4, 5):
            fits = [_fit_subblock(tuple(samples[i] for i in side), bits) for side in split]
            if not all(fits):
                continue
            if bits == 4:
                pairs = [(fits[0][0], fits[1][0])]
            else:
                # Differential endpoints must differ by -4..3. Bound this
                # search and reject when no compatible pair is found.
                pairs = ((a, b) for a in fits[0][:32] for b in fits[1][:32]
                         if all(-4 <= y - x <= 3 for x, y in zip(a[1], b[1])))
            for a, b in pairs:
                error = a[0] + b[0]
                if best is not None and best[0] <= error:
                    continue
                word = (flip << 32) | (a[2] << 37) | (b[2] << 34)
                if bits == 4:
                    channels = [(x << 4) | y for x, y in zip(a[1], b[1])]
                else:
                    word |= 1 << 33
                    channels = [(x << 3) | ((y - x) & 7) for x, y in zip(a[1], b[1])]
                for shift, channel in zip((56, 48, 40), channels):
                    word |= channel << shift
                for indices, fit in zip(split, (a, b)):
                    for i, selector in zip(indices, fit[3]):
                        word |= (selector & 1) << i
                        word |= (selector >> 1) << (16 + i)
                best = (error, word)
    if best is None:
        raise ValueError("ETC1 could not fit edited RGB while preserving protected texels")
    return best[1]


def selector_only(word: int, samples: tuple) -> int | None:
    """Keep the original endpoints if every requested sample is representable."""
    colors = _etc_colors(word)
    for i, (rgb, _) in enumerate(samples):
        palette = colors[(i % 4 if word & (1 << 32) else i // 4) // 2]
        if rgb not in palette:
            return None
        previous = ((word >> i) & 1) | ((word >> (i + 15)) & 2)
        if palette[previous] != rgb:
            selector = palette.index(rgb)
            word &= ~((1 << i) | (1 << (i + 16)))
            word |= ((selector & 1) << i) | ((selector >> 1) << (i + 16))
    return word
