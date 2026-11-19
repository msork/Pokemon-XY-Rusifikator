# Milestone 2D: Cyrillic Runtime Validation Setup

Date: 2026-11-19. This records the Russian test installation only. The games have not been launched for this test; Cyrillic rendering remains unverified.

## Pre-install validation

Both generated archives were read from `build/milestone-2c/russian/` and matched SHA-256 `d2fbd6bebd5b7764b2e4ec2077d7f3ed7cbc343dc60bf3b1b73933db24c572fa`; each is 2,388,484 bytes. GARC parsing found 151 members. TextFile parsing of member 85/0 found message 25 equal to `Привет!`, with no control tokens. The rebuilt archive was compared against its update 1.5 source: all 150 non-target members are byte-identical. X and Y outputs passed the same checks.

Before installation, both target files contained the verified ASCII control hash `252f90a4eca1c16dac0f0a32758e867ec7b9dbb322c00f975e3d7fc6ab233d0c`. AzaharPlus was not running during the replacement.

## Installed files and backups

Only the following two mod files were replaced:

- `%APPDATA%\AzaharPlus\load\mods\0004000000055D00\romfs\a\0\7\4` (Pokémon X)
- `%APPDATA%\AzaharPlus\load\mods\0004000000055E00\romfs\a\0\7\4` (Pokémon Y)

Each installed file was rehashed after replacement: SHA-256 `d2fbd6bebd5b7764b2e4ec2077d7f3ed7cbc343dc60bf3b1b73933db24c572fa`, size 2,388,484 bytes.

The pre-install ASCII files are backed up in the ignored local directory `build/milestone-2d/install-backups/20261119T182134Z/`:

- `pokemon-x-a074.before-russian`
- `pokemon-y-a074.before-russian`

Each backup hash is `252f90a4eca1c16dac0f0a32758e867ec7b9dbb322c00f975e3d7fc6ab233d0c`. Restore only these two files by closing AzaharPlus and running the following from the project root:

```powershell
$backup = Join-Path (Get-Location) 'build\milestone-2d\install-backups\20261119T182134Z'
$xTarget = Join-Path $env:APPDATA 'AzaharPlus\load\mods\0004000000055D00\romfs\a\0\7\4'
$yTarget = Join-Path $env:APPDATA 'AzaharPlus\load\mods\0004000000055E00\romfs\a\0\7\4'
Copy-Item -LiteralPath (Join-Path $backup 'pokemon-x-a074.before-russian') -Destination $xTarget -Force
Copy-Item -LiteralPath (Join-Path $backup 'pokemon-y-a074.before-russian') -Destination $yTarget -Force
```

No source game assets, updates, saves, or unrelated mods were changed. No emulator setting was changed.

## Required user runtime check

Launch X and Y separately in AzaharPlus 2126.2-A with update 1.5 enabled. Check the initial language-selection screen for `Привет!`; report the visible result for each game and provide screenshots/logs if possible. Do not interpret this as successful Cyrillic support until the glyphs are visibly correct. If glyphs render incorrectly, record whether they appear as boxes, blanks, or another substitute. After confirmation, investigate uppercase/lowercase coverage, Ё/ё, punctuation, mixed Latin/numbers, line wrapping, and fonts used by the screen before any bulk translation work.

## Subsequent runtime confirmation

After this installation record, the project owner confirmed that both X and Y correctly display `Привет!` in AzaharPlus 2126.2-A with update 1.5. This verifies the greeting only. Milestone 3A prepares broader glyph and layout probes; those new variants have not been installed or launched. See [Milestone 3A findings](milestone-3a.md).
