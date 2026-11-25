# Repository Instructions

- Write all developer communication, documentation, code comments, and logs in English. In-game translations belong in Russian.
- Treat `workspace/**` as read-only source data. Never edit, delete, stage, or commit extracted game files.
- Write generated data only under `build/`, `reports/`, or another explicitly generated directory.
- Do not commit game assets, extracted text archives, saves, game images, or derived full binaries. Distributable work must use a legally reviewed delta format.
- Keep tooling deterministic and document evidence, assumptions, and unverified behavior.
- Primary runtime target is the installed AzaharPlus AppImage on Linux. Confirm the build, data directory, and LayeredFS root against local evidence. Keep Pokémon X and Pokémon Y runtime results distinct. Preserve historical Windows deployment and rollback records.
- Never claim runtime testing without a recorded AzaharPlus test.
- Primary Git remote is `git@git.gay:msork/Pokemon-XY-Rusifikator.git` over SSH; GitHub is an externally managed mirror. Require SSH authentication, never push directly to GitHub, and never force-push. Check remote state before every push and stop if it contains unrelated history.
- After completing and testing an authorized milestone, commit the verified source/documentation changes and push the current branch to git.gay automatically. Never push unfinished work, extracted assets, or copyrighted game assets.
- WTFPL Version 2 applies only to original project code and documentation; it does not license Nintendo/Game Freak assets or third-party dependencies.
