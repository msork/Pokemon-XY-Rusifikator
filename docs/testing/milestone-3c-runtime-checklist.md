# Milestone 3C Runtime Checklist: Exact Pilot Records

This checklist is transcribed from `translations/pilot.jsonl` and the corresponding rows in the ignored `build/milestone-3b/source-catalog.jsonl`. It covers all 12 pilot records. English source segments and Russian translation segments are shown in order; control annotations stand between segments and do not replace or alter their stored word values.

All pilot records remain `machine_draft`. No exact scene location for these records has been confirmed by runtime evidence. The file-level `context` labels and the semantic placement notes below are not runtime verification. Treat gameplay placements and protagonist conditions identified as inferred as hypotheses for owner testing.

The source uses the right single quotation mark U+2019 (`’`) in contractions and U+00E9 (`é`) in Pokémon. Both are reproduced as decoded from the catalog.

## Control annotation key

- `⟦LINE BREAK — raw 000A⟧`: TextFile newline unit `000A`.
- `⟦TEXT CLEAR — raw 0010 0001 BE01⟧`: The parser recognizes this control as a text-clear event. The exact raw control words are shown.
- `⟦VARIABLE/PLACEHOLDER — raw 0010 0002 0100 0000⟧`: Variable/control sequence retained as stored. The pilot context treats it as the player's name, but this checklist does not reinterpret its underlying words.

There are no page-break control words in these 12 records. The `BE01` sequence is identified by the project parser as text clear, not labeled here as a page break.

## Options

The pilot record context is `Options screen`. The exact resource context is `a/0/7/4`, member `75/0`; these are update 1.5 resources for both games. The screen/menu role is recorded in the pilot metadata, but exact visible placement and fit still need runtime confirmation.

### Options title

| Field | Value |
|---|---|
| Record | `gen6:a/0/7/4:0075/00:00000` |
| Resource / member / message | `a/0/7/4` / `75/0` / `0` |
| Where and when | Options screen title/label according to pilot context. Exact screen placement is not runtime-verified. |
| Protagonist | Either; no protagonist-specific variant recorded. |
| Controls/placeholders | None. |

| Original English (verbatim extracted segment) | Russian translation (verbatim record segment) |
|---|---|
| `OPTIONS` | `НАСТРОЙКИ` |

### Text speed heading

| Field | Value |
|---|---|
| Record | `gen6:a/0/7/4:0075/00:00003` |
| Resource / member / message | `a/0/7/4` / `75/0` / `3` |
| Where and when | Options screen; the text says “TEXT SPEED,” so placement as the text-speed heading is inferred. |
| Protagonist | Either. |
| Controls/placeholders | None. |

| Original English (verbatim extracted segment) | Russian translation (verbatim record segment) |
|---|---|
| `TEXT SPEED` | `СКОРОСТЬ ТЕКСТА` |

### Slow option

| Field | Value |
|---|---|
| Record | `gen6:a/0/7/4:0075/00:00004` |
| Resource / member / message | `a/0/7/4` / `75/0` / `4` |
| Where and when | Options screen; a text-speed choice is inferred from its text and adjacent records. |
| Protagonist | Either. |
| Controls/placeholders | None. |

| Original English (verbatim extracted segment) | Russian translation (verbatim record segment) |
|---|---|
| `SLOW` | `МЕДЛЕННО` |

### Normal option

| Field | Value |
|---|---|
| Record | `gen6:a/0/7/4:0075/00:00005` |
| Resource / member / message | `a/0/7/4` / `75/0` / `5` |
| Where and when | Options screen; a text-speed choice is inferred from its text and adjacent records. |
| Protagonist | Either. |
| Controls/placeholders | None. |

| Original English (verbatim extracted segment) | Russian translation (verbatim record segment) |
|---|---|
| `NORMAL` | `НОРМАЛЬНО` |

### Fast option

| Field | Value |
|---|---|
| Record | `gen6:a/0/7/4:0075/00:00006` |
| Resource / member / message | `a/0/7/4` / `75/0` / `6` |
| Where and when | Options screen; a text-speed choice is inferred from its text and adjacent records. |
| Protagonist | Either. |
| Controls/placeholders | None. |

| Original English (verbatim extracted segment) | Russian translation (verbatim record segment) |
|---|---|
| `FAST` | `БЫСТРО` |

### Text-speed explanation

| Field | Value |
|---|---|
| Record | `gen6:a/0/7/4:0075/00:00007` |
| Resource / member / message | `a/0/7/4` / `75/0` / `7` |
| Where and when | Options screen according to pilot context; placement as help text for text-speed choices is inferred from its wording. |
| Protagonist | Either. |
| Controls/placeholders | One line break, raw `000A`; no other controls or placeholders. |

