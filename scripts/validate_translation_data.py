#!/usr/bin/env python3
"""Validate the committed species glossary and draft translations against a local catalog."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.translation.catalog import read_jsonl, validate_species_document, validate_terms_glossary, validate_translation_rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, default=ROOT / "build/milestone-3b/source-catalog.jsonl")
    parser.add_argument("--translations", type=Path, default=ROOT / "translations/pilot.jsonl")
    parser.add_argument("--species", type=Path, default=ROOT / "glossary/pokemon_species_ru.json")
    parser.add_argument("--report", type=Path, default=ROOT / "reports/milestone-3b/asset-catalog.json")
    parser.add_argument("--terms", type=Path, default=ROOT / "glossary/terms.json")
    args = parser.parse_args()
    translations = read_jsonl(args.translations)
    ids = {row["record_id"] for row in translations}
    source = []
    for line in args.catalog.open(encoding="utf-8"):
        row = json.loads(line)
        if row["record_id"] in ids:
            source.append(row)
    glossary = json.loads(args.species.read_text(encoding="utf-8"))
    terms = json.loads(args.terms.read_text(encoding="utf-8"))
    catalog_report = json.loads(args.report.read_text(encoding="utf-8"))
    validate_species_document(glossary)
    validate_terms_glossary(terms)
    errors = validate_translation_rows(source, translations, glossary)
    if errors:
        print("\n".join(errors))
        return 1
    catalog_count = int(catalog_report["catalog_record_count"])
    print(json.dumps({"species_entries": glossary["entry_count"], "pilot_records": len(translations),
                      "source_rows_checked": len(source), "catalog_variants": catalog_count,
                      "untranslated_variants": max(0, catalog_count - len(translations)),
                      "translation_coverage_percent": round(100 * len(translations) / catalog_count, 4) if catalog_count else 0,
                      "result": "PASS"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
