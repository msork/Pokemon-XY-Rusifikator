# Milestone 3F Installation Record

Installation: 2026-11-19 local time (backup directory timestamp `20261120T044138Z`)

The four Milestone 3E archives were checked against `build/milestone-3e/candidate/manifest.json`, including a second reproducible build, before installation. AzaharPlus 2126.2-A was not running at inspection/install time and was not launched. All 139 strings remain draft/runtime-test content; none were marked human-approved.

## AzaharPlus paths and results

Observed user-data directory: `C:\Users\maxim\AppData\Roaming\AzaharPlus`.

LayeredFS root: `C:\Users\maxim\AppData\Roaming\AzaharPlus\load\mods`.

All four prior target files existed. The installer copied each to the timestamped backup, recorded its original SHA-256, checked the copy, and then replaced only those four files. The update a/0/7/4 assets are loaded through each base game Title ID; a/0/8/2 uses the base resource because update 1.5 contains no override.

| Game / Title ID | Resource | Installed SHA-256 | Size | Original SHA-256 |
|---|---|---|---:|---|
| Pokémon X / `0004000000055D00` | `a/0/7/4` (update 1.5) | `8febfef4d41f9b11f8c705cdd795d0eab7f3cdec6880a8e3bb4cac3755a56108` | 2,388,912 | `603be1e9609cfb27f7a4ef8f781f8ef6160f2d8bfda4d8e9043b69cc1ba57117` |
| Pokémon X / `0004000000055D00` | `a/0/8/2` (base) | `e8dfe6f963a3c8ee8855148d4d4209d40bbab687598b925ed791ea36026b2e6f` | 1,304,424 | `2e5486043cc250d1239f9a5446bf1395550712868923caf1e2662442c62580e0` |
| Pokémon Y / `0004000000055E00` | `a/0/7/4` (update 1.5) | `8febfef4d41f9b11f8c705cdd795d0eab7f3cdec6880a8e3bb4cac3755a56108` | 2,388,912 | `603be1e9609cfb27f7a4ef8f781f8ef6160f2d8bfda4d8e9043b69cc1ba57117` |
| Pokémon Y / `0004000000055E00` | `a/0/8/2` (base) | `e8dfe6f963a3c8ee8855148d4d4209d40bbab687598b925ed791ea36026b2e6f` | 1,304,424 | `2e5486043cc250d1239f9a5446bf1395550712868923caf1e2662442c62580e0` |

Independent read-back verification passed for all four installed files against the build manifest and all four backup copies. `python scripts/verify_milestone3f_installation.py` reports `PASS`, 4 targets verified, no save changes, and no emulator launch. The full local record is ignored at `build/milestone-3f/installation-record.json`; backup files and their manifest are under `build/milestone-3f/installation-backups/20261120T044138Z/`. No game/update assets, saves, or unrelated mods were changed.

## Rollback

Close AzaharPlus first. From the project root in PowerShell, run:

```powershell
python scripts/install_milestone3f.py --rollback
```

The rollback command preflights all four live hashes and every backup before restoring anything. It refuses to proceed if an installed target changed after this installation or if any backup hash is wrong. It restores the four exact prior files and verifies their hashes afterward. The backup directory is retained. The full automated suite passed (**46 tests**); installer tests exercised successful restoration, removal of a target recorded as originally absent, preservation of an unrelated mod, corrupted-candidate rejection, and refusal to overwrite a changed target. The live rollback has not been run; the installed patch is left in place for owner testing.

## Runtime status and open issues

No runtime result is claimed for the installed Milestone 3E patch. The earlier owner-confirmed Milestone 3C test was Pokémon X with a female protagonist and covered the Options, mother, Calem, and Shauna contexts. It does not validate the new Aquacorde, starter-menu, battle, or expanded dialogue strings; the installed files have not been launched since replacement.

Open issues for review during testing:

- Protagonist-creation prompts were not found in the current English TextFile corpus; the screen/resource remains unknown.
- Gender-dependent control sequences such as `0010 0003 1100 00FF 0202` and `0010 0003 1100 00FF 0403` are preserved but not semantically decoded.
- The source catalog contains U+FFFD replacement characters in some English apostrophes/`Pokémon` spellings. This is an extraction/decoding issue; the checklist shows the decoded evidence without guessing the original character.

See the concise [owner test checklist](milestone-3f-owner-checklist.md) and the full [source-linked Milestone 3E checklist](milestone-3e-runtime-checklist.md).
