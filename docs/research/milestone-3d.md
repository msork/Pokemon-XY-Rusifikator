# Milestone 3D: Translation Pipeline and Bounded Early-Game Draft

## Scope and current evidence

The local Milestone 3B catalog contains 281,728 unique coordinate/source-word variants and 1,005,104 message occurrences across X/Y base and update 1.5 datasets. It covers 11,616 TextFile members accepted by the current parser. Of those variants, 35,216 are labeled English because they come from `a/0/7/4` or `a/0/8/2`; 246,512 variants from other resources are labeled `undetermined`. This is a resource-path classification, not language detection. It does not prove that every English string in the games is covered.

The scanner found 568 GARC-signature files and parsed 566 under its 128 MiB cap. It recorded 66,666 member payloads that did not parse as TextFiles; these include non-text and unsupported content and have not been individually classified. Two 1,041,219,296-byte base archives at `a/0/0/7` (one per game) were skipped. Executable literals, other resource formats, and embedded text in images/video/audio are not represented in the coverage denominator. Complete English corpus coverage is therefore unknown.

Identical X/Y and base/update messages are keyed by stable resource/member/message coordinates and exact decoded source-word SHA-256. Duplicate English display strings retain their separate coordinates, ordered control events, scopes, and occurrences. Update 1.5 is selected for a resource when that path exists in the update tree; otherwise the base resource is selected. The pilot builder applies this per resource, so it builds `a/0/7/4` from update 1.5 and `a/0/8/2` from base for both games. The owner confirmed LayeredFS replacement for update 1.5 `a/0/7/4`; base `a/0/8/2` runtime resolution has not been independently confirmed.

## Translation state and workflow

Translation records use these states: `untranslated`, `draft`, `machine_draft`, `reviewed`, `approved`, `validated`, and `tested_in_game`. Review/approval states require named attribution; `tested_in_game` additionally requires runtime evidence. Runtime observations are not substituted for linguistic approval. The twelve Milestone 3C entries and the 41 new entries remain drafts. None of the 41 new entries has owner runtime evidence.

The reusable workflow is:

1. Build or refresh the ignored source catalog with `python scripts/build_translation_catalog.py`.
2. Put selected stable IDs in a UTF-8 file, then run `python scripts/export_translation_batch.py --ids build/selected-ids.txt --output build/translation-batch.jsonl`.
3. Edit only translation text and state in the batch. Source hash, source text/segments, provenance, and control words are validated on import.
4. Merge with `python scripts/import_translation_batch.py --batch build/translation-batch.jsonl --output translations/section.jsonl`.
5. Validate with `python scripts/validate_translation_data.py --translations translations/section.jsonl`.
6. Generate an ignored coverage report with `python scripts/report_translation_coverage.py --translations translations/section.jsonl`.
7. Build a local, unapproved X/Y candidate with `python scripts/build_gameplay_pilot.py --include-machine-drafts --translations translations/section.jsonl --output build/milestone-3d/candidate`.

The build requires explicit `--include-machine-drafts` because these are test candidates. It selects effective base/update resources independently for each game, checks source hashes before/after, validates control-event sequences, and verifies that unrelated GARC members and untranslated messages remain unchanged. Generated archives and source catalogs are ignored and must not be committed or redistributed.

## Bounded early-game draft and limits

`translations/early-game.jsonl` adds 41 manually authored draft records. Together with the twelve existing Milestone 3C records, the local candidate has 53 translated message variants. It includes opening bedroom/home dialogue, neighbor greetings, selected map/inventory guidance, and generic first-battle templates. The dialogue coordinates `a/0/8/2` members `55/0` and `57/0` were selected from their English text and remain scene-context inferences; stable event-to-message mapping has not been proven for every line.

This is not yet a complete opening section. The source catalog has no event graph, and the current draft selection does not include a verified player-name/gender character-creation screen, the Aquacorde starter-choice exchange, or all first-battle context. A search found an Aquacorde location label at `a/0/8/2`, member `49/0`, message `70`, and later dialogue referring to the battle in Aquacorde at member `67/0`, message `6`; neither identifies the initial starter-selection messages. Those targets must be mapped through event/script analysis and owner gameplay before translating them. Do not infer scene assignment solely from nearby numeric IDs.

The Russian drafts were not reviewed by a human linguist. The first-battle generic strings in member `125/0` use concise `пал!` to limit expansion; wording and grammatical agreement still need review. No claim is made that these new lines fit in game. The owner-confirmed Milestone 3C runtime result remains separate: Pokémon X, female protagonist, showed the previously installed Options, mother's dialogue, Calem, and Shauna pilot; Pokémon Y and Serena remain untested. That evidence does not validate the new 41 drafts.

## Glossary

