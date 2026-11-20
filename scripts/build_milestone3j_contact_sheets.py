#!/usr/bin/env python3
"""Create unchanged English and Russian-reference SVG sheets for the canonical 24 textures."""
from __future__ import annotations

import base64
import hashlib
import html
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.build_milestone3i_textures import EDITING, validate_editing_workspace

OUTPUT = ROOT / "build/milestone-3j/artwork-reference"
TYPE_LABELS = {
    "type_icon_00_normal.bclim": ("NORMAL", "Обычный"),
    "type_icon_01_kakutou.bclim": ("FIGHTING", "Боевой"),
    "type_icon_02_hikou.bclim": ("FLYING", "Летающий"),
    "type_icon_03_doku.bclim": ("POISON", "Ядовитый"),
    "type_icon_04_jimen.bclim": ("GROUND", "Земляной"),
    "type_icon_05_iwa.bclim": ("ROCK", "Каменный"),
    "type_icon_06_mushi.bclim": ("BUG", "Насекомый"),
    "type_icon_07_ghost.bclim": ("GHOST", "Призрачный"),
    "type_icon_08_hagane.bclim": ("STEEL", "Стальной"),
    "type_icon_09_honoo.bclim": ("FIRE", "Огненный"),
    "type_icon_10_mizu.bclim": ("WATER", "Водный"),
    "type_icon_11_kusa.bclim": ("GRASS", "Травяной"),
    "type_icon_12_denki.bclim": ("ELECTRIC", "Электрический"),
    "type_icon_13_esper.bclim": ("PSYCHIC", "Психический"),
    "type_icon_14_koori.bclim": ("ICE", "Ледяной"),
    "type_icon_15_dragon.bclim": ("DRAGON", "Драконий"),
    "type_icon_16_aku.bclim": ("DARK", "Тёмный"),
    "type_icon_17_yousei.bclim": ("FAIRY", "Волшебный"),
}
LABELS = {
    "fight_text.bclim": ("FIGHT", "БОЙ"),
    "bag_button.bclim": ("BAG", "СУМКА"),
    "pokemon_button.bclim": ("POKÉMON", "ПОКЕМОНЫ"),
    "run_button.bclim": ("RUN", "ПОБЕГ"),
    "ally_gauge.bclim": ("HP / Lv.", "ОЗ / Ур."),
    "enemy_gauge.bclim": ("HP / Lv.", "ОЗ / Ур."),
    **TYPE_LABELS,
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def render_sheet(manifest: dict[str, object], *, language: str) -> bytes:
    rows = manifest["assets"]
    width, cell_width, cell_height, columns = 1260, 420, 160, 3
    header = 92
    total_height = header + ((len(rows) + columns - 1) // columns) * cell_height + 20
    russian = language == "ru"
    title = "Russian Label Reference — Source PNGs Unchanged" if russian else "English Battle UI Texture Contact Sheet"
    subtitle = ("Label text is a translation specification, not edited artwork." if russian
                else "English labels are shown for mapping; source artwork is unchanged.")
    pieces = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{total_height}" viewBox="0 0 {width} {total_height}">',
              '<rect width="100%" height="100%" fill="#f3f5f8"/>',
              '<style>text{font-family:Segoe UI,Arial,sans-serif;fill:#17212b}.title{font-size:25px;font-weight:700}.sub{font-size:14px;fill:#566474}.label{font-size:20px;font-weight:700}.meta{font-size:12px;fill:#536170}.thumb{fill:#fff;stroke:#8996a5;stroke-width:1}</style>',
              f'<text x="24" y="36" class="title">{html.escape(title)}</text>',
              f'<text x="24" y="62" class="sub">{html.escape(subtitle)}</text>']
    for index, item in enumerate(rows):
        filename = str(item["internal_filename"])
        english, russian_label = LABELS[filename]
        localized = russian_label if russian else english
        x = 12 + (index % columns) * cell_width
        y = header + (index // columns) * cell_height
        png_path = EDITING / str(item["png"])
        png = png_path.read_bytes()
        data_uri = "data:image/png;base64," + base64.b64encode(png).decode("ascii")
        image_w, image_h = int(item["width"]), int(item["height"])
        max_w, max_h = 180, 82
        scale = min(max_w / image_w, max_h / image_h)
        draw_w, draw_h = image_w * scale, image_h * scale
        image_x, image_y = x + 12 + (max_w - draw_w) / 2, y + 12 + (max_h - draw_h) / 2
        resource = html.escape(f"{item['resource']}:{item['member']}")
        internal = html.escape(filename)
        pieces.extend([
            f'<rect x="{x}" y="{y}" width="{cell_width - 12}" height="{cell_height - 8}" rx="8" fill="#fff" stroke="#c7d0da"/>',
            f'<rect x="{x + 12}" y="{y + 12}" width="{max_w}" height="{max_h}" rx="4" class="thumb"/>',
            f'<image href="{data_uri}" x="{image_x:.2f}" y="{image_y:.2f}" width="{draw_w:.2f}" height="{draw_h:.2f}" preserveAspectRatio="xMidYMid meet"/>',
            f'<text x="{x + 210}" y="{y + 38}" class="label">{html.escape(localized)}</text>',
            f'<text x="{x + 210}" y="{y + 63}" class="meta">{internal}</text>',
            f'<text x="{x + 210}" y="{y + 84}" class="meta">{resource} · {image_w} × {image_h} · BCLIM {item["bclim_format"]}</text>',
            f'<text x="{x + 210}" y="{y + 104}" class="meta">Order {item["pack_order"]} · PNG SHA-256 {sha256(png)[:16]}…</text>',
        ])
    pieces.append("</svg>")
    return "\n".join(pieces).encode("utf-8")


def build() -> dict[str, object]:
    validation = validate_editing_workspace(EDITING)
    manifest = json.loads((EDITING / "manifest.json").read_text(encoding="utf-8"))
    OUTPUT.mkdir(parents=True, exist_ok=True)
    outputs = []
    for language, filename in (("en", "contact-sheet-english.svg"), ("ru", "contact-sheet-russian-reference.svg")):
        data = render_sheet(manifest, language=language)
        target = OUTPUT / filename
        target.write_bytes(data)
        outputs.append({"language": language, "path": target.relative_to(ROOT).as_posix(), "sha256": sha256(data)})
    summary = {"milestone": "3J", "canonical_assets_validated": validation["assets_validated"],
               "canonical_manifest_sha256": sha256((EDITING / "manifest.json").read_bytes()),
               "artwork_changed": False, "sheets": outputs}
    (OUTPUT / "manifest.json").write_text(json.dumps(summary, sort_keys=True, indent=2) + "\n",
                                           encoding="utf-8", newline="\n")
    return summary


def main() -> int:
    print(json.dumps(build(), ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
