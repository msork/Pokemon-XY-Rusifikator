# Milestone 3C Pilot Installation Record

Date: 2026-11-19

This record documents installation of the Russian runtime-test pilot. The 12 translation records remain `machine_draft`; installation is not linguistic approval. AzaharPlus was not launched and no runtime behavior is claimed here.

## Installed files and evidence

AzaharPlus mod root: `%APPDATA%\AzaharPlus\load\mods` (`C:\Users\maxim\AppData\Roaming\AzaharPlus\load\mods`). The game folders use the base Title IDs, even with update 1.5 installed.

| Game | Title ID | Resource | Effective source | Installed SHA-256 | Pre-install state |
|---|---|---|---|---|---|
| Pokémon X | `0004000000055D00` | `a/0/7/4` | Update 1.5 | `603be1e9609cfb27f7a4ef8f781f8ef6160f2d8bfda4d8e9043b69cc1ba57117` | Existing file backed up; prior SHA-256 `c9e9914f04f57cd2e4f38d2ef5ab6eaa0983f7fe0a11d1dbc59dc9ece9c39e20` |
| Pokémon X | `0004000000055D00` | `a/0/8/2` | Base (not present in update 1.5) | `2e5486043cc250d1239f9a5446bf1395550712868923caf1e2662442c62580e0` | Originally absent |
| Pokémon Y | `0004000000055E00` | `a/0/7/4` | Update 1.5 | `603be1e9609cfb27f7a4ef8f781f8ef6160f2d8bfda4d8e9043b69cc1ba57117` | Existing file backed up; prior SHA-256 `c9e9914f04f57cd2e4f38d2ef5ab6eaa0983f7fe0a11d1dbc59dc9ece9c39e20` |
| Pokémon Y | `0004000000055E00` | `a/0/8/2` | Base (not present in update 1.5) | `2e5486043cc250d1239f9a5446bf1395550712868923caf1e2662442c62580e0` | Originally absent |

All four installed file hashes were read back and matched the build manifest. The exact backup files and original existence states are recorded in ignored `build/milestone-3c/installation-backups/2026-11-19-pilot/manifest.json`. The installation record is in ignored `build/milestone-3c/installation-record.json`. These local records and binary backups are not committed.

Only the four listed LayeredFS files were replaced or created. Original game assets, updates, saves, and unrelated mods were not changed. No emulator launch occurred.

## Rollback

Close AzaharPlus before rollback. From the repository root run:

```powershell
python scripts/install_gameplay_pilot.py --rollback
```

The script verifies each target still has the pilot hash before changing anything. It restores the backed-up X/Y `a/0/7/4` files and removes the X/Y `a/0/8/2` files because those were originally absent. If any target has changed since installation, it refuses automatic rollback rather than overwrite that change. The backups are retained.

## Owner runtime checklist

Use AzaharPlus 2126.2-A with update 1.5 enabled. Test X and Y separately and record results separately. Use a fresh or disposable save session; do not overwrite an existing save. The following translations are test drafts, not final approvals.

### Both games

- [ ] Confirm **Options > Text Speed** shows Russian text. This tests update 1.5 `a/0/7/4`, member `75/0`, messages `0`, `3`, `4`, `5`, `6`, and `7`. Check option meanings, labels, Cyrillic, fit, and wrapping.
- [ ] After character creation, inspect the first morning scene at home: `a/0/8/2`, member `55/0`, message `10`. Check the player-name substitution, punctuation, line breaks, and gender-neutral wording.
- [ ] Inspect the mother's send-off before leaving home: member `55/0`, message `13`. Check dialogue progression and control timing.
- [ ] At the first meeting in Vaniville Town, check member `57/0`: message `1` for a male protagonist (Serena variant) or message `2` for a female protagonist (Calem variant). Check the selected character name and place spelling.
- [ ] Inspect Shauna's introduction/arrival dialogue: member `57/0`, messages `3` and `6`. Check speaker, punctuation, line breaks, page/clear events, and transition to the next dialogue.
- [ ] For each item, record whether text is legible, substitutions are correct, no lines clip, control events remain correctly timed, and gameplay proceeds. Capture screenshots for review.

### Pokémon X result

- [ ] Options text-speed menu
- [ ] First morning message
- [ ] Mother's send-off
- [ ] First neighbor meeting, correct protagonist variant
- [ ] Shauna introduction
- [ ] Screenshot/log notes recorded

### Pokémon Y result

- [ ] Options text-speed menu
- [ ] First morning message
- [ ] Mother's send-off
- [ ] First neighbor meeting, correct protagonist variant
- [ ] Shauna introduction
- [ ] Screenshot/log notes recorded

Do not mark records human-approved or runtime-tested until the corresponding linguistic review and owner evidence have been recorded.
