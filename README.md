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

## Current milestone: 3E

The owner confirmed the Milestone 3C pilot in Pokémon X with the female protagonist: Options, mother's dialogue, Calem, and Shauna appeared. Pokémon Y and Serena remain untested for that pilot. Russian alphabet rendering, including Ё/ё, was owner-confirmed in both games. The 295-word and 350-word rendering tests displayed; the 527-word test produced a blank information panel. These are observations, not universal engine limits. Milestone 3E now tracks 139 bounded source variants (127 draft, 12 machine draft), covering 0.394707% of the 35,216 path-classified English variants. All remain unapproved. New candidate archives are generated but not installed or runtime-tested. Character-creation prompt resources and much of the English corpus remain unresolved.

With the four local `workspace/` datasets present, regenerate the ignored source catalog, selected draft translations, coverage report, and local candidates, then run unit tests:

```powershell
python scripts/build_translation_catalog.py
python scripts/build_milestone3e_translations.py
python scripts/validate_translation_data.py --translations translations/early-game.jsonl
python scripts/report_translation_coverage.py --translations translations/early-game.jsonl --output-dir reports/milestone-3e
python scripts/generate_milestone3e_checklist.py --translations translations/early-game.jsonl
python scripts/build_gameplay_pilot.py --include-machine-drafts --translations translations/early-game.jsonl --milestone 3E --output build/milestone-3e/candidate
python scripts/verify_build_manifest.py build/milestone-3e/candidate/manifest.json
python -m unittest discover -s tests -v
```

The explicit build flag permits packaging of unapproved translations for a future owner test; it does not install the files. The source catalog and rebuilt full archives contain copyrighted game text and remain under ignored build directories. Another 246,512 variants are still language-undetermined, 66,666 member payloads are not parsed as TextFiles, and two oversized archives were skipped; the full English corpus remains unknown. See [Milestone 3E findings](docs/research/milestone-3e.md) and the [scene-ordered owner runtime checklist](docs/testing/milestone-3e-runtime-checklist.md), along with the [Milestone 3D pipeline and findings](docs/research/milestone-3d.md), [Milestone 3C findings and build hashes](docs/research/milestone-3c.md), [Milestone 3B findings and attribution](docs/research/milestone-3b.md), [Milestone 2A findings](docs/research/milestone-2a.md), [Milestone 2B findings](docs/research/milestone-2b.md), [Milestone 2C findings](docs/research/milestone-2c.md), [Milestone 2D findings](docs/research/milestone-2d.md), [Milestone 3A findings](docs/research/milestone-3a.md), and [AzaharPlus test plan](docs/testing/azaharplus.md).

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
