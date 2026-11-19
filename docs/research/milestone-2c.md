# Milestone 2C: AzaharPlus LayeredFS Runtime Debugging

Date: 2026-11-18. Source assets remain read-only under `workspace/`; test archives are generated only under ignored `build/`.

## Runtime evidence supplied and locally inspected

The project owner supplied screenshots from Pokémon X and Pokémon Y showing the initial language-selection screen, including the bottom-right `Ver. 1.5` label. The owner reports that both games still showed that label after installing the Milestone 2B Russian probe.

The installed files exist at:

- `%APPDATA%\AzaharPlus\load\mods\0004000000055D00\romfs\a\0\7\4`
- `%APPDATA%\AzaharPlus\load\mods\0004000000055E00\romfs\a\0\7\4`

Each is 2,388,484 bytes and has SHA-256 `ebfa2db696d0e7b2c5bcd2b6fe20527ff395e51590b605b4250f30e8ce535cae`, identical to the Milestone 2B generated file. Thus the tested mod files were copied to both expected base-Title-ID folders without byte changes.

The inspected `azahar_log.old.txt` records Program IDs `0004000000055D00` and `0004000000055E00`. It has no `LayeredFS`, `load/mods`, or RomFS replacement entries. The current `azahar_log.txt` was empty at inspection. These logs prove the emulator launched both base titles, but do not prove that the LayeredFS files were mounted. The screenshots show the update version marker, and the source data places that marker in the update archive; no separate update Title ID appears in the captured launch records.

## Exact screen resource and cause of inconclusive Milestone 2B test

Read-only extraction found the screenshot strings in `a/0/7/4`, GARC member 85/0:

| Text | Message ID | Presence |
|---|---:|---|
| Language-selection help panel | 1 | Base and update 1.5 |
| `Play Pokémon X in` / `Play Pokémon Y in` | 4 / 5 | Base and update 1.5 |
| Language names | 6-12 | Base and update 1.5 |
| Visible bottom-right `Ver. 1.5` | 25 | Update 1.5 only |

Base member 85 has 25 records (IDs 0-24); update 1.5 member 85 has 26 records (IDs 0-25), with ID 25 equal to `Ver. 1.5`. This strongly identifies an update-only message resource matching the screenshot label. It means the text need not be hardcoded in the executable; the runtime source is confirmed only when the ASCII control visibly changes it. The screen's other text is also present in this member, and the inspected screenshot strings were not found in the separate script archive `a/0/8/2`.

The earlier Milestone 2B probe edited a different duplicate string, member 35/0 message 22. That data is present in the update archive, but the initial-screen bottom-right label comes from member 85/0 message 25. Therefore, the unchanged screen after that probe does not show that LayeredFS failed. Whether member 35/0 message 22 is used elsewhere remains unverified.

## New controlled probes

`python scripts/build_language_screen_poc.py` makes a pair of variants from each game's update 1.5 `a/0/7/4`:

| Variant | Message 85/0 ID 25 replacement | X/Y SHA-256 |
|---|---|---|
| ASCII control | `ASCII 2C` | `252f90a4eca1c16dac0f0a32758e867ec7b9dbb322c00f975e3d7fc6ab233d0c` |
| Cyrillic probe | `Привет!` | `d2fbd6bebd5b7764b2e4ec2077d7f3ed7cbc343dc60bf3b1b73933db24c572fa` |

All outputs remain 2,388,484 bytes. Reparse validation confirms the replacement at message 25 and preserves all 150 non-target GARC members byte-for-byte. The selected message has no control tokens or placeholders; ID and structure remain stable. Each generated file is separate under `build/milestone-2c/<variant>/<game>/<base-title-id>/romfs/a/0/7/4`.

Test the ASCII control first. If `ASCII 2C` appears, the emulator read the patched update-only resource and the remaining Cyrillic test isolates font mapping/rendering. If `Ver. 1.5` remains, the run still does not establish that this target was overlaid; inspect the actual title-specific mod folder, competing mods, whether the emulator was restarted, and the effective update resource. Exact manual steps and backup/restore commands are in [the AzaharPlus test plan](../testing/azaharplus.md).

## Verification and limits

- `python -m unittest discover -s tests -v`: 11 tests passed, including the new ASCII probe rebuild check.
- `python scripts/build_language_screen_poc.py`: four X/Y variant archives built; the script reparses each output, checks message 25, and verifies the unchanged-member set.
- `python scripts/verify_text_roundtrips.py`: retained Milestone 2B full-corpus verification for all 1,452 TextFile members.
- On 2026-11-18, the ASCII control archive was installed to both AzaharPlus mod targets. The installed X and Y hashes each verified as `252f90a4eca1c16dac0f0a32758e867ec7b9dbb322c00f975e3d7fc6ab233d0c`, size 2,388,484 bytes. The emulator was not launched by this operation.
- Before replacement, the previous installed file for each title was backed up under `build/milestone-2c/install-backups/20261118T215421Z/`. Each backup hash is `ebfa2db696d0e7b2c5bcd2b6fe20527ff395e51590b605b4250f30e8ce535cae`.
- No Cyrillic rendering or LayeredFS runtime success is claimed. Await the user's runtime observation of the ASCII control on both games.

Subsequent results supersede that status: the owner confirmed `ASCII 2C` appeared in both X and Y, then confirmed `Привет!` rendered correctly in both with update 1.5 enabled. Those reports are recorded in [Milestone 2D](milestone-2d.md) and [Milestone 3A](milestone-3a.md). The broader character matrix remains untested.
