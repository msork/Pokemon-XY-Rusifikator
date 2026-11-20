# Milestone 3E: Early-Game Localization Review

Date: 2026-11-19

## Scope and result

This milestone expands the prior 53 draft records into a bounded 139-record opening/gameplay candidate set. The set includes the existing 12-record 3C pilot, 41 earlier opening drafts, and 86 additional or revised records. All newly authored strings remain drafts. The earlier 12 machine drafts remain `machine_draft`; structural review does not promote them to linguistic approval.

The opening dialogue and Options entries were reviewed against their exact catalog source hashes and segment/control sequence. Existing awkward wording was corrected where the source and control structure were clear. Dynamic gender-control messages, uncertain scene triggers, provisional move/place terminology, and strings affected by replacement characters remain explicitly unapproved. All 139 rows record assistant review evidence; 0 are human-reviewed, approved, marked validated, or newly tested in AzaharPlus.

## Source corpus and classification

Evidence comes from the ignored local catalog `build/milestone-3b/source-catalog.jsonl` and asset report `reports/milestone-3b/asset-catalog.json`:

- 281,728 unique coordinate/source-word variants and 1,005,104 occurrences across X/Y base and update datasets.
- 11,616 TextFile members and 66,666 member payloads rejected by the current TextFile parser. A rejection can be binary/non-text or an unsupported format; it is not automatically English.
- Two oversized archives were skipped under the scanner's 128 MiB cap. Their text coverage remains unknown.
- The current resource-path rule identifies 35,216 variants as English in `a/0/7/4` and `a/0/8/2`. Another 246,512 variants remain undetermined.
- `scripts/classify_english_candidates.py` reports 58 high-confidence and 38 review-priority lexical candidates outside the known path rule. These are inspection leads only; they are not relabeled as English. No new candidate resource has been promoted without a resource-level audit.
- The corpus also includes decoded U+FFFD characters in source words such as `Pok�mon`, `It�s`, and some gender-conditional split forms. The source hashes still point to the original exact binary records, but the current text decoder has not recovered every glyph/character mapping. The checklist displays the replacement character and flags it rather than silently reconstructing the source.
- The gender-conditioned string controls (including `0010 0003 1100 00FF 0202` and `0010 0003 1100 00FF 0403`) are preserved byte-for-byte, but their runtime substitution semantics are not decoded. Russian phrasing around these tokens remains unapproved and should be checked alongside the source replacement-character issue.

The character-name/appearance prompt for protagonist creation has not been found in the English-labeled TextFile records. `Male`/`Female` strings exist in other menus and are not sufficient evidence of protagonist-selection UI. The prompt may be in a different resource or generated outside these TextFiles. Character creation is therefore an explicit coverage gap.

## Early-game record map

All IDs below use the form `resource / GARC member / message`. The exact source-variant SHA-256 for every translated record is in [the scene-ordered runtime checklist](../testing/milestone-3e-runtime-checklist.md).

| Scene or content | Records in candidate | Evidence state |
|---|---|---|
| Options | `a/0/7/4 / 75/0 / 0, 3–7` | X, female-protagonist owner testing of the earlier 3C pilot confirmed the Options flow; no new runtime claim. |
| Character creation | No confirmed record | Unresolved resource/screen gap; no placeholder translations added. |
| Vaniville opening/home | `a/0/8/2 / 55/0 / 0–3, 10–28` (empty/postgame records are not translated); `a/0/8/2 / 57/0 / 1–13`; `a/0/7/4 / 72/0 / 6, 9, 10` | Message content and archive context identify the subject; exact event order/trigger is inferred pending runtime testing. Messages 55/16, 20, and 26 were added during this milestone. |
| Protagonist branches | `a/0/8/2 / 53/0 / 0–3` | Text explicitly distinguishes boy/girl and Serena/Calem branches. Pairing with player selection for 2/3 remains inferred. |
| Aquacorde opening/starter handoff | `a/0/8/2 / 49/0 / 0–59, 70` | IDs 0–59 form the extracted opening dialogue set, including meeting, nicknames, partner Pokémon, Pokédex handoff, and first battle. Per-line event trigger/order is not runtime-confirmed. Ancillary messages 60–71 other than 70 remain outside this pilot. |
| Starter-selection UI | `a/0/7/4 / 63/0 / 0–5` | Direct menu text and choice labels; not runtime-tested in this milestone. |
| Battle interface/moves | `a/0/7/4 / 124/0 / 71–72`; `125/0 / 0–2`; `126/0 / 3–5, 30–32, 66–68, 99–101, 117–119, 135–137` | Battle templates and move strings. Exact sequence varies by starter and battle outcome; runtime verification required. |

The Aquacorde sign/location text is `a/0/8/2 / 49/0 / 70`. Move-name choices for Pound, Vine Whip, and Tail Whip are provisional; their sources and reuse status are recorded in `glossary/terms.json`. The project does not claim official Gen VI console terminology for these terms.

## Translation and review workflow

Recreate the bounded strings from local catalog source and preserve the exact source control sequence:

```powershell
python scripts/build_milestone3e_translations.py
python scripts/validate_translation_data.py --translations translations/early-game.jsonl
```

`translations/pilot.jsonl` contains 12 earlier records. `translations/early-game.jsonl` contains 127 records after this milestone. Combined, they contain 139 unique source variants. Machine drafts keep their `machine_draft` state. The other records are `draft`. Every record has `assistant_reviewed_pending_human` review evidence; that field is not equivalent to a human review or approval.

