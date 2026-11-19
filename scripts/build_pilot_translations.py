#!/usr/bin/env python3
"""Create the authored, draft-only early-game pilot from a local source catalog."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.translation.catalog import read_jsonl, write_jsonl


# Each entry supplies Russian text segments in the exact order of source text segments.
DRAFTS = {
    "gen6:a/0/8/2:0055/00:00010": ["Доброе утро, ", "!", "Хорошо спалось?", "Ты отдохнул после переезда?"],
    "gen6:a/0/8/2:0055/00:00013": ["Пора тебе собираться!", "Почему бы тебе не выйти и не поздороваться с", "соседями?"],
    "gen6:a/0/8/2:0057/00:00001": ["Добро пожаловать в Ванивилл!", "Меня зовут Серена.", "Я твоя соседка."],
    "gen6:a/0/8/2:0057/00:00002": ["Добро пожаловать в Ванивилл!", "Меня зовут Калем.", "Я живу по соседству."],
    "gen6:a/0/8/2:0057/00:00003": ["А я Шауна!", "Рада знакомству!", "Угадайте что!", "Мы пришли за тобой!"],
    "gen6:a/0/8/2:0057/00:00006": ["Будем ждать тебя в соседнем городе!", "И знаешь что?!", "Мы получим... покемона!", "Скорее! Пойдём!"],
    "gen6:a/0/7/4:0075/00:00000": ["НАСТРОЙКИ"],
    "gen6:a/0/7/4:0075/00:00003": ["СКОРОСТЬ ТЕКСТА"],
    "gen6:a/0/7/4:0075/00:00004": ["МЕДЛЕННО"],
    "gen6:a/0/7/4:0075/00:00005": ["ОБЫЧНО"],
    "gen6:a/0/7/4:0075/00:00006": ["БЫСТРО"],
    "gen6:a/0/7/4:0075/00:00007": ["Можно выбрать одну из трёх скоростей прокрутки текста", "чтобы настроить, как быстро появляются сообщения."],
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, default=ROOT / "build/milestone-3b/source-catalog.jsonl")
    parser.add_argument("--output", type=Path, default=ROOT / "translations/pilot.jsonl")
    args = parser.parse_args()
    source_rows = read_jsonl(args.catalog)
    indexed = {}
    for row in source_rows:
        if row["record_id"] in DRAFTS:
            key = (row["record_id"], row["source_variant_sha256"])
            prior = indexed.get(key)
            if prior is not None and prior["source_segments"] != row["source_segments"]:
                raise ValueError(f"Source variant has inconsistent segment data: {key[0]}")
            indexed[key] = row
    translations = []
    for record_id, russian_text in DRAFTS.items():
        matches = [(key, row) for key, row in indexed.items() if key[0] == record_id]
        if len(matches) != 1:
            raise ValueError(f"Expected one source variant for pilot ID {record_id}; found {len(matches)}")
        (_, variant_hash), source = matches[0]
        text_count = sum("text" in segment for segment in source["source_segments"])
        if text_count != len(russian_text):
            raise ValueError(f"Pilot text segment count mismatch for {record_id}: expected {text_count}, got {len(russian_text)}")
        translated = iter(russian_text)
        segments = []
        for segment in source["source_segments"]:
            if "text" in segment:
                segments.append({"text": next(translated)})
            else:
                segments.append({"control_words": segment["control_words"]})
        games = {str(item["dataset"]).split("/")[0] for item in source["occurrences"]}
        scope = "shared" if games == {"pokemon-x", "pokemon-y"} else ("x" if "pokemon-x" in games else "y")
        versions = sorted({str(item["dataset"]).split("/")[-1] for item in source["occurrences"]})
        translations.append({
            "record_id": record_id,
            "source_variant_sha256": variant_hash,
            "scope": scope,
            "version_scope": versions,
            "translation_segments": segments,
            "status": "machine_draft",
            "context": "early-game dialogue" if "/8/2:" in record_id else "Options screen",
        })
    write_jsonl(args.output.resolve(), translations)
    print(f"Wrote {len(translations)} machine-draft pilot records to {args.output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
