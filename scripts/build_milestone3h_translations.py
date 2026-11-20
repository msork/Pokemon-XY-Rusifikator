#!/usr/bin/env python3
"""Create the review-pending Milestone 3H naming and battle UI translation set."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
CATALOG = ROOT / "build/milestone-3b/source-catalog.jsonl"
OUTPUT = ROOT / "translations/milestone3h-ui-battle.jsonl"
EXISTING_TRANSLATIONS = (ROOT / "translations/pilot.jsonl", ROOT / "translations/early-game.jsonl",
                         ROOT / "translations/milestone3g-battle.jsonl")

# Each value replaces text segments in source order; control segments are copied byte-for-byte.
TEXT = {
    "gen6:a/0/7/4:0036/00:00000": ["Твоё имя?"],
    "gen6:a/0/7/4:0036/00:00001": [" — прозвище?"],
    "gen6:a/0/7/4:0036/00:00002": ["Название ящика?"],
    "gen6:a/0/7/4:0036/00:00003": ["Что ты хочешь сообщить всем?"],
    "gen6:a/0/7/4:0036/00:00004": ["Твоё прозвище?"],
    "gen6:a/0/7/4:0036/00:00005": ["Какое короткое сообщение ты хочешь", " отправить партнёру по обмену?"],
    "gen6:a/0/7/4:0036/00:00006": ["Какого покемона ты ищешь?"],
    "gen6:a/0/7/4:0036/00:00007": ["Что ты говоришь, когда радуешься?"],
    "gen6:a/0/7/4:0036/00:00008": ["Это слово нельзя ввести."],
    "gen6:a/0/7/4:0036/00:00009": ["Можно ввести не более пяти цифр."],
    "gen6:a/0/7/4:0036/00:00010": ["Это имя нельзя использовать."],
    "gen6:a/0/7/4:0036/00:00011": ["Введи прозвище."],
    "gen6:a/0/7/4:0036/00:00012": ["Введи имя."],
    "gen6:a/0/7/4:0036/00:00013": ["Удалить"],
    "gen6:a/0/7/4:0036/00:00014": ["Да"],
    "gen6:a/0/7/4:0036/00:00015": ["Пробел"],
    "gen6:a/0/7/4:0036/00:00016": ["Удалить"],
    "gen6:a/0/7/4:0036/00:00020": ["Какого покемона ты хочешь?"],
    "gen6:a/0/7/4:0079/00:00000": ["Малыш "],
    "gen6:a/0/7/4:0079/00:00001": ["-мастер"],
    "gen6:a/0/7/4:0079/00:00002": ["Большой "],
    "gen6:a/0/7/4:0079/00:00004": ["Малыш "],
    "gen6:a/0/7/4:0079/00:00005": ["Леди "],
    "gen6:a/0/7/4:0079/00:00006": ["-чик"],
    "gen6:a/0/7/4:0079/00:00008": ["Придумай своё"],
    "gen6:a/0/7/4:0080/00:00650": ["Чеспин"],
    "gen6:a/0/7/4:0080/00:00653": ["Феннекин"],
    "gen6:a/0/7/4:0080/00:00656": ["Фроки"],
    "gen6:a/0/7/4:0095/00:00642": ["Письмо профессора", ""],
    "gen6:a/0/7/4:0096/00:00642": ["Письмо профессора"],
    "gen6:a/0/7/4:0097/00:00642": ["Письма профессора"],
    "gen6:a/0/7/4:0098/00:00642": ["Письмо профессора"],
    "gen6:a/0/7/4:0127/00:00035": ["ВОССТАНОВИТЬ ОЗ/ОС"],
    "gen6:a/0/7/4:0127/00:00036": ["ВОССТАНОВИТЬ СТАТУС"],
    "gen6:a/0/7/4:0127/00:00040": ["ОЗ/ОС", "ВОССТАНОВИТЬ"],
    "gen6:a/0/7/4:0127/00:00041": ["СТАТУС", "ВОССТАНОВИТЬ"],
    "gen6:a/0/7/4:0127/00:00043": ["ПОКЕБОЛЫ"],
    "gen6:a/0/7/4:0127/00:00044": ["БОЕВЫЕ ПРЕДМЕТЫ"],
    "gen6:a/0/7/4:0127/00:00045": ["ПОСЛЕДНИЙ ПРЕДМЕТ"],
    "gen6:a/0/7/4:0017/00:00000": ["Обычный"],
    "gen6:a/0/7/4:0017/00:00009": ["Огонь"],
    "gen6:a/0/7/4:0017/00:00010": ["Вода"],
    "gen6:a/0/7/4:0017/00:00011": ["Трава"],
    "gen6:a/0/8/2:0142/00:00001": [" получил(а)", "предмет «", "»!"],
    "gen6:a/0/7/4:0124/00:00008": ["Вас вызывает на бой", " ", "!"],
    "gen6:a/0/7/4:0125/00:00000": [" потерял сознание!"],
    "gen6:a/0/7/4:0125/00:00001": ["Дикий покемон ", " потерял сознание!"],
    "gen6:a/0/7/4:0125/00:00002": ["Покемон противника ", " потерял сознание!"],
}

for member, pairs in {
    "0013": {10: "Царапание", 33: "Удар", 39: "Хвостовая плеть", 52: "Угольки"},
    "0014": {10: "Царапание", 33: "Удар", 39: "Хвостовая плеть", 52: "Угольки"},
}.items():
    for message, text in pairs.items():
        TEXT[f"gen6:a/0/7/4:{member}/00:{message:05}"] = [text]

for message, move in ((30, "Царапание"), (99, "Удар"), (117, "Хвостовая плеть"), (156, "Угольки")):
    for variant, prefix in ((0, ""), (1, "Дикий покемон "), (2, "Покемон противника ")):
        TEXT[f"gen6:a/0/7/4:0126/00:{message + variant:05}"] = ([f"{prefix} применяет приём «{move}»!"] if variant == 0 else
                                                                   [prefix, f" применяет приём «{move}»!"])

for message in (13, 14):
    prefix = "Хорошо! Приятно познакомиться!"
    TEXT[f"gen6:a/0/8/2:0049/00:{message:05}"] = [
        prefix, "Знаешь, если мы будем звать друг друга по прозвищам,", "мы станем ближе.",
        "Можно я буду звать тебя «Леди " if message == 13 else "Можно я буду звать тебя ",
        "»?" if message == 13 else "-мастер?",
    ]
TEXT.update({
    "gen6:a/0/8/2:0049/00:00015": ["Что? Да ну!", "Да она же просто малышка ", ", это точно!"],
    "gen6:a/0/8/2:0049/00:00016": ["Что? Да ну!", "Он же совсем малыш ", ", это точно!"],
    "gen6:a/0/8/2:0049/00:00017": ["Как думаешь, Тревор?"],
    "gen6:a/0/8/2:0049/00:00018": ["Что?! Ты хочешь дать прозвище", "человеку при первой встрече?!", "Шауна, не ставь людей", "в неловкое положение.", "Ну... может, что-нибудь простенькое?", "Например, «", "-чик?"],
    "gen6:a/0/8/2:0049/00:00019": ["Что?! Ты хочешь дать прозвище", "человеку при первой встрече?!", "Шауна, не ставь людей", "в неловкое положение.", "Ну... может, что-нибудь простенькое?", "Например, «Большой ", "...»"],
    "gen6:a/0/8/2:0049/00:00020": ["Почему бы тебе не выбрать, как нам тебя звать?"],
    "gen6:a/0/8/2:0049/00:00021": ["Реши, как мы будем тебя звать."],
    "gen6:a/0/8/2:0049/00:00022": ["Хочешь, чтобы мы звали тебя ", "?"],
    "gen6:a/0/8/2:0049/00:00023": ["Отлично! ♪", "Тебе очень подходит!", "Уверена, мы станем отличными", "подругами, так что и я буду тебя так звать!"],
    "gen6:a/0/8/2:0049/00:00034": ["Хочешь дать своему", "покемону прозвище?"],
    "gen6:a/0/8/2:0049/00:00035": ["Значит, новое прозвище будет", "", "?"],
    "gen6:a/0/8/2:0049/00:00036": ["Значит, ты не будешь давать", "своему покемону прозвище? ♪"],
})


def main() -> int:
    existing_ids = set()
    for path in EXISTING_TRANSLATIONS:
        if path.exists():
            with path.open(encoding="utf-8") as stream:
                existing_ids.update(json.loads(line)["record_id"] for line in stream)
    source = {}
    with CATALOG.open(encoding="utf-8") as stream:
        for line in stream:
            row = json.loads(line)
            if row.get("record_id") in TEXT:
                source[row["record_id"]] = row
    missing = set(TEXT) - source.keys()
    if missing:
        raise ValueError(f"Source records not found: {sorted(missing)}")
    rows = []
    for record_id, text_parts in TEXT.items():
        if record_id in existing_ids:
            continue
        item = source[record_id]
        actual_text_slots = [segment for segment in item["source_segments"] if "text" in segment]
        if len(actual_text_slots) != len(text_parts):
            raise ValueError(f"Text-segment count mismatch for {record_id}: source={len(actual_text_slots)} translations={len(text_parts)}")
        translated = []
        slot = 0
        for segment in item["source_segments"]:
            if "text" in segment:
                # Empty fragments carry no game word data and are omitted;
                # this keeps the serialized translation compatible with the
                # strict builder while preserving every control event.
                if text_parts[slot]:
                    translated.append({"text": text_parts[slot]})
                slot += 1
            else:
                translated.append({"control_words": list(segment["control_words"])})
        rows.append({
            "context": "Milestone 3H naming, nickname, battle, or UI draft; exact screen binding is documented separately.",
            "record_id": record_id,
            "review_state": "draft_pending_linguistic_and_owner_runtime_review",
            "scope": "shared",
            "source_variant_sha256": item["source_variant_sha256"],
            "status": "draft",
            "translation_segments": translated,
            "version_scope": sorted({str(occurrence["dataset"]).split("/")[-1]
                                      for occurrence in item.get("occurrences", [])}),
        })
    rows.sort(key=lambda row: row["record_id"])
    OUTPUT.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n" for row in rows),
                      encoding="utf-8", newline="\n")
    print(json.dumps({"output": OUTPUT.relative_to(ROOT).as_posix(), "records": len(rows)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
