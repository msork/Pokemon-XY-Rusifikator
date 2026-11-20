# Milestone 3G Deployment Record

## Candidate and Git verification

Commit `b9f33aa` was fetched from the primary SSH remote `git@git.gay:msork/Pokemon-XY-Rusifikator.git` and verified as the current `main` tip before deployment preparation. The independently stored candidate manifest passed `scripts/verify_build_manifest.py`; all four archive hashes match the candidate files. The X/Y resources have these hashes:

| Resource | Effective source | Candidate SHA-256 |
|---|---|---|
| `a/0/7/4` | Update 1.5 | `4df53ab9e1a7fa68d0488640e722cda884a6b8299ee322082a0fd341464e2f2e` |
| `a/0/8/2` | Base; no update override | `6f24c4590d3e3b77bf8523b9a5522c03b2d861f5b80148269f838c4db53cb3f6` |

Pokémon X uses base Title ID `0004000000055D00`; Pokémon Y uses `0004000000055E00`. Each game receives only those two archives at its own LayeredFS path.

## Installer and recovery

`scripts/install_milestone3g.py --install` revalidates manifest paths, title IDs, effective resource versions, candidate sizes, and SHA-256 values before touching the mod directory. It snapshots exactly the four target paths under `build/milestone-3g/installation-backups/<UTC timestamp>/`, records hashes and originally absent paths, verifies backup copies, then replaces each target through a temporary file and checks the installed hash. It does not traverse or alter unrelated mods, game/update assets, or saves. The ignored installation record is `build/milestone-3g/installation-record.json`.

## Installation result

Installed on 2026-11-20 after SSH trust was usable, remote `main` was fetched at `b9f33aa`, and the four candidate hashes passed manifest verification. AzaharPlus was not running and was not launched. The observed user-data root was `C:\Users\maxim\AppData\Roaming\AzaharPlus`; mod root: `C:\Users\maxim\AppData\Roaming\AzaharPlus\load\mods`.

All four target files existed before installation. Their backups are in `build/milestone-3g/installation-backups/20261120T171518Z/` and were hash-verified. The previous Milestone 3F hashes were `8febfef4d41f9b11f8c705cdd795d0eab7f3cdec6880a8e3bb4cac3755a56108` for `a/0/7/4` and `e8dfe6f963a3c8ee8855148d4d4209d40bbab687598b925ed791ea36026b2e6f` for `a/0/8/2`, identical in X and Y. The installed files match the candidate hashes in the table above. `python scripts/verify_milestone3g_installation.py` passed for all four installed files and all four backups. No saves, original assets, update assets, or unrelated mods were changed.

The rollback command is:

```powershell
python scripts/install_milestone3g.py --rollback
```

Rollback verifies every installed target and backup before restoring anything. It restores targets that previously existed and removes only listed targets that were absent before installation. The backups remain available afterward. Automated tests exercise this flow with existing and absent targets and an unrelated mod fixture; they do not roll back the owner's live installation.

## Runtime test checklist

Run Pokémon X and Pokémon Y separately with update 1.5 enabled. Keep the existing save unchanged; use a disposable or recoverable test save. Record the game, protagonist gender, visible text, wrapping, and screenshot for each check.

1. In the Vaniville bedroom, interact with the PC: verify the player name is followed by a space, with no extra `Ты`, and the line uses the gender-neutral `проверил(а)` wording.
2. Interact with the mirror: verify `…И ты уже без пижамы!` appears without stray characters.
3. Check field and battle menus, including `СУМКА`, `БЕГ`, `ПОКЕМОНЫ`, and any remaining English labels. `FIGHT` is not sourced from the identified TextFile corpus and may remain English.
4. Inspect party, move, and battle screens for `ОЗ`, `ОС`, `Ур.`, and `ДО СЛ. УР.`. Check that numeric values and mechanics remain unchanged and that labels do not overlap.
5. Check Chespin's displayed name for `Чеспин`.
6. Record which battle messages changed and which labels remain English; do not infer a source ID from the screen alone.

All strings in this installed candidate are drafts for runtime testing, not linguistically approved release translations. Installation alone is not evidence that they render correctly. Record X and Y results separately. No Milestone 3G AzaharPlus launch or runtime pass is claimed by this document.