| Original English (verbatim extracted segments) | Russian translation (verbatim segments) |
|---|---|
| `You can choose from three different text-scrolling speeds`<br>⟦LINE BREAK — raw 000A⟧<br>`to control how quickly messages appear.` | `Можно выбрать одну из трёх скоростей прокрутки текста`<br>⟦LINE BREAK — raw 000A⟧<br>`чтобы настроить, как быстро появляются сообщения.` |

## Mother's dialogue

Both records are tagged `early-game dialogue` in the pilot file. Their exact scene placement below is inferred from the wording and sequence; it has not been runtime-confirmed.

### Morning greeting

| Field | Value |
|---|---|
| Record | `gen6:a/0/8/2:0055/00:00010` |
| Resource / member / message | `a/0/8/2` / `55/0` / `10` |
| Where and when | Inferred: mother's morning dialogue after the move, likely early in the game. Exact scene trigger is unverified. |
| Protagonist | Either; translation was drafted to avoid grammatical-gender assumptions. |
| Controls/placeholders | Player-name variable/control raw `0010 0002 0100 0000`; text clear raw `0010 0001 BE01`; two line breaks, each raw `000A`. |

| Original English (verbatim extracted segments) | Russian translation (verbatim segments) |
|---|---|
| `Morning, `<br>⟦VARIABLE/PLACEHOLDER — raw 0010 0002 0100 0000⟧<br>`!`<br>⟦TEXT CLEAR — raw 0010 0001 BE01⟧<br>⟦LINE BREAK — raw 000A⟧<br>`You sure slept well!`<br>⟦LINE BREAK — raw 000A⟧<br>`All rested up from the move?` | `Доброе утро, `<br>⟦VARIABLE/PLACEHOLDER — raw 0010 0002 0100 0000⟧<br>`!`<br>⟦TEXT CLEAR — raw 0010 0001 BE01⟧<br>⟦LINE BREAK — raw 000A⟧<br>`Хорошо спалось?`<br>⟦LINE BREAK — raw 000A⟧<br>`Удалось отдохнуть после переезда?` |

### Send-off

| Field | Value |
|---|---|
| Record | `gen6:a/0/8/2:0055/00:00013` |
| Resource / member / message | `a/0/8/2` / `55/0` / `13` |
| Where and when | Inferred: mother's send-off encouraging the player to go outside and meet neighbors. Exact scene trigger is unverified. |
| Protagonist | Either. |
| Controls/placeholders | Text clear raw `0010 0001 BE01`; two line breaks, each raw `000A`. |

| Original English (verbatim extracted segments) | Russian translation (verbatim segments) |
|---|---|
| `It’s about time you got going!`<br>⟦TEXT CLEAR — raw 0010 0001 BE01⟧<br>⟦LINE BREAK — raw 000A⟧<br>`Why don’t you step out and say hello to`<br>⟦LINE BREAK — raw 000A⟧<br>`the neighbors?` | `Пора тебе собираться!`<br>⟦TEXT CLEAR — raw 0010 0001 BE01⟧<br>⟦LINE BREAK — raw 000A⟧<br>`Почему бы тебе не выйти и не поздороваться с`<br>⟦LINE BREAK — raw 000A⟧<br>`соседями?` |

## Serena / Calem

Both records are tagged `early-game dialogue`. The first-meeting-in-town placement and protagonist pairing reflect the pilot's intended interpretation; neither has been confirmed by runtime testing in this milestone.

### Serena variant

| Field | Value |
|---|---|
| Record | `gen6:a/0/8/2:0057/00:00001` |
| Resource / member / message | `a/0/8/2` / `57/0` / `1` |
| Where and when | Inferred: Serena introduces herself as the neighbor in Vaniville Town, early in the story. Exact trigger is unverified. |
| Protagonist | Intended for a male protagonist; inferred from the Serena variant. |
| Controls/placeholders | Text clear raw `0010 0001 BE01`; two line breaks, each raw `000A`. |

| Original English (verbatim extracted segments) | Russian translation (verbatim segments) |
|---|---|
| `Welcome to Vaniville Town!`<br>⟦TEXT CLEAR — raw 0010 0001 BE01⟧<br>⟦LINE BREAK — raw 000A⟧<br>`My name’s Serena.`<br>⟦LINE BREAK — raw 000A⟧<br>`I’m your neighbor.` | `Добро пожаловать в Ванивилл!`<br>⟦TEXT CLEAR — raw 0010 0001 BE01⟧<br>⟦LINE BREAK — raw 000A⟧<br>`Меня зовут Серена.`<br>⟦LINE BREAK — raw 000A⟧<br>`Я твоя соседка.` |

### Calem variant