The existing 721-species list remains the primary species-name source, keyed by National Pokédex number and separately licensed CC BY-NC-SA 2.5. Do not merge that dataset into the WTFPL-licensed project code/docs. `glossary/terms.json` now has categories for UI, locations, moves, abilities, items, character names, battle terminology, and system messages. It contains 44 seeds: 36 have provisional Russian text and eight remain `needs_research`; unresolved entries span locations, moves, abilities, and items. Provisional entries are not authoritative game localization. Sources and uncertainty are recorded per term where applicable; reference material with unverified reuse terms must not be redistributed as source-derived text.

Only entries marked `enforce: true` are checked automatically as exact-form terms; inflected Russian forms require human review. Species-name validation consults the separate 721-entry glossary. Glossary coverage is a starter set, not a complete moves/abilities/items/locations database.

## Validation and generated coverage

Run:

```powershell
python -m unittest discover -s tests -v
python scripts/build_early_game_drafts.py
python scripts/validate_translation_data.py --translations translations/early-game.jsonl
python scripts/report_translation_coverage.py --translations translations/early-game.jsonl
python scripts/build_gameplay_pilot.py --include-machine-drafts --translations translations/early-game.jsonl --output build/milestone-3d/candidate
```

At this milestone the dashboard reports 53 draft/machine-draft records, 0 reviewed, 0 approved, 0 marked `validated`, and 0 newly tested in game. All 53 pass the current automated structural validator; their database status remains draft pending human review. The dashboard covers 53 of 35,216 identified English variants (0.150500%) and 53 of 281,728 total catalog variants (0.018812%). There are 35,163 untranslated identified-English variants and 281,675 untranslated catalog variants. The all-catalog percentage is not a full-game localization percentage because the parser exclusions and language classification gaps above remain.

The four generated local candidate archives have these SHA-256 hashes:

| Game | Resource | Effective source | Candidate SHA-256 |
|---|---|---|---|
| Pokémon X | `a/0/7/4` | update 1.5 | `cf7f77613a0378beb4004ace9f0e8d03a0fc44456c148077b4e6319637eab00b` |
| Pokémon X | `a/0/8/2` | base | `2ec2ba4b88bd288c3e49d60a78d88ce3336f31e113aa77acccedd28dc5002722` |
| Pokémon Y | `a/0/7/4` | update 1.5 | `cf7f77613a0378beb4004ace9f0e8d03a0fc44456c148077b4e6319637eab00b` |
| Pokémon Y | `a/0/8/2` | base | `2ec2ba4b88bd288c3e49d60a78d88ce3336f31e113aa77acccedd28dc5002722` |

The X/Y outputs happen to hash identically because these selected source resources and shared translations are identical; the builder still reads each game's own effective resource and verifies its provenance. These are generated full archives containing copyrighted game data, stay under ignored `build/`, and are not distributable. A release must use a legally reviewed delta format.

## Owner testing plan (future, not performed here)

No patch was installed and AzaharPlus was not launched for Milestone 3D. Before runtime testing these drafts, a Russian reviewer should review/approve the batch, then rebuild and verify the new hashes. For the next owner session, use a backed-up disposable save or a new save that will not overwrite an existing one; test Pokémon X female and Pokémon Y separately, record protagonist selection, and capture screenshots/video for each target. Check opening home dialogue, neighbor meeting, menu/map guidance, and battle templates when their exact event is reached. Record which IDs actually appeared, text wrapping, placeholders, control rendering, and screen fit. Then test the Aquacorde starter sequence only after its exact IDs have been mapped. Keep Y and Serena evidence distinct from the existing X female pilot result. Do not mark a record `tested_in_game` without an ID-specific observation and evidence note.

## Remaining work to a full release

- Inspect both skipped `a/0/0/7` archives and classify all 66,666 rejected member payloads; discover executable and non-GARC strings.
- Determine which `undetermined` resources contain English and build a language-aware inventory, including text embedded in non-TextFile assets.
- Map message coordinates to event/script context, including character creation, Aquacorde and starter choice, battle branches, and protagonist/gender variants.
- Expand/research complete move, ability, item, location, character, battle, UI, multiplayer, tutorial, postgame, and system terminology. Human-review every translation and preserve unresolved terms.
- Translate all identified English strings by bounded gameplay sections; maintain X/Y and base/update overrides and report every untranslated item.
- Validate actual font glyphs, punctuation, glyph widths, text boxes, line breaks, dynamic names, UI constraints, and runtime behavior in both titles with update 1.5.
- Localize non-text graphics and other user-facing assets if required, under separate asset and licensing review.
- Produce legally reviewed delta patches, installer/rollback packages, compatibility checks, and release notes. Do not distribute original/derived full game archives or the CC BY-NC-SA species glossary outside its attribution, noncommercial, and share-alike conditions.
