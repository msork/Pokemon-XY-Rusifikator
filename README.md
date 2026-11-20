# Pokemon X/Y Rusifikator

An English-documented project to build a Russian localization for Pokemon X and Pokemon Y. The primary emulator target is AzaharPlus 2126.2-A for Windows. GARC/TextFile extraction, update-1.5 LayeredFS replacement, and Cyrillic rendering for the owner-confirmed alphabet test have been verified in both games. No localization release or bulk translation is available.

## Hosting and license

- Primary repository: https://git.gay/msork/Pokemon-XY-Rusifikator
- GitHub mirror (managed by git.gay): https://github.com/msork/Pokemon-XY-Rusifikator
- WTFPL Version 2 applies only to original project code and documentation. It does not apply to Nintendo/Game Freak assets, game text, fonts, trademarks, third-party dependencies, or external tools. See [LICENSE](LICENSE) and [licensing notes](docs/release/licensing.md).
- The extracted 721-species name glossary has separate Creative Commons Attribution-NonCommercial-ShareAlike 2.5 conditions and attribution. See [Milestone 3B research](docs/research/milestone-3b.md).

Contributions should be made as topic branches through the primary git.gay repository's contribution workflow. Keep code, documentation, comments, logs, commit messages, and issue descriptions in English. Do not submit game dumps, extracted RomFS data, save files, copyrighted derived binaries, secrets, or third-party material without its license. Add tests for tooling changes and include the exact command and results. The GitHub mirror is read-only for this project; do not push there.

## Safety

The four extracted datasets under `workspace/` are read-only local source material, excluded from Git. Original `.3ds` files, update data, saves, extracted resources, and full modified binaries must never enter this repository. Generated inspection data belongs in ignored `build/` or `reports/`. Any eventual release must use a legally reviewed delta format and preserve existing saves and game files.

## Current milestone: 3G

Milestone 3F's pilot was owner-tested in Pokémon X with the female protagonist. The owner then reported two malformed bedroom lines and English battle labels/messages. Milestone 3G traced the PC and mirror lines to `a/0/8/2`, member `0055/00`, messages 1 and 3; the updated Russian candidates preserve the player-name variable, retain `проверил(а)`, and remove only the obsolete gender-selection events. The candidate also applies `ОЗ` (Очки здоровья) and `ОС` (Очки силы) to verified short labels and adds Russian menu labels and the official glossary spelling for Chespin. All new translations remain unapproved and runtime-untested. The `FIGHT` source asset is unresolved; many descriptions and other HP/PP strings remain untranslated.

The 295- and 350-word information-panel tests rendered; the 527-word test produced a blank panel. These are observations, not universal engine limits. The catalog has 35,216 path-classified English variants out of 281,728 variants; the rest remain undetermined or unsupported. See [Milestone 3G findings](docs/research/milestone-3g.md) and the [owner test checklist](docs/testing/milestone-3g-owner-checklist.md) for exact IDs, hashes, candidate paths, and open work.

To regenerate the ignored Milestone 3G candidate and run the tests, use the four local `workspace/` datasets and source catalog:

```powershell
python scripts/build_milestone3g_fixes.py
python scripts/build_milestone3g_terms.py
python -X utf8 scripts/validate_translation_data.py --translations translations/early-game.jsonl --translations translations/milestone3g-battle.jsonl
python scripts/build_gameplay_pilot.py --include-machine-drafts --translations translations/early-game.jsonl --translations translations/milestone3g-battle.jsonl --milestone 3G --output build/milestone-3g/candidate
python scripts/verify_build_manifest.py build/milestone-3g/candidate/manifest.json
python -m unittest discover -s tests -v
```

The candidate builder uses update 1.5 for `a/0/7/4` and the base resource for `a/0/8/2` where no update override exists. The four test archives are installed in the X/Y LayeredFS folders, with verified backups and rollback under ignored `build/milestone-3g/`. They are not release files. AzaharPlus has not been launched for Milestone 3G, and saves were not modified. See the [deployment record](docs/testing/milestone-3g-deployment.md) for hashes and owner checks.

## Project layout

- `docs/architecture/`: pipeline and component boundaries.
- `docs/specifications/`: inventory, extraction, and translation data contracts.
- `docs/research/`: evidence and source references.
- `docs/testing/`: automated and emulator test plans.
- `docs/release/`: packaging, licensing, contribution, and recovery requirements.
- `scripts/`, `src/`: read-only inspection and deterministic localization tooling.
- `tests/`: synthetic-fixture tests; no original assets are included.
- `glossary/`, `translations/`: project-authored terminology and translation records.
- `workspace/`: local read-only RomFS datasets; never stage or commit.
