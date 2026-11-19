# Pokemon X/Y Rusifikator

An English-documented project to build a Russian localization for Pokemon X and Pokemon Y. The primary emulator target is AzaharPlus 2126.2-A for Windows. The project has verified GARC/TextFile extraction, update-1.5 LayeredFS replacement, and the initial Cyrillic greeting `Привет!` in both games. No localization release or bulk translation is available yet.

## Hosting and license

- Primary repository: https://git.gay/msork/Pokemon-XY-Rusifikator
- GitHub mirror (managed by git.gay): https://github.com/msork/Pokemon-XY-Rusifikator
- License: WTFPL Version 2, applying only to original project code and documentation in this repository. It does not apply to Nintendo/Game Freak assets, game text, fonts, trademarks, third-party dependencies, or external tools. See [LICENSE](LICENSE) and [licensing notes](docs/release/licensing.md).

Contributions should be made as topic branches and submitted through the primary git.gay repository's contribution workflow. Keep code, documentation, comments, logs, commit messages, and issue descriptions in English. Do not submit game dumps, extracted RomFS data, save files, copyrighted derived binaries, secrets, or third-party material without its license. Add tests for tooling changes and include the exact command and results. The GitHub mirror is read-only for this project; do not push there.

## Safety

The four extracted datasets under `workspace/` are read-only local source material, excluded from Git. Original `.3ds` files, update data, saves, extracted resources, and full modified binaries must never enter this repository. Generated inspection data belongs in ignored `build/` or `reports/`. Any eventual release must use a legally reviewed delta format and preserve existing saves and game files.

## Current milestone: 3A

Read-only Gen VI GARC inspection, lossless TextFile serialization, safe replacement, CFNT CMAP/CWDH inspection, static glyph/length validation, and disposable AzaharPlus rendering probes are implemented. The commands below write extracted data and test patches only under ignored `build/`:

```powershell
python scripts/inspect_assets.py
python scripts/verify_text_roundtrips.py
python scripts/build_russian_poc.py
python scripts/build_language_screen_poc.py
python scripts/build_render_validation.py
python -m unittest discover -s tests -v
```

`workspace/` must exist locally and contain the four datasets specified in the project instructions. The Milestone 3A glyph-coverage and long-text probes are not installed automatically. The user confirmed `Привет!` displays correctly in X/Y; broader character and layout coverage still requires runtime testing. See [Milestone 2A findings](docs/research/milestone-2a.md), [Milestone 2B findings](docs/research/milestone-2b.md), [Milestone 2C findings](docs/research/milestone-2c.md), [Milestone 2D findings](docs/research/milestone-2d.md), [Milestone 3A findings](docs/research/milestone-3a.md), and the [AzaharPlus test plan](docs/testing/azaharplus.md).

## Project layout

- `docs/architecture/`: pipeline and component boundaries.
- `docs/specifications/`: inventory, extraction, and translation data contracts.
- `docs/research/`: evidence and source references.
- `docs/testing/`: automated and emulator test plans.
- `docs/release/`: packaging, licensing, contribution, and recovery requirements.
- `scripts/`, `src/`: read-only inspection and deterministic localization tooling.
- `tests/`: synthetic-fixture tests; no original assets are included.
- `glossary/`, `translations/`: project-authored terminology and future translation records.
- `workspace/`: local read-only RomFS datasets; never stage or commit.
