# Repository Instructions

- Write all developer communication, documentation, code comments, and logs in English. In-game translations belong in Russian.
- Treat `workspace/**` as read-only source data. Never edit, delete, stage, or commit extracted game files.
- Write generated data only under `build/`, `reports/`, or another explicitly generated directory.
- Do not commit game assets, extracted text archives, saves, game images, or derived full binaries. Distributable work must use a legally reviewed delta format.
- Keep tooling deterministic and document evidence, assumptions, and unverified behavior.
- Primary runtime target: AzaharPlus 2126.2-A for Windows 11. Do not assume standard Azahar configuration paths or behavior; record local evidence and keep X/Y runtime results distinct.
- Never claim runtime testing without a recorded AzaharPlus test.
- Primary Git remote is `https://git.gay/msork/Pokemon-XY-Rusifikator`; GitHub is an externally managed mirror. Never push directly to GitHub or force-push. Check remote state before pushing.
- WTFPL Version 2 applies only to original project code and documentation; it does not license Nintendo/Game Freak assets or third-party dependencies.
