#!/usr/bin/env python3
"""Export unchanged native and nearest-neighbor references for the original FIGHT texture."""
from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
SOURCE = ROOT / "build/milestone-3i/editing/fight_text.bclim.png"
OUTPUT = ROOT / "build/milestone-3l/artwork-review"
NATIVE = OUTPUT / "fight_text-original-80x50.png"
ENLARGED = OUTPUT / "fight_text-nearest-8x-640x400.png"
SHEET = OUTPUT / "original-fight-style-reference.svg"

from scripts.extract_milestone3h_textures import write_png
from src.rebuilding.textures import read_png_rgba


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def nearest_neighbor(rgba: bytes, width: int, height: int, scale: int) -> bytes:
    result = bytearray(width * height * scale * scale * 4)
    out_width = width * scale
    for y in range(height):
        row = rgba[y * width * 4:(y + 1) * width * 4]
        scaled_row = b"".join(row[x * 4:x * 4 + 4] * scale for x in range(width))
        for dy in range(scale):
            start = ((y * scale + dy) * out_width) * 4
            result[start:start + len(scaled_row)] = scaled_row
    return bytes(result)


def analyze(rgba: bytes, width: int, height: int) -> dict[str, object]:
    red_ink = []
    alpha_pixels = []
    opaque = 0
    transparent = 0
    colors: dict[tuple[int, int, int], int] = {}
    for index in range(width * height):
        x, y = index % width, index // width
        r, g, b, a = rgba[index * 4:index * 4 + 4]
        if a:
            alpha_pixels.append((x, y))
            colors[(r, g, b)] = colors.get((r, g, b), 0) + 1
            opaque += a == 255
            if r > g + 20 and r > b + 20 and g < 210:
                red_ink.append((x, y))
        else:
            transparent += 1
    bbox = lambda points: ([min(p[0] for p in points), min(p[1] for p in points),
                            max(p[0] for p in points), max(p[1] for p in points)] if points else None)
    return {"alpha_nonzero_bbox_xyxy": bbox(alpha_pixels), "red_ink_bbox_xyxy": bbox(red_ink),
            "transparent_pixel_count": transparent, "fully_opaque_pixel_count": opaque,
            "most_common_visible_rgb": [{"rgb": list(rgb), "count": count}
                                         for rgb, count in sorted(colors.items(), key=lambda pair: -pair[1])[:12]]}


def build(output: Path = OUTPUT) -> dict[str, object]:
    source_bytes = SOURCE.read_bytes()
    width, height, rgba = read_png_rgba(SOURCE)
    if (width, height) != (80, 50):
        raise ValueError(f"Expected original 80x50 texture, got {width}x{height}")
    output.mkdir(parents=True, exist_ok=True)
    native = output / NATIVE.name
    native.write_bytes(source_bytes)
    enlarged = output / ENLARGED.name
    write_png(enlarged, width * 8, height * 8, nearest_neighbor(rgba, width, height, 8))
    # Re-decode and prove every enlarged 8x8 block is exactly its original RGBA pixel.
    ew, eh, enlarged_rgba = read_png_rgba(enlarged)
    if (ew, eh) != (640, 400):
        raise ValueError("Nearest-neighbor preview dimensions are incorrect")
    for y in range(height):
        for x in range(width):
            source_pixel = rgba[(y * width + x) * 4:(y * width + x + 1) * 4]
            for dy in range(8):
                start = (((y * 8 + dy) * ew) + x * 8) * 4
                for dx in range(8):
                    if enlarged_rgba[start + dx * 4:start + dx * 4 + 4] != source_pixel:
                        raise ValueError("Preview is not an exact nearest-neighbor enlargement")

    source_uri = "data:image/png;base64," + base64.b64encode(source_bytes).decode("ascii")
    enlarged_uri = "data:image/png;base64," + base64.b64encode(enlarged.read_bytes()).decode("ascii")
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="610" viewBox="0 0 1200 610">
<defs><pattern id="checker" width="16" height="16" patternUnits="userSpaceOnUse"><rect width="16" height="16" fill="#fff"/><path d="M0 0h8v8H0zm8 8h8v8H8z" fill="#d9dee5"/></pattern></defs>
<rect width="1200" height="610" fill="#f4f6f8"/><style>text{{font-family:Segoe UI,Arial,sans-serif;fill:#17212b}}.title{{font-size:26px;font-weight:700}}.label{{font-size:17px;font-weight:700}}.meta{{font-size:14px;fill:#4e5b67}}</style>
<text x="28" y="40" class="title">Original FIGHT Texture — Reference Only</text>
<text x="28" y="68" class="meta">Source PNG is unchanged. The 8× view uses nearest-neighbor scaling; no new lettering was generated.</text>
<text x="36" y="112" class="label">Native 80 × 50 PNG</text><rect x="32" y="126" width="400" height="250" fill="url(#checker)" stroke="#67727c"/><image href="{source_uri}" x="32" y="126" width="400" height="250" image-rendering="pixelated"/>
<text x="466" y="112" class="label">Nearest-neighbor 8× — 640 × 400 PNG</text><rect x="462" y="126" width="640" height="400" fill="url(#checker)" stroke="#67727c"/><image href="{enlarged_uri}" x="462" y="126" width="640" height="400" image-rendering="pixelated"/>
<text x="32" y="424" class="meta">Original file: build/milestone-3i/editing/fight_text.bclim.png</text>
<text x="32" y="452" class="meta">Opaque ink and translucent edge/shadow pixels remain visible against checkerboard transparency.</text>
<text x="32" y="480" class="meta">Use the native PNG and this pixel view as reference before any new lettering proposal.</text>
<text x="32" y="550" class="meta">Source SHA-256: {sha256(source_bytes)}</text>
</svg>'''
    sheet = output / SHEET.name
    sheet.write_text(svg, encoding="utf-8", newline="\n")
    relative = lambda path: (path.resolve().relative_to(ROOT).as_posix()
                             if ROOT.resolve() in path.resolve().parents else path.name)
    manifest = {"milestone": "3L", "status": "original_reference_only_no_replacement_art",
                "source_path": SOURCE.relative_to(ROOT).as_posix(), "source_sha256": sha256(source_bytes),
                "native_path": relative(native), "native_sha256": sha256(native.read_bytes()),
                "native_dimensions": [width, height], "nearest_neighbor_path": relative(enlarged),
                "nearest_neighbor_sha256": sha256(enlarged.read_bytes()), "nearest_neighbor_dimensions": [ew, eh],
                "scale": 8, "interpolation": "nearest-neighbor integer replication", "pixels_verified": True,
                "visual_sheet_path": relative(sheet), "visual_sheet_sha256": sha256(sheet.read_bytes()),
                "replacement_art_created": False, "source_image_modified": False,
                "source_image_analysis": analyze(rgba, width, height)}
    (output / "manifest.json").write_text(json.dumps(manifest, sort_keys=True, indent=2) + "\n",
                                             encoding="utf-8", newline="\n")
    return manifest


if __name__ == "__main__":
    print(json.dumps(build(), sort_keys=True, indent=2))
