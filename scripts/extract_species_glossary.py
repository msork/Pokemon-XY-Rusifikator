#!/usr/bin/env python3
"""Extract National Dex #0001-0721 from a saved Bulbapedia page copy."""

from __future__ import annotations

import argparse
from html.parser import HTMLParser
import hashlib
import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_URL = "https://bulbapedia.bulbagarden.net/wiki/List_of_Russian_Pok%C3%A9mon_names"
SOURCE_REVISION_URL = "https://bulbapedia.bulbagarden.net/w/index.php?title=List_of_Russian_Pok%C3%A9mon_names&oldid=4640552"
LICENSE_URL = "https://creativecommons.org/licenses/by-nc-sa/2.5/"
RETRIEVED_DATE = "2026-11-19"
PAGE_REVISION = 4640552


class TableRows(HTMLParser):
    """Collect normalized cell text without third-party HTML dependencies."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tables: list[dict[str, object]] = []
        self._table_stack: list[dict[str, object]] = []
        self._row: list[str] | None = None
        self._cell: list[str] | None = None

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag == "table":
            table = {"class": dict(attrs).get("class", ""), "rows": []}
            self.tables.append(table)
            self._table_stack.append(table)
            return
        if tag == "tr":
            self._row = []
        elif tag in {"td", "th"} and self._row is not None:
            self._cell = []
        elif tag == "br" and self._cell is not None:
            self._cell.append(" ")

    def handle_data(self, data: str) -> None:
        if self._cell is not None:
            self._cell.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag in {"td", "th"} and self._cell is not None and self._row is not None:
            self._row.append(" ".join("".join(self._cell).split()))
            self._cell = None
        elif tag == "tr" and self._row is not None:
            if self._table_stack:
                rows = self._table_stack[-1]["rows"]
                assert isinstance(rows, list)
                rows.append(self._row)
            self._row = None
        elif tag == "table" and self._table_stack:
            self._table_stack.pop()


def extract_entries(html: str) -> list[dict[str, object]]:
    parser = TableRows()
    parser.feed(html)
    article_tables = [t for t in parser.tables if "roundtable" in str(t["class"]).split()]
    rows = [
        row for table in article_tables for row in table["rows"]
        if len(row) == 5 and row[1] == ""
    ]
    found: dict[int, dict[str, object]] = {}
    for row in rows:
        if len(row) < 5:
            continue
        match = re.fullmatch(r"#(\d{4})", row[0])
        if match is None:
            continue
        dex = int(match.group(1))
        if dex < 1 or dex > 721:
            continue
        english = unicodedata.normalize("NFC", row[2])
        russian = unicodedata.normalize("NFC", row[3])
        romanization = unicodedata.normalize("NFC", row[4])
        entry = {
            "national_dex_number": dex,
            "english": english,
            "russian": russian,
            "source_romanization": romanization,
            "name_status": "established_official_per_source",
            "alternatives": [],
        }
        found[dex] = entry
    expected = set(range(1, 722))
    missing = sorted(expected - found.keys())
    extra = sorted(found.keys() - expected)
    if missing or extra:
        raise ValueError(f"Species coverage is incomplete: missing={missing[:10]}, extra={extra[:10]}")
    entries = [found[dex] for dex in range(1, 722)]
    by_dex = {int(entry["national_dex_number"]): entry for entry in entries}
    alternatives = []
    historical_sources = {
        9: ("official_pokemon_handbook", "Russian edition of The Official Pokémon Handbook (ISBN 5-85044-638-9)"),
        10: ("previous_official_pokedex_and_champions_handbook_ii", "Previous official Pokédex and Pokémon Champion's Handbook II (ISBN 978-5-85044-639-0)"),
    }
    for table_index, table in enumerate(article_tables):
        if table_index not in historical_sources:
            continue
        source_id, source_note = historical_sources[table_index]
        for row in table["rows"]:
            if len(row) != 6 or not row[1]:
                continue
            match = re.fullmatch(r"#(\d{4})", row[0])
            if match is None:
                continue
            dex = int(match.group(1))
            if dex not in by_dex:
                continue
            old_name = unicodedata.normalize("NFC", row[2])
            old_romanization = unicodedata.normalize("NFC", row[3])
            current_name = unicodedata.normalize("NFC", row[4])
            if current_name != by_dex[dex]["russian"]:
                raise ValueError(f"Trivia current-name column disagrees at #{dex:04d}")
            alternatives.append({
                "national_dex_number": dex,
                "russian": old_name,
                "source_romanization": old_romanization,
                "status": "historical_alternative",
                "historical_source_id": source_id,
                "historical_source_note": source_note,
                "usage": "Historical spelling reported by Bulbapedia; not the current standard name.",
            })
    alt_by_dex: dict[int, list[dict[str, object]]] = {}
    for alternative in alternatives:
        alt_by_dex.setdefault(int(alternative["national_dex_number"]), []).append(alternative)
    for entry in entries:
        entry["alternatives"] = alt_by_dex.get(int(entry["national_dex_number"]), [])
    for entry in entries:
        if not entry["english"] or not entry["russian"]:
            raise ValueError(f"Missing English or Russian name at #{entry['national_dex_number']:04d}")
        for field in ("english", "russian"):
            value = str(entry[field])
            if unicodedata.normalize("NFC", value) != value:
                raise ValueError(f"Non-NFC {field} at #{entry['national_dex_number']:04d}")
    english_keys = [str(entry["english"]).casefold() for entry in entries]
    if len(english_keys) != len(set(english_keys)):
        raise ValueError("English species-name lookup is not unique")
    russian_keys = [str(entry["russian"]).casefold() for entry in entries]
    if len(russian_keys) != len(set(russian_keys)):
        raise ValueError("Russian species spellings are not unique in the source list")
    dex_numbers = [int(entry["national_dex_number"]) for entry in entries]
    if dex_numbers != list(range(1, 722)):
        raise ValueError("National Pokédex identifiers are not a unique contiguous 1-721 range")
    return entries


def build_document(source_html: Path) -> dict[str, object]:
    source_html = source_html.resolve(strict=True)
    raw = source_html.read_bytes()
    entries = extract_entries(raw.decode("utf-8"))
    return {
        "schema_version": 1,
        "dataset": "Bulbapedia Russian Pokémon species names, National Pokédex 0001-0721",
        "source_url": SOURCE_URL,
        "source_revision_url": SOURCE_REVISION_URL,
        "source_revision_id": PAGE_REVISION,
        "retrieved_date": RETRIEVED_DATE,
        "source_sha256": hashlib.sha256(raw).hexdigest(),
        "attribution": "Bulbapedia contributors, List of Russian Pokémon names, revision 4640552",
        "source_license": "Creative Commons Attribution-NonCommercial-ShareAlike 2.5 Generic",
        "source_license_url": LICENSE_URL,
        "interpretation": (
            "The source describes its Cyrillic column as the official Russian spellings. "
            "Its separate BGN/PCGN romanization column is retained as reference metadata, "
            "not treated as an alternative Russian name. No names were invented."
        ),
        "entry_count": len(entries),
        "national_dex_range": [1, 721],
        "historical_alternative_count": sum(len(entry["alternatives"]) for entry in entries),
        "historical_source_counts": {
            "official_pokemon_handbook": sum(1 for entry in entries for alt in entry["alternatives"] if alt["historical_source_id"] == "official_pokemon_handbook"),
            "previous_official_pokedex_and_champions_handbook_ii": sum(1 for entry in entries for alt in entry["alternatives"] if alt["historical_source_id"] == "previous_official_pokedex_and_champions_handbook_ii"),
        },
        "missing_translation_numbers": [],
        "entries": entries,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "source_html", nargs="?",
        type=Path,
        default=ROOT / "build/milestone-3b/sources/bulbapedia-russian-pokemon-names.html",
        help="saved page source (kept under ignored build/)",
    )
    parser.add_argument(
        "--output", type=Path, default=ROOT / "glossary/pokemon_species_ru.json",
        help="structured glossary JSON output",
    )
    args = parser.parse_args()
    document = build_document(args.source_html)
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({
        "output": output.as_posix(),
        "entries": document["entry_count"],
        "source_sha256": document["source_sha256"],
        "first": document["entries"][0],
        "last": document["entries"][-1],
    }, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
