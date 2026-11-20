# Milestone 3G: Text corruption and battle UI investigation

## Scope and runtime evidence

The owner reported the following during Pokémon X testing with the female protagonist and the Milestone 3F candidate:

- Computer line: `ButchТы проверил(а) компьютер, который па подарил бе.`
- Mirror line: `...И тыe без пижамы!`
- Battle interface and battle text still included English labels such as FIGHT, BAG, RUN, POKÉMON, HP, Lv., and Chespin.

These are owner-reported runtime observations for Pokémon X, female protagonist. Pokémon Y and the male protagonist have not been runtime-checked for these defects. No AzaharPlus session was launched during Milestone 3G.

## Dialogue source and diagnosis

The catalog maps the first two defects to the base-game script archive `a/0/8/2`, member `0055/00`:

| Message | Source hash | Extracted source structure | Finding |
|---|---|---|---|
| `00001` | `7785bd5dab9394c2e6acc68ef09bc76d3855d357baa7b026f69fbde87fcbd626` | Player-name variable `0010 0002 0100 0000`; text ` checked the PC h`; gender selection `0010 0003 1100 00FF 0202`; text `iser dad gave h`; the same gender selection; text `imer.` | `source_text` flattens both branches into `hiser`/`himer`; this is not a literal source spelling. The current Russian draft also started with `Ты` after the player-name variable, which explains the observed `ButchТы` duplication. The source message does not contain U+FFFD. |
| `00003` | `d75ef8c12f76833f88ecf762c7aa57a59ad4bce36d906b257a317fee7d51b3a5` | Text `...And changed out of h`; gender selection `0010 0003 1100 00FF 0202`; text `iser pajamas!` | The marker selects gender-dependent fragments across adjacent text. It is not an ordinary printable placeholder. The Russian draft placed a neutral phrase around that selection point, producing the stray character. The source message does not contain U+FFFD. |

