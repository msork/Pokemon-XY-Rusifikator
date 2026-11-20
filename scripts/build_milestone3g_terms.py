#!/usr/bin/env python3
"""Generate targeted Russian battle-label records from the verified source catalog."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "build/milestone-3b/source-catalog.jsonl"
SPECIES = ROOT / "glossary/pokemon_species_ru.json"
OUTPUT = ROOT / "translations/milestone3g-battle.jsonl"

LABELS = {
    "HP": "ОЗ", "PP": "ОС", "Lv.": "Ур.", "NEXT LV.": "ДО СЛ. УР.",
    "BAG": "СУМКА", "RUN": "БЕГ",
    "POKÉMON": "ПОКЕМОНЫ", "POKÉDEX": "ПОКЕДЕКС", "SAVE": "СОХРАНИТЬ", "OPTIONS": "НАСТРОЙКИ",
}


def main() -> int:
    species_doc = json.loads(SPECIES.read_text(encoding="utf-8"))
    species = {entry["english"]: entry["russian"] for entry in species_doc["entries"]}
    source_rows = [json.loads(line) for line in CATALOG.open(encoding="utf-8")]
    existing_ids = set()
    for path in (ROOT / "translations/pilot.jsonl", ROOT / "translations/early-game.jsonl"):
        with path.open(encoding="utf-8") as stream:
            existing_ids.update(json.loads(line)["record_id"] for line in stream)
    targets = []
    for source in source_rows:
        rid = source["record_id"]
        if not rid.startswith("gen6:a/0/7/4:"):
            continue
        if rid in existing_ids:
            continue
        source_text = source["source_text"]
        if source_text in LABELS:
            translated = LABELS[source_text]
            context = "Battle or party UI abbreviation/command; screen placement requires runtime confirmation."
        elif source_text == "Chespin":
            translated = species[source_text]
            context = "Species name from the National Pokédex keyed Russian glossary."
        else:
            continue
        targets.append({
            "context": context,
            "record_id": rid,
            "review_state": "draft_pending_owner_runtime_and_linguistic_review",
            "scope": "shared",
            "source_variant_sha256": source["source_variant_sha256"],
            "status": "draft",
            "translation_segments": [{"text": translated}],
            "version_scope": ["base", "update-1.5"],
        })
    targets.sort(key=lambda row: row["record_id"])
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in targets),
                      encoding="utf-8", newline="\n")
    print(json.dumps({"output": OUTPUT.relative_to(ROOT).as_posix(), "records": len(targets)}, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