## Glossary sources and licensing

The glossary now covers the encountered UI and system terms, characters, Kalos/Vaniville/Aquacorde locations, starter battle moves, starter abilities, early-game items, and battle terminology. Unverified terms remain `needs_research`; sourced candidates remain `provisional_review_required`.

- Bulbapedia's Russian Pokémon-name list is the reference for the separately maintained 721-species glossary. The page describes its Russian-name column as current official usage in Pokémon GO, Pokémon UNITE, TCG, animation, and merchandise; it does not establish those spellings as Gen VI console-game localization. Bulbapedia says its later article content is under CC BY-NC-SA 2.5; attribution and share-alike conditions apply to reused material. See [the species list](https://bulbapedia.bulbagarden.net/wiki/List_of_Russian_Pok%C3%A9mon_names) and [Bulbapedia copyright statement](https://bulbapedia.bulbagarden.net/wiki/Bulbapedia%3ACopyrights).
- Move/ability candidates in `glossary/terms.json` cite their source and license. These are terminology references, not official Gen VI console-game translations. Fan references with unverified licensing are not claimed as distributable source text.
- WTFPL Version 2 applies to original project code and documentation only. It does not relicense Nintendo/Game Freak material, Bulbapedia's CC BY-NC-SA-derived data, or other referenced material. Keep attribution and license notices attached to the species/terminology data. Before distributing a combined glossary or patch, review the noncommercial/share-alike restrictions and separate third-party-derived datasets from WTFPL project code.

## Update precedence and generated candidate

The local effective-resource selection verified in previous milestones is retained: update 1.5 `a/0/7/4` takes precedence; base `a/0/8/2` is the effective source because no update override exists for that resource. The builder independently records the selected source version and source/output hashes for X and Y.

The candidate is generated, uninstalled, and not runtime-tested. `scripts/verify_build_manifest.py` hashes all four output files and compares a second clean build. The two games' output hashes are identical because these effective source archives and selected translations are identical:

| Game | Resource | Effective source | Source SHA-256 | Output SHA-256 | Messages applied | Unchanged GARC members | Unchanged messages |
|---|---|---|---|---|---:|---:|---:|
| Pokémon X | `a/0/7/4` | update 1.5 | `ed8a7a8e69e24ffb4d55c8ff6912457dbd4b4fb8825f30b1511563ab91ba0881` | `8febfef4d41f9b11f8c705cdd795d0eab7f3cdec6880a8e3bb4cac3755a56108` | 38 | 145 | 3,557 |
| Pokémon X | `a/0/8/2` | base | `16b9a70f11fd6ac5779a577a16e457b793028be612d279dab28d1abf59349999` | `e8dfe6f963a3c8ee8855148d4d4209d40bbab687598b925ed791ea36026b2e6f` | 101 | 420 | 60 |
| Pokémon Y | `a/0/7/4` | update 1.5 | `ed8a7a8e69e24ffb4d55c8ff6912457dbd4b4fb8825f30b1511563ab91ba0881` | `8febfef4d41f9b11f8c705cdd795d0eab7f3cdec6880a8e3bb4cac3755a56108` | 38 | 145 | 3,557 |
| Pokémon Y | `a/0/8/2` | base | `16b9a70f11fd6ac5779a577a16e457b793028be612d279dab28d1abf59349999` | `e8dfe6f963a3c8ee8855148d4d4209d40bbab687598b925ed791ea36026b2e6f` | 101 | 420 | 60 |

Verification result: all 4 archive hashes match their manifest; the repeat build produced the same hashes; each archive's modified plus verified-unchanged member counts equal its total GARC members. The source hash is also recorded per output in the ignored build manifest.

```powershell
python scripts/build_gameplay_pilot.py --include-machine-drafts --translations translations/early-game.jsonl --milestone 3E --output build/milestone-3e/candidate
```

The SHA-256 manifest is `build/milestone-3e/candidate/manifest.json`. It is an ignored local artifact because it identifies derived game binaries; do not stage it or the candidate archives. The manifest confirms unrelated GARC members and untranslated messages were verified unchanged for each rebuilt resource. LayeredFS installation and rollback must be prepared as a separate owner-approved action after draft review; no emulator directory was changed in 3E.

## Coverage and unresolved work

The generated dashboard is `reports/milestone-3e/coverage.md` (ignored report output):

- 139 translated source variants: 127 draft, 12 machine draft.
- Assistant review evidence: 139; human-reviewed: 0; approved: 0; translation status `validated`: 0; tested in game during 3E: 0. The automated structural validator passed all 139 rows.
- 139 / 35,216 identified English variants are represented (0.3947%).
- 139 / 281,728 catalog variants are represented (0.0493%).
- 35,077 identified-English variants and 281,589 total indexed variants remain untranslated.
- 246,512 variants remain language-undetermined; 66,666 member payloads were rejected by the TextFile parser; two large archives remain skipped.

The checklist includes the candidate lines, IDs, hashes, code annotations, and X/Y/male/female runtime result rows. Next, a human linguist should review the 53 pre-existing records and 89 added/revised rows against the English/Russian pairs, then test each game and protagonist branch using safe new-game/test-save procedure. Record clipping and typography. Serena-specific and Pokémon Y runtime contexts remain unverified from the earlier pilot. No bulk translation should begin until the control-word decode/replacement-character issues and character-creation resource gap are better understood.