The Gen VI message encoding reference describes function `0x1100` as gender-dependent text; the local source words independently show the same selection event repeated around the English `his`/`her` alternatives. The full reference is [Bulbapedia's Generation V–present character encoding notes](https://bulbapedia.bulbagarden.net/wiki/Character_encoding_(Generation_V%E2%80%93present)). The message container and its encrypted records are consistent with the public [pkNX TextFile implementation](https://github.com/kwsch/pkNX/blob/master/pkNX.Structures/Text/TextFile.cs); project round-trip and source-hash checks are performed locally.

The correction in `translations/early-game.jsonl` now retains the player-name variable and the gender-neutral `проверил(а)` wording, removes the extra `Ты`, and merges the neutral clause into one text segment. The mirror draft is `…И ты уже без пижамы!`. For these two records only, the obsolete gender-selection events are explicitly removed because the Russian wording no longer branches by gender. Every other control event, including the player-name variable, text clears, and line breaks in message 1, remains in order. `src/extraction/messages.py` accepts this removal only when the caller names the exact `0010 0003 1100 00FF 0202` event; unrelated control changes still fail validation.

This is a structural correction candidate, not a runtime-confirmed fix. The owner must check it with both protagonist genders and both games before it can be treated as solved.

## Battle text resources

The English TextFile resource is `a/0/7/4`; update 1.5 is present for X and Y and is the effective resource used by the candidates. The source catalog identifies these relevant records:

| Content | Resource coordinates | Evidence and limits |
|---|---|---|
| Main menu labels | `a/0/7/4`, member `0114/00`, messages `0–5` (`POKÉMON`, `POKÉDEX`, `BAG`, empty, `SAVE`, `OPTIONS`) | Exact source labels are present in the TextFile catalog. The record-to-screen binding is inferred from the strings; the candidate changes only non-empty exact labels not already translated by the existing pilot. |
| HP/PP/level UI strings | `a/0/7/4`, including members `0011`, `0012`, `0064`, `0123`, `0127`, `0129`, and `0140` | Exact `HP`, `PP`, `Lv.`, and `NEXT LV.` records are text, not binary replacements. `a/0/7/4` contains 164 source variants mentioning HP and 44 mentioning PP; many are move descriptions and are not translated yet. |
| Species names | `a/0/7/4`, member `0080/00`, message `00650` = `Chespin` | The generated Russian name is `Чеспин`, from the existing National Pokédex 650 glossary entry. It is not an independent transliteration. |
| Move names and descriptions | `a/0/7/4`, members `0013/00`, `0014/00`, and `0015/00` | The existing catalog identifies move-name tables and move descriptions here. The 3G candidate does not attempt bulk move translation. HP/PP terms are enforced when these source strings are translated. |
| Battle message templates | `a/0/7/4`, members `0124/00`, `0125/00`, and `0126/00` | Used by the earlier gameplay pilot. Exact on-screen event ordering is not established for every message. |
| `FIGHT` command | No exact `FIGHT` source string was found in the extracted TextFile catalog. | The text location remains unresolved. The candidate UI archive `a/1/7/9` is a base-game GARC in both titles (SHA-256 `72d1e4b334c4c65a78035c1240057e5880da3dd6a7ef677be19dca9e3ad7582d`); the update does not contain this path. Its sole member `0/0` is 73,400 bytes and contains a `CLIM` section at offset 38,410. Neither ASCII nor UTF-16LE `FIGHT` occurs in that member. Open-source [pk3DS BCLIM code](https://github.com/kwsch/png2bclim/blob/master/png2bclim/BCLIM.cs) identifies `CLIM` as an image container signature. This makes a texture-based source plausible, but does not prove that this exact section contains the battle button label. Executable strings also remain possible because ExeFS was not part of the four RomFS datasets. |

The user-reported English `BAG` and `RUN` labels have matching TextFile entries, but the source catalog alone cannot prove that the battle screen uses those particular entries. `POKÉMON` is present as a text label in member `0114/00`; its use on the battle command button is not runtime-confirmed. The English `FIGHT` label is absent from the extracted TextFile corpus. It has not been blindly substituted in binary assets.

The game font tables lack static Cyrillic mappings, but owner testing in Milestone 3A confirmed the Russian alphabet and Ё/ё render on the language-selection screen under AzaharPlus. That does not verify width or wrapping on battle buttons, summary panels, or move descriptions. `ОЗ` and `ОС` have the same character count as HP and PP, respectively, but actual glyph advances may differ. `СУМКА`, `БЕГ`, `ПОКЕМОНЫ`, `ПОКЕДЕКС`, and `Чеспин` also need in-game fit checks.

## Terminology and validation

`glossary/terms.json` now records:

- `HP` → `ОЗ` (Очки здоровья)
- `PP` → `ОС` (Очки силы)
- `Lv.` → `Ур.`
- Context-specific UI candidates for POKÉMON, POKÉDEX, BAG, RUN, and other menu labels. FIGHT remains `needs_research` because its source asset is not located.

The translation validator enforces actual Cyrillic `ОЗ` and `ОС` whenever a translated source contains the matching exact abbreviation. A Latin `OZ` or `OS` fails that check. This is a targeted glossary rule, not a binary-wide search-and-replace. Until the unlocalized move descriptions, summaries, healing text, and other messages are translated, their English abbreviations remain unchanged.

## Candidate build

Run from the project root:

```powershell
python scripts/build_milestone3g_fixes.py
python scripts/build_milestone3g_terms.py
python -X utf8 scripts/validate_translation_data.py --translations translations/early-game.jsonl --translations translations/milestone3g-battle.jsonl
python scripts/build_gameplay_pilot.py --include-machine-drafts --translations translations/early-game.jsonl --translations translations/milestone3g-battle.jsonl --milestone 3G --output build/milestone-3g/candidate
python scripts/verify_build_manifest.py build/milestone-3g/candidate/manifest.json
```

The candidate remains unapproved. It has been installed in both games' LayeredFS mod folders for owner runtime testing; no Milestone 3G AzaharPlus launch has occurred. Both games produce the same archive hashes because the selected effective source archives and message variants are identical:

| Game | Resource | Effective source | Source SHA-256 | Candidate SHA-256 |
|---|---|---|---|---|
| Pokémon X | `a/0/7/4` | update 1.5 | `ed8a7a8e69e24ffb4d55c8ff6912457dbd4b4fb8825f30b1511563ab91ba0881` | `4df53ab9e1a7fa68d0488640e722cda884a6b8299ee322082a0fd341464e2f2e` |
| Pokémon X | `a/0/8/2` | base (no update override) | `16b9a70f11fd6ac5779a577a16e457b793028be612d279dab28d1abf59349999` | `6f24c4590d3e3b77bf8523b9a5522c03b2d861f5b80148269f838c4db53cb3f6` |
| Pokémon Y | `a/0/7/4` | update 1.5 | `ed8a7a8e69e24ffb4d55c8ff6912457dbd4b4fb8825f30b1511563ab91ba0881` | `4df53ab9e1a7fa68d0488640e722cda884a6b8299ee322082a0fd341464e2f2e` |
| Pokémon Y | `a/0/8/2` | base (no update override) | `16b9a70f11fd6ac5779a577a16e457b793028be612d279dab28d1abf59349999` | `6f24c4590d3e3b77bf8523b9a5522c03b2d861f5b80148269f838c4db53cb3f6` |

The X/Y `a/0/8/2` source archives are shared. The builder reports 71 translated message variants in `a/0/7/4` and 101 in `a/0/8/2`. It verified 129 and 420 unrelated GARC members unchanged, plus 5,727 and 60 untranslated messages unchanged, respectively. All four candidate hashes were verified after installation. The previous Milestone 3F files were backed up with hashes; details and rollback steps are in the [deployment record](../testing/milestone-3g-deployment.md). Build artifacts remain under ignored `build/` and are not committed.

## Remaining work

- Confirm the two corrected dialogue lines in Pokémon X and Y with female and male protagonists.
- Confirm which asset renders FIGHT and the POKÉMON battle button; inspect relevant texture resources or ExeFS only after locating the runtime-bound resource.
- Verify all battle labels, `ОЗ`/`ОС`, level labels, Chespin, moves, descriptions, and battle messages in both games.
- Review text width, line wrapping, numeric adjacency, and dynamic substitutions. No screen-fit claim is made in this milestone.
- Translate the remaining move descriptions and all other matching HP/PP messages with glossary checks. Do not alter untranslated English resources by blanket replacement.