| Field | Value |
|---|---|
| Record | `gen6:a/0/8/2:0057/00:00002` |
| Resource / member / message | `a/0/8/2` / `57/0` / `2` |
| Where and when | Inferred: Calem introduces himself as the neighbor in Vaniville Town, early in the story. Exact trigger is unverified. |
| Protagonist | Intended for a female protagonist; inferred from the Calem variant. |
| Controls/placeholders | Text clear raw `0010 0001 BE01`; two line breaks, each raw `000A`. |

| Original English (verbatim extracted segments) | Russian translation (verbatim segments) |
|---|---|
| `Welcome to Vaniville Town!`<br>⟦TEXT CLEAR — raw 0010 0001 BE01⟧<br>⟦LINE BREAK — raw 000A⟧<br>`The name’s Calem.`<br>⟦LINE BREAK — raw 000A⟧<br>`I live next door.` | `Добро пожаловать в Ванивилл!`<br>⟦TEXT CLEAR — raw 0010 0001 BE01⟧<br>⟦LINE BREAK — raw 000A⟧<br>`Меня зовут Калем.`<br>⟦LINE BREAK — raw 000A⟧<br>`Я живу по соседству.` |

## Shauna

Both records are tagged `early-game dialogue`. A conversation with Shauna and the neighbor group is inferred from the lines; exact scene position, trigger, and sequence are not runtime-confirmed.

### Shauna's greeting

| Field | Value |
|---|---|
| Record | `gen6:a/0/8/2:0057/00:00003` |
| Resource / member / message | `a/0/8/2` / `57/0` / `3` |
| Where and when | Inferred: Shauna greets the player and says the group came to get them, early in the story. Exact trigger is unverified. |
| Protagonist | Either; no gender-specific version is indicated by this record. |
| Controls/placeholders | Three line breaks, raw `000A`; text clear raw `0010 0001 BE01`. |

| Original English (verbatim extracted segments) | Russian translation (verbatim segments) |
|---|---|
| `And I’m Shauna!`<br>⟦LINE BREAK — raw 000A⟧<br>`Great to meet you!`<br>⟦TEXT CLEAR — raw 0010 0001 BE01⟧<br>⟦LINE BREAK — raw 000A⟧<br>`Guess what!`<br>⟦LINE BREAK — raw 000A⟧<br>`We’ve come to get you!` | `А я Шауна!`<br>⟦LINE BREAK — raw 000A⟧<br>`Приятно познакомиться!`<br>⟦TEXT CLEAR — raw 0010 0001 BE01⟧<br>⟦LINE BREAK — raw 000A⟧<br>`А знаешь что?`<br>⟦LINE BREAK — raw 000A⟧<br>`Мы пришли за тобой!` |

### Next-town / Pokémon announcement

| Field | Value |
|---|---|
| Record | `gen6:a/0/8/2:0057/00:00006` |
| Resource / member / message | `a/0/8/2` / `57/0` / `6` |
| Where and when | Inferred: continuation of early neighbor-group dialogue; mentions waiting in the next town and getting a Pokémon. Exact trigger/sequence is unverified. |
| Protagonist | Either; no gender-specific version is indicated by this record. |
| Controls/placeholders | Two text clears, each raw `0010 0001 BE01`; three line breaks, each raw `000A`. |

| Original English (verbatim extracted segments) | Russian translation (verbatim segments) |
|---|---|
| `We’ll wait for you in the next town over!`<br>⟦LINE BREAK — raw 000A⟧<br>`And you know what?!`<br>⟦TEXT CLEAR — raw 0010 0001 BE01⟧<br>⟦LINE BREAK — raw 000A⟧<br>`We’re going to get...a Pokémon!`<br>⟦TEXT CLEAR — raw 0010 0001 BE01⟧<br>⟦LINE BREAK — raw 000A⟧<br>`C’mon! Hurry! Let’s go!` | `Будем ждать тебя в соседнем городе!`<br>⟦LINE BREAK — raw 000A⟧<br>`И знаешь что?!`<br>⟦TEXT CLEAR — raw 0010 0001 BE01⟧<br>⟦LINE BREAK — raw 000A⟧<br>`Мы получим... покемона!`<br>⟦TEXT CLEAR — raw 0010 0001 BE01⟧<br>⟦LINE BREAK — raw 000A⟧<br>`Скорее! Пойдём!` |

## Owner runtime recording

For each game, mark each row only after observing it in AzaharPlus with update 1.5. Record actual scene and trigger, protagonist gender, visible text, substitutions, wrapping/clipping, and control timing. Keep X and Y observations separate. No test is marked passed by this document.

| Group | X result / evidence | Y result / evidence |
|---|---|---|
| Options, messages 0 and 3–7 | Pending | Pending |
| Mother's dialogue, messages 10 and 13 | Pending | Pending |
| Serena / Calem, message 1 or 2 | Pending | Pending |
| Shauna, messages 3 and 6 | Pending | Pending |
