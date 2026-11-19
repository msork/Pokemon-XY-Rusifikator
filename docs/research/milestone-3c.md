# Milestone 3C: Playable Gameplay Pilot Build

Date: 2026-11-19. This milestone builds local test candidates only. Nothing was copied into AzaharPlus, and AzaharPlus was not launched.

## Translation review

All twelve pilot strings were reviewed for meaning, Russian grammar, tone, glossary use, and available context. Changes made in this milestone:

- The mother's morning question was made gender-neutral so the line works with either player character.
- Shauna's greeting was rephrased as natural spoken Russian; punctuation is retained.
- The Normal text-speed label uses a clear Russian option label.
- The `Vaniville`, Serena, Calem, and Shauna spellings remain provisional glossary terms because this project has not verified a Russian X/Y localization authority for those names.

Control words, variable arguments, message IDs, and line-break events are taken from the source catalog and checked against the selected source bytes during the build. Each record remains `machine_draft` with `review_state: assistant_reviewed_pending_human`. This records assistant linguistic review only; it is not human approval, runtime validation, or owner approval. The builder refuses machine drafts unless `--include-machine-drafts` is explicitly supplied. The manifest labels the result an unapproved test candidate.

## Effective resources and source selection

For each game, the builder selects a present update resource in preference to base. Owner runtime tests previously confirmed that a replacement for update 1.5 `a/0/7/4` loads through the base Title ID's LayeredFS directory in both games. The update contains no `a/0/8/2`, so the builder selects the base archive for dialogue. The absence of an update file is local file evidence; the game's use of these specific dialogue lines has not been runtime-tested in this milestone.

| Game | Resource | Selected source | Members | Messages in resource |
|---|---|---|---:|---:|
| X and Y | `a/0/7/4` | `update-1.5` | 151 | 27,607 |
| X and Y | `a/0/8/2` | `base` | 424 | 7,607 |

The builder reads each game's own workspace tree, checks the source archive hash and each message's source-word hash, requires byte-exact no-change GARC rebuilding, and writes outputs only under ignored `build/milestone-3c/`. It then reparses the rebuilt GARC, verifies output round-trip identity, confirms all GARC member coordinates, verifies unrelated members and untranslated messages, and checks requested replacement words and original controls.

## Build results

The deterministic command is:

```powershell
python scripts/build_pilot_translations.py
python scripts/validate_translation_data.py
python scripts/build_gameplay_pilot.py --include-machine-drafts
```

The explicit flag permits local packaging of the still-unapproved machine drafts for a future owner test. It does not approve or install them.

| Game | Resource | Source SHA-256 | Output SHA-256 | Size | Applied records | Unrelated members verified unchanged |
|---|---|---|---:|---:|---:|---:|
| X | `a/0/7/4` | `ed8a7a8e69e24ffb4d55c8ff6912457dbd4b4fb8825f30b1511563ab91ba0881` | `603be1e9609cfb27f7a4ef8f781f8ef6160f2d8bfda4d8e9043b69cc1ba57117` | 2,388,528 | 6 | 150 |
| Y | `a/0/7/4` | `ed8a7a8e69e24ffb4d55c8ff6912457dbd4b4fb8825f30b1511563ab91ba0881` | `603be1e9609cfb27f7a4ef8f781f8ef6160f2d8bfda4d8e9043b69cc1ba57117` | 2,388,528 | 6 | 150 |
| X | `a/0/8/2` | `16b9a70f11fd6ac5779a577a16e457b793028be612d279dab28d1abf59349999` | `2e5486043cc250d1239f9a5446bf1395550712868923caf1e2662442c62580e0` | 1,306,148 | 6 | 422 |
| Y | `a/0/8/2` | `16b9a70f11fd6ac5779a577a16e457b793028be612d279dab28d1abf59349999` | `2e5486043cc250d1239f9a5446bf1395550712868923caf1e2662442c62580e0` | 1,306,148 | 6 | 422 |

X and Y were built independently from their own source trees. The selected source files are byte-identical across games, and each corresponding output hash matches. `a/0/7/4` modifies one TextFile member and preserves the other 150; 48 other messages in the modified member were verified unchanged. `a/0/8/2` modifies two TextFile members and preserves the other 422; 79 other messages in the modified members were verified unchanged. The manifest records these checks and every translated stable ID.

Build files are at `build/milestone-3c/pokemon-x/romfs/` and `build/milestone-3c/pokemon-y/romfs/`. Exact file hashes, source paths, update selection, message IDs, and runtime/installation flags are in ignored `build/milestone-3c/manifest.json`. No generated archive is tracked by Git.

## Existing mod backups

The actual AzaharPlus profile was inspected read-only at `%APPDATA%\AzaharPlus\load\mods`. Existing X and Y `a/0/7/4` files were copied into ignored `build/milestone-3c/preinstall-backups/current/` and SHA-256 verified. Both are the prior `record-350-words` test files:

- X `0004000000055D00/romfs/a/0/7/4`: `c9e9914f04f57cd2e4f38d2ef5ab6eaa0983f7fe0a11d1dbc59dc9ece9c39e20`
- Y `0004000000055E00/romfs/a/0/7/4`: `c9e9914f04f57cd2e4f38d2ef5ab6eaa0983f7fe0a11d1dbc59dc9ece9c39e20`
- Neither mod directory had `a/0/8/2` before this milestone.

The verified copies and existence records are in `build/milestone-3c/preinstall-backups/current/manifest.json`. These backups are local and ignored; they are not part of the commit. If the active mods change before a future installation, make a fresh backup then.

## Future installation and rollback procedure

No installation was performed. When the owner chooses to test these candidates:

1. Close AzaharPlus and leave the original game/update files and saves untouched.
2. In `%APPDATA%\AzaharPlus\load\mods\0004000000055D00\romfs\`, back up the current `a\0\7\4` file and record its SHA-256. Create the `a\0` parent directories for `a\0\8\2` only if they are missing; preserve existing directories and unrelated files.
3. Copy `build\milestone-3c\pokemon-x\romfs\a\0\7\4` and `a\0\8\2` to those exact X paths.
4. Repeat for Y under `0004000000055E00`, using only the Y build directory.
5. Hash all four installed files and compare with the table above. Leave unrelated mod files unchanged.
6. Launch X with update 1.5 enabled and inspect the checklist below. Close it, then repeat independently for Y. Use a fresh or disposable save session; do not overwrite an existing save.

Rollback after the test: restore each backed-up `a\0\7\4` file and verify it matches its pre-test hash. Since `a\0\8\2` was absent before this milestone, remove only the newly created X/Y `a\0\8\2` files. Keep all unrelated files and folders. The tested rollback helper is `src/rebuilding/installation.py`; its tests exercise exact-file restoration and removal of only previously absent targets.

PowerShell copy commands for that future test (run only when ready to install):

```powershell
$project = 'C:\Projects\Pokemon-XY-Rusifikator'
$modRoot = Join-Path $env:APPDATA 'AzaharPlus\load\mods'
$x = Join-Path $modRoot '0004000000055D00\romfs'
$y = Join-Path $modRoot '0004000000055E00\romfs'
New-Item -ItemType Directory -Force (Join-Path $x 'a\0\7') | Out-Null
New-Item -ItemType Directory -Force (Join-Path $x 'a\0\8') | Out-Null
New-Item -ItemType Directory -Force (Join-Path $y 'a\0\7') | Out-Null
New-Item -ItemType Directory -Force (Join-Path $y 'a\0\8') | Out-Null
Copy-Item -LiteralPath (Join-Path $project 'build\milestone-3c\pokemon-x\romfs\a\0\7\4') -Destination (Join-Path $x 'a\0\7\4') -Force
Copy-Item -LiteralPath (Join-Path $project 'build\milestone-3c\pokemon-x\romfs\a\0\8\2') -Destination (Join-Path $x 'a\0\8\2') -Force
Copy-Item -LiteralPath (Join-Path $project 'build\milestone-3c\pokemon-y\romfs\a\0\7\4') -Destination (Join-Path $y 'a\0\7\4') -Force
Copy-Item -LiteralPath (Join-Path $project 'build\milestone-3c\pokemon-y\romfs\a\0\8\2') -Destination (Join-Path $y 'a\0\8\2') -Force
Get-FileHash (Join-Path $x 'a\0\7\4'), (Join-Path $x 'a\0\8\2'), (Join-Path $y 'a\0\7\4'), (Join-Path $y 'a\0\8\2') -Algorithm SHA256
```

## Owner runtime checklist

Record X and Y separately. Do not mark any record tested until the corresponding game shows the expected result.

| Screen/progression | Source message | What to inspect |
|---|---|---|
| Options > Text Speed | `a/0/7/4`, member `75/0`, messages 0, 3–7 | Settings heading, text-speed heading, three option labels, explanatory line; check alignment, fit, and wrapping. |
| First morning at home, after character creation | `a/0/8/2`, member `55/0`, message 10 | Player-name variable, punctuation, gender-neutral question, clear/newline timing. |
| Mother's send-off before leaving home | `a/0/8/2`, member `55/0`, message 13 | Natural dialogue, newline placement, text-clear timing. |
| First meeting in Vaniville Town | `a/0/8/2`, member `57/0`, message 1 for a male protagonist or 2 for a female protagonist | Correct Serena/Calem variant, speaker name, place spelling, line breaks. |
| Shauna arrives with the neighbor group | `a/0/8/2`, member `57/0`, messages 3 and 6 | Dialogue sequence, punctuation, page breaks, clear events, text flow. |

For every entry, check Cyrillic, variable substitution, text wrapping, clipping, control-event timing, and whether the game reaches the next dialogue/menu state. Capture screenshots and emulator logs for each title separately. Runtime success remains unverified until the owner reports it.

## Licensing and scope

The Bulbapedia-derived 721-species dataset remains in `glossary/pokemon_species_ru.json` with separate CC BY-NC-SA 2.5 attribution and restrictions. The pilot binary build does not include or relicense that dataset. WTFPL applies only to original project code and documentation. These local full-archive build candidates are not distributable; any release requires legal review and a delta format.
