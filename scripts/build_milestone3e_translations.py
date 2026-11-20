#!/usr/bin/env python3
"""Build a bounded opening-sequence draft set from the ignored local source catalog."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.translation.catalog import read_jsonl, write_jsonl


# Each list corresponds in order to the source TextFile's text segments. Control
# segments are copied verbatim from the local source catalog during generation.
OPENING: dict[str, list[str]] = {
    "gen6:a/0/8/2:0049/00:00000": ["Эй, ", "!", "Сюда! Иди сюда!"],
    "gen6:a/0/8/2:0049/00:00001": ["Эй, ", "!", "Сюда! Иди сюда!"],
    "gen6:a/0/8/2:0049/00:00002": ["Мы как раз о тебе говорили!"],
    "gen6:a/0/8/2:0049/00:00003": ["Давай, садись!"],
    "gen6:a/0/8/2:0049/00:00004": ["Это место встречи, ", "."],
    "gen6:a/0/8/2:0049/00:00005": ["Позволь представить тебя всем.", "Знакомьтесь, это ", "."],
    "gen6:a/0/8/2:0049/00:00006": ["Это место встречи, ", "."],
    "gen6:a/0/8/2:0049/00:00007": ["Я вас познакомлю.", "Знакомьтесь, это ", "."],
    "gen6:a/0/8/2:0049/00:00008": ["Вот...", "Шауна описала тебя точь-в-точь!"],
    "gen6:a/0/8/2:0049/00:00009": ["Итак, ", ", это Тиерно.", "Он здорово танцует, и..."],
    "gen6:a/0/8/2:0049/00:00010": ["А это Тревор. Он ни разу не ошибается в", "ответах на тестах, но немного стесняется..."],
    "gen6:a/0/8/2:0049/00:00011": ["Итак, ", ". Это Тиерно.", "Он зажигает на танцполе..."],
    "gen6:a/0/8/2:0049/00:00012": ["А это Тревор. Он немного стеснительный, но", "в тестах всегда получает высшие баллы..."],
    "gen6:a/0/8/2:0049/00:00013": ["Вот и познакомились!", "Знаешь, прозвища помогут нам стать ближе.", "Давай будем звать друг друга по прозвищам.", "Можно я буду звать тебя леди ", "?"],
    "gen6:a/0/8/2:0049/00:00014": ["Вот и познакомились!", "Знаешь, прозвища помогут нам стать ближе.", "Давай будем звать друг друга по прозвищам.", "Можно я буду звать тебя мастером ", "?"],
    "gen6:a/0/8/2:0049/00:00015": ["Что? Да ну!", "Она точно малышка ", "!"],
    "gen6:a/0/8/2:0049/00:00016": ["Что? Да ну!", "Он точно малыш ", "!"],
    "gen6:a/0/8/2:0049/00:00017": ["Как думаешь, Тревор?"],
    "gen6:a/0/8/2:0049/00:00018": ["Что?! Ты хочешь, чтобы я дал прозвище", "человеку, которого только что встретил?!", "Шауна, не ставь людей в неловкое положение.", "Это не очень-то вежливо.", "Может... что-нибудь попроще?", "Например, ", "-кинс?"],
    "gen6:a/0/8/2:0049/00:00019": ["Что?! Ты хочешь, чтобы я дал прозвище", "человеку, которого только что встретил?!", "Шауна, не ставь людей в неловкое положение.", "Это не очень-то вежливо.", "Может... что-нибудь попроще?", "Например, Большой ", "?"],
    "gen6:a/0/8/2:0049/00:00020": ["Реши сам, как нам тебя называть."],
    "gen6:a/0/8/2:0049/00:00021": ["Выбери себе прозвище сам."],
    "gen6:a/0/8/2:0049/00:00022": ["Хотите звать тебя ", "?"],
    "gen6:a/0/8/2:0049/00:00023": ["Ладно! ♪", " тебе отлично подходит!", "Уверена, мы станем хорошими", "друзьями, и я тоже буду так тебя звать!"],
    "gen6:a/0/8/2:0049/00:00024": ["Эй! Можно уже посмотреть на покемонов?", "Хочу скорее познакомиться со своим напарником! ♪"],
    "gen6:a/0/8/2:0049/00:00025": ["Ага! Когда мы с Тревсом встретили", "своих покемонов, это было так здорово!", "Надеюсь, ты тоже испытаешь это чувство!"],
    "gen6:a/0/8/2:0049/00:00026": [", теперь твоя очередь", "выбирать!"],
    "gen6:a/0/8/2:0049/00:00027": [", выбирай ты."],
    "gen6:a/0/8/2:0049/00:00028": ["У-у-у...", "Так трудно выбрать!"],
    "gen6:a/0/8/2:0049/00:00029": ["Что? Серьёзно?", "Куда ты собрался?", "Давай выбирать покемона!"],
    "gen6:a/0/8/2:0049/00:00030": ["Будешь выбирать покемона?"],
    "gen6:a/0/8/2:0049/00:00031": ["Вот, держи, ", "!", "Кто станет твоим напарником?"],
    "gen6:a/0/8/2:0049/00:00032": ["Да, решение важное.", "Не торопись, подумай."],
    "gen6:a/0/8/2:0049/00:00033": ["Мы уже выбрали себе напарников.", "Покемоны и правда удивительные, да?"],
    "gen6:a/0/8/2:0049/00:00034": ["Хочешь дать своему", "покемону прозвище?"],
    "gen6:a/0/8/2:0049/00:00035": ["Ты выбрал прозвище", "«", "»?"],
    "gen6:a/0/8/2:0049/00:00036": ["Значит, прозвище своему", "покемону давать не будешь? ♪"],
    "gen6:a/0/8/2:0049/00:00037": ["Мой напарник — ", "!", "Вот мы и нашли друг друга!", "Мы с ним просто очаровашки! ♪"],
    "gen6:a/0/8/2:0049/00:00038": ["Приятно познакомиться, ", ".", "Я Серена.", "Благодаря тебе я стала настоящим", "тренером покемонов. Спасибо!"],
    "gen6:a/0/8/2:0049/00:00039": ["Рад знакомству, ", ".", "Я Калем.", "Благодаря тебе я стал настоящим", "тренером покемонов. Спасибо!"],
    "gen6:a/0/8/2:0049/00:00040": ["Простите, у меня тоже есть", "кое-что для тебя от профессора.", "Это поможет тебе лучше понять", "покемонов."],
    "gen6:a/0/8/2:0049/00:00041": [" получает", "свой ", "Покедекс", "!"],
    "gen6:a/0/8/2:0049/00:00042": ["Ну, понимаешь...", "Покедекс, который я тебе дал, —", "высокотехнологичный прибор, который", "автоматически записывает", "встреченных тобой покемонов!", "Профессор выдал нам его,", "потому что хочет, чтобы мы", "отправились в путешествие", "и заполнили Покедекс.", "Это важное поручение профессора, я уверен!"],
    "gen6:a/0/8/2:0049/00:00043": ["Да не переживай, Тревс!", "Ты иногда слишком серьёзен.", "Эй, ", "...", "Возьми ещё вот это.", "Это письмо от профессора.", "Он просил передать его твоей маме."],
    "gen6:a/0/8/2:0049/00:00044": ["Вот и всё! Мы выполнили", "поручение профессора.", "Пойдём, Тревс,", "искать покемонов!", "Пойдём!"],
    "gen6:a/0/8/2:0049/00:00045": ["В Калосе детям поручают взять Покедекс", "и отправиться в путешествие.", "Но сначала отнеси письмо", "маме."],
    "gen6:a/0/8/2:0049/00:00046": ["В Калосе детям поручают взять Покедекс", "и отправиться в путешествие.", "Но сначала отнеси письмо", "маме."],
    "gen6:a/0/8/2:0049/00:00047": ["С покемоном-напарником", "дикие покемоны тебе не страшны."],
    "gen6:a/0/8/2:0049/00:00048": ["С покемоном-напарником", "ты сможешь сражаться с дикими покемонами."],
    "gen6:a/0/8/2:0049/00:00049": ["У меня теперь есть свой ", "!", "Скоро мы будем играть вместе!", "С ним я отправлюсь в путешествие,", "и оно будет замечательным! ♪"],
    "gen6:a/0/8/2:0049/00:00050": [", подожди!"],
    "gen6:a/0/8/2:0049/00:00051": ["Ты станешь моим первым", "соперником в бою покемонов!"],
    "gen6:a/0/8/2:0049/00:00052": ["Ладно, малыш ", "!", "Это наш первый бой!", "Давай победим красиво!"],
    "gen6:a/0/8/2:0049/00:00053": ["Ты отлично сражался, ", "!", "Давай я подлечу твоих покемонов. ♪"],
    "gen6:a/0/8/2:0049/00:00054": ["Неплохо! Ну как, ", "?", "Давай я подлечу твоих покемонов. ♪"],
    "gen6:a/0/8/2:0049/00:00055": ["Передавай маме привет! ♪"],
    "gen6:a/0/8/2:0049/00:00056": ["Пожалуй, пойду", "сражаться с дикими покемонами!", "Надо сделать моего покемона", "сильнее! ♪"],
    "gen6:a/0/8/2:0049/00:00057": ["О! Ты один из детей,", "которых выбрал профессор?", "Сначала зайди домой и попроси помочь", "собраться в путешествие!"],
    "gen6:a/0/8/2:0049/00:00058": ["Привет! Вижу, дома тебе помогли", "собраться!", "Не забудь взять с собой побольше", "Покеболов и зелий!"],
    "gen6:a/0/8/2:0049/00:00059": ["Эй, тренер покемонов!", "Если войдёшь в высокую траву,", "может появиться дикий покемон!", "Но не бойся: твой покемон-напарник", "сразится за тебя!"],
}

PROTAGONIST_BRANCHES: dict[str, list[str]] = {
    "gen6:a/0/8/2:0053/00:00000": ["О, ты, должно быть, новый мальчик из", "соседнего дома. Добро пожаловать в Ванивайл!", "У нас есть дочь примерно твоего", "возраста. Если встретишь Серену,", "надеюсь, вы станете хорошими друзьями."],
    "gen6:a/0/8/2:0053/00:00001": ["О, ты, должно быть, новая девочка из", "соседнего дома. Добро пожаловать в Ванивайл!", "У нас есть сын примерно твоего", "возраста. Если встретишь Калема,", "надеюсь, вы станете хорошими друзьями."],
    "gen6:a/0/8/2:0053/00:00002": ["Хм! Мне нравится выражение мордочки твоего покемона.", "Уверен, если бы ты сразился с Сереной,", "этот бой помог бы вам обоим стать сильнее!"],
    "gen6:a/0/8/2:0053/00:00003": ["Хм! Мне нравится выражение мордочки твоего покемона.", "Уверен, если бы ты сразилась с Калемом,", "этот бой помог бы вам обоим стать сильнее!"],
}

STARTER_UI: dict[str, list[str]] = {
    "gen6:a/0/7/4:0063/00:00000": ["Выбери покемона."],
    "gen6:a/0/7/4:0063/00:00001": ["Травяной покемон"],
    "gen6:a/0/7/4:0063/00:00002": ["Огненный покемон"],
    "gen6:a/0/7/4:0063/00:00003": ["Водный покемон"],
    "gen6:a/0/7/4:0063/00:00004": ["Выбрать этого покемона?"],
    "gen6:a/0/7/4:0063/00:00005": ["Ты выбрал ", "!"],
}

LOCATION_UI: dict[str, list[str]] = {
    "gen6:a/0/7/4:0072/00:00006": ["Ванивайл-таун"],
    "gen6:a/0/7/4:0072/00:00009": ["Тропа Ванивайл"],
    "gen6:a/0/7/4:0072/00:00010": ["Аквакорд-таун"],
    "gen6:a/0/8/2:0049/00:00070": ["Аквакорд-таун", "Вода и цивилизация в согласии."],
}

FIRST_BATTLE_MOVES: dict[int, list[str]] = {
    3: [" бьёт «Тяжёлым ударом»!"],
    4: ["Дикий ", " бьёт «Тяжёлым ударом»!"],
    5: ["Вражеский ", " бьёт «Тяжёлым ударом»!"],
    66: [" применяет «Плеть-лиану»!"],
    67: ["Дикий ", " применяет «Плеть-лиану»!"],
    68: ["Вражеский ", " применяет «Плеть-лиану»!"],
    117: [" применяет «Виляние хвостом»!"],
    118: ["Дикий ", " применяет «Виляние хвостом»!"],
    119: ["Вражеский ", " применяет «Виляние хвостом»!"],
}

VANIVILLE_ADDITIONS: dict[str, list[str]] = {
    "gen6:a/0/8/2:0055/00:00016": ["Чирик-чирик! ♪"],
    "gen6:a/0/8/2:0055/00:00020": ["… … …"],
    "gen6:a/0/8/2:0055/00:00026": ["Вот ты у меня ", "молодец!", "Карту города можно выбрать в сумке", "когда она понадобится."],
    "gen6:a/0/8/2:0057/00:00007": ["Ррр... Грр..."],
    "gen6:a/0/8/2:0057/00:00008": ["Рааа!"],
    "gen6:a/0/8/2:0057/00:00009": ["Что это сейчас было?"],
}

REVISIONS: dict[str, list[str]] = {
    "gen6:a/0/8/2:0055/00:00001": ["Ты проверил(а) компьютер, который ", "папа подарил ", "тебе.", "Правило приключения № 1", "Кнопка X открывает меню!", "Правило приключения № 2", "Сохраняй прогресс командой «СОХРАНИТЬ»."],
    "gen6:a/0/8/2:0055/00:00003": ["…И ты", "уже без пижамы!"],
    "gen6:a/0/8/2:0055/00:00022": ["!", "Мы ещё толком не распаковали вещи,", "а уже столько всего происходит!", "Ладно! Подготовим тебя и ", "к путешествию —", "пора собираться!"],
    "gen6:a/0/8/2:0055/00:00013": ["Пора тебе собираться!", "Почему бы тебе не выйти и не поздороваться", "с соседями?"],
    "gen6:a/0/8/2:0055/00:00023": ["Вот, держи, ", ".", "Я положила тебе сменную одежду.", "Ну и неожиданный поворот!", "Прямо как последний рывок", "на гонках райхорнов!", "У тебя появились друзья!", "В твоей команде появился покемон!", "Теперь ты отправишься в путешествие по Калосу!"],
    "gen6:a/0/8/2:0055/00:00027": ["Нажми X, чтобы открыть сумку.", "Затем нажми + на крестовине и выбери", "карман КЛЮЧЕВЫЕ ПРЕДМЕТЫ.", "Выбери карту города — и путешествовать", "по Калосу станет проще простого!"],
    "gen6:a/0/8/2:0055/00:00028": ["Не знаю, что профессор Сикамор", "хочет показать тебе в путешествии...", "Но странствовать вместе со своим покемоном", "— прекрасный опыт."],
    "gen6:a/0/8/2:0057/00:00004": ["Прославленный профессор Сикамор", "живёт здесь, в Калосе.", "Я слышала, что он позвал пятерых ребят,", "включая нас.", "Но я удивлена, что он знает, кто ты.", "Ты ведь только недавно переехал в Ванивайл."],
    "gen6:a/0/8/2:0057/00:00005": ["Известный профессор Сикамор", "живёт здесь, в Калосе.", "Я слышал, он позвал пятерых ребят, включая нас.", "Но я удивлён, что он знает, кто ты.", "Ты ведь только недавно переехала в Ванивайл."],
    "gen6:a/0/8/2:0057/00:00010": ["Ха-ха-ха! Вот проказник!", "Наверное, Райхорн решил", "громко проводить тебя в путь!", "Ведь он знает тебя с самого рождения,", "как-никак!"],
    "gen6:a/0/8/2:0057/00:00011": ["Удачи, ", "!", "Действуй на полную!", "И не волнуйся!", "Покемоны будут рядом, так что", "всё получится!"],
    "gen6:a/0/8/2:0057/00:00012": ["Ладно, ", "!", "Счастливого пути вместе с ", "!", "Расскажи мне обо всём,", "что увидишь в дороге!"],
    "gen6:a/0/8/2:0057/00:00013": ["Ванивайл — хороший городок, правда?", "В Калосе столько замечательных городов!", "Когда вырасту, хочу побывать в каждом!"],
    "gen6:a/0/8/2:0057/00:00006": ["Будем ждать тебя в соседнем городе!", "И знаешь что?!", "Скоро у нас будет… покемон!", "Ну же, скорее! Пойдём!"],
    "gen6:a/0/7/4:0075/00:00007": ["Выбери одну из трёх скоростей текста,", "чтобы настроить темп показа сообщений."],
    "gen6:a/0/7/4:0125/00:00000": [" выбыл из боя!"],
    "gen6:a/0/7/4:0125/00:00001": ["Дикий ", " выбыл из боя!"],
    "gen6:a/0/7/4:0125/00:00002": ["Вражеский ", " выбыл из боя!"],
}


def set_translation(row: dict, source: dict, fragments: list[str], review_note: str) -> dict:
    text_slots = sum("text" in segment for segment in source["source_segments"])
    if len(fragments) != text_slots or any(not value for value in fragments):
        raise ValueError(f"Expected {text_slots} nonempty Russian text segments for {source['record_id']}")
    iterator = iter(fragments)
    row["translation_segments"] = [
        {"text": next(iterator)} if "text" in segment else {"control_words": list(segment["control_words"])}
        for segment in source["source_segments"]
    ]
    row["review_state"] = "assistant_reviewed_pending_human"
    row["review_evidence"] = {
        "source_hash_checked": True,
        "control_event_sequence_checked": True,
        "glossary_consulted": True,
        "runtime_checked": False,
        "uncertainty": "Human linguistic approval and runtime inspection are still required.",
    }
    row["review_note"] = review_note
    row["status"] = "machine_draft" if row["status"] == "machine_draft" else "draft"
    row.pop("source_text", None)
    row.pop("source_segments", None)
    row.pop("occurrences", None)
    return row


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, default=ROOT / "build/milestone-3b/source-catalog.jsonl")
    parser.add_argument("--pilot", type=Path, default=ROOT / "translations/pilot.jsonl")
    parser.add_argument("--early-game", type=Path, default=ROOT / "translations/early-game.jsonl")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "build/milestone-3e")
    args = parser.parse_args()

    source_by_id: dict[str, dict] = {}
    for line in args.catalog.open(encoding="utf-8"):
        source = json.loads(line)
        source_by_id.setdefault(source["record_id"], source)
    existing_files = [args.pilot, args.early_game]
    output_rows: dict[Path, list[dict]] = {}
    input_rows = {path: read_jsonl(path) for path in existing_files}

    for path, rows in input_rows.items():
        revised = []
        for row in rows:
            source = source_by_id.get(row["record_id"])
            if source is None or source["source_variant_sha256"] != row["source_variant_sha256"]:
                raise ValueError(f"Missing or stale source for {row['record_id']}")
            fragments = REVISIONS.get(row["record_id"])
            if fragments is not None:
                row = set_translation(row, source, fragments, "Reviewed against the exact source and controls; wording remains unapproved pending human review and runtime fit checks.")
            else:
                row["review_state"] = "assistant_reviewed_pending_human"
                row["review_evidence"] = {
                    "source_hash_checked": True,
                    "control_event_sequence_checked": True,
                    "glossary_consulted": True,
                    "runtime_checked": False,
                    "uncertainty": "No authored correction selected; human review and runtime inspection remain required.",
                }
                row["review_note"] = "Checked against the exact source, preserved controls, and consulted glossary; wording remains unapproved pending human review and runtime fit checks."
            revised.append(row)
        output_rows[path] = revised

    new_maps = [(args.early_game, OPENING), (args.early_game, PROTAGONIST_BRANCHES),
                (args.early_game, STARTER_UI), (args.early_game, LOCATION_UI),
                (args.early_game, VANIVILLE_ADDITIONS)]
    for path, mapping in new_maps:
        known = {(row["record_id"], row["source_variant_sha256"]) for row in output_rows[path]}
        for record_id, fragments in mapping.items():
            source = source_by_id.get(record_id)
            if source is None:
                raise ValueError(f"Opening source missing from catalog: {record_id}")
            key = (record_id, source["source_variant_sha256"])
            if key in known:
                continue
            row = {
                "record_id": record_id,
                "source_variant_sha256": source["source_variant_sha256"],
                "scope": "shared",
                "version_scope": sorted({str(item["dataset"]).split("/")[-1] for item in source.get("occurrences", [])}),
                "status": "draft",
                "context": "Aquacorde opening scene" if ":0049/" in record_id else "protagonist branch, starter UI, or early-game location",
            }
            row = set_translation(row, source, fragments, "New project-authored draft checked against source hash and control order; requires human linguistic approval and runtime checks.")
            output_rows[path].append(row)
            known.add(key)

    # Battle move templates are authored per move but retain their shared source IDs.
    target = output_rows[args.early_game]
    keys = {(r["record_id"], r["source_variant_sha256"]) for r in target}
    for source_id, fragments in FIRST_BATTLE_MOVES.items():
        record_id = f"gen6:a/0/7/4:0126/00:{source_id:05d}"
        source = source_by_id[record_id]
        key = (record_id, source["source_variant_sha256"])
        if key in keys:
            for index, existing in enumerate(target):
                if (existing["record_id"], existing["source_variant_sha256"]) == key:
                    target[index] = set_translation(
                        existing, source, fragments,
                        "Reviewed against the exact move template and placeholder; move-name terminology remains provisional and runtime fit is untested.")
                    break
            continue
        row = {
            "record_id": record_id,
            "source_variant_sha256": source["source_variant_sha256"],
            "scope": "shared",
            "version_scope": sorted({str(item["dataset"]).split("/")[-1] for item in source.get("occurrences", [])}),
            "status": "draft",
            "context": "starter first-battle move message",
        }
        row = set_translation(row, source, fragments, "Move name is provisional in the glossary; exact control sequence checked; human approval and in-game layout review required.")
        target.append(row)
        keys.add(key)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    for path, rows in output_rows.items():
        write_jsonl(path.resolve(), rows)
    print(json.dumps({"pilot_records": len(output_rows[args.pilot]), "early_game_records": len(output_rows[args.early_game]),
                      "total_records": sum(map(len, output_rows.values())), "statuses": sorted({r["status"] for rows in output_rows.values() for r in rows})}, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
