# AzaharPlus 2126.2-A Test Plan

## Target profile

- Windows installation: `C:\Users\maxim\Games\azaharplus-2126.2-A-windows`
- Observed user data: `%APPDATA%\AzaharPlus`
- Pokémon X mod root: `%APPDATA%\AzaharPlus\load\mods\0004000000055D00\romfs`
- Pokémon Y mod root: `%APPDATA%\AzaharPlus\load\mods\0004000000055E00\romfs`
- Run with each game's update 1.5 enabled. LayeredFS folders use the base game Title IDs.

## Milestone 2C language-selection screen probe

The user-provided X and Y screenshots show the initial language-selection interface. Source inspection locates the visible screen strings in `a/0/7/4`, GARC member 85/0, including message 1 (help panel), message 4 (game title), and messages 6-12 (language names). The visible bottom-right `Ver. 1.5` is message 25 in that same member in update 1.5. Base member 85 has messages 0-24 and no message 25. This explains why the earlier probe of member 35/0 message 22 could not change the screenshot: it targeted a separate duplicate label that is not the one rendered on this screen.

The new builder creates two variants from the update 1.5 archive for both games:

- ASCII control: `ASCII 2C`
- Russian rendering probe: `Привет!`

Both replace only message 25 in member 85/0, retain its empty control-code signature and message ID, and preserve the other 150 GARC members byte-for-byte. Generated outputs are under ignored `build/milestone-2c/`. Run `python scripts/build_language_screen_poc.py` to regenerate them.

### Installed state and next runtime step

On 2026-11-18, the ASCII control was installed to these exact files:

- X: `%APPDATA%\AzaharPlus\load\mods\0004000000055D00\romfs\a\0\7\4`
- Y: `%APPDATA%\AzaharPlus\load\mods\0004000000055E00\romfs\a\0\7\4`

Both installed files are 2,388,484 bytes and have SHA-256 `252f90a4eca1c16dac0f0a32758e867ec7b9dbb322c00f975e3d7fc6ab233d0c`, matching their generated ASCII-control files. The previous files were backed up to `build\milestone-2c\install-backups\20261118T215421Z\`:

- `pokemon-x-a074.before-ascii-control`
- `pokemon-y-a074.before-ascii-control`

Each backup has SHA-256 `ebfa2db696d0e7b2c5bcd2b6fe20527ff395e51590b605b4250f30e8ce535cae`. AzaharPlus was not launched during installation. Launch Pokémon X and Pokémon Y separately with update 1.5 enabled and check whether the bottom-right label shows `ASCII 2C`. Do not install the Russian variant yet. Record one result per game and capture screenshots plus AzaharPlus logs.

To restore the previous mod archives, close AzaharPlus, open PowerShell, and run:

```powershell
$backup = Join-Path (Get-Location) 'build\milestone-2c\install-backups\20261118T215421Z'
$xTarget = Join-Path $env:APPDATA 'AzaharPlus\load\mods\0004000000055D00\romfs\a\0\7\4'
$yTarget = Join-Path $env:APPDATA 'AzaharPlus\load\mods\0004000000055E00\romfs\a\0\7\4'
Copy-Item -LiteralPath (Join-Path $backup 'pokemon-x-a074.before-ascii-control') -Destination $xTarget -Force
Copy-Item -LiteralPath (Join-Path $backup 'pokemon-y-a074.before-ascii-control') -Destination $yTarget -Force
```

This restores only the two `a/0/7/4` mod files. It does not touch game assets, updates, saves, or unrelated mods. To disable the project override instead, close AzaharPlus and remove only these exact two mod files after confirming no other mod uses them.

## Logs and interpretation

The inspected `%APPDATA%\AzaharPlus\log\azahar_log.old.txt` records launches of base Title IDs `0004000000055D00` and `0004000000055E00`, but contains no LayeredFS or `load\mods` entries. The current `azahar_log.txt` was empty at inspection. The installed `a/0/7/4` files matched the earlier generated Milestone 2B outputs by SHA-256, but their in-game result was inconclusive because message 35/0 ID 22 is not the screenshot label.

Seeing `ASCII 2C` in the next run will be direct runtime evidence that the new update archive resource is overlaid. If the exact ASCII label remains visible even though it is present in the update-only member, that separates the problem from glyph support and points to the effective mod path, competing mod, update resource selection, or runtime cache. Record the title ID and update version shown by the emulator, screenshot, mod file hash, and complete log before reporting.

After LayeredFS is confirmed, test uppercase and lowercase Cyrillic, Ё/ё, punctuation, mixed digits, and a longer wrapped string before starting bulk translation. Verify other menus and gameplay screens in later QA. No Milestone 2C variant has been launched by this project run.

## Milestone 2D Russian test installation

On 2026-11-19, only the two `a\0\7\4` mod files were replaced with the generated Russian variants. Both installed files hash to `d2fbd6bebd5b7764b2e4ec2077d7f3ed7cbc343dc60bf3b1b73933db24c572fa`. The previous ASCII controls are backed up at `build\milestone-2d\install-backups\20261119T182134Z\` and hash to `252f90a4eca1c16dac0f0a32758e867ec7b9dbb322c00f975e3d7fc6ab233d0c`. Exact paths and restore commands are in [the Milestone 2D record](../research/milestone-2d.md).

AzaharPlus was not launched by the project for this replacement. The owner subsequently confirmed that `Привет!` renders correctly in both X and Y with update 1.5 enabled. See the Milestone 3A tests below for broader character and layout coverage.

## Milestone 3A full glyph and layout tests

The owner later confirmed that `Привет!` renders correctly in both games. This verifies only the characters in that greeting. Generated test patches target update 1.5 `a/0/7/4`, GARC member 85/0, message 1, the visible language-selection help panel:

| Variant | X/Y SHA-256 | Generated target |
|---|---|---|
| `glyph-coverage` | `f05cbd20ebdc2beb1d438d6b82a6ff61ccdd183ee41b12b208ced7be0d1e791c` | `build/milestone-3a/glyph-coverage/<pokemon-x-or-y>/<base-title-id>/romfs/a/0/7/4` |
| `long-text` | `092ee4b69a085867f2547f780ff13af19826d70ab3a8b0963bd834fa01f8ab61` | `build/milestone-3a/long-text/<pokemon-x-or-y>/<base-title-id>/romfs/a/0/7/4` |

Each preserves the original control-code sequence, placeholders, and all 150 non-target GARC members. Build or refresh them with `python scripts/build_render_validation.py`. They are not installed automatically.

### Backup current Russian files and install glyph coverage

Close AzaharPlus before changing any mod file. From the project root in PowerShell, back up the currently installed Russian probes. Stop if the target files are missing or the backup path already exists:

```powershell
$backup = Join-Path (Get-Location) 'build\milestone-3a\install-backups\pre-test-russian'
if (Test-Path -LiteralPath $backup) { throw 'Backup path already exists; choose a new directory.' }
$xTarget = Join-Path $env:APPDATA 'AzaharPlus\load\mods\0004000000055D00\romfs\a\0\7\4'
$yTarget = Join-Path $env:APPDATA 'AzaharPlus\load\mods\0004000000055E00\romfs\a\0\7\4'
if (!(Test-Path -LiteralPath $xTarget) -or !(Test-Path -LiteralPath $yTarget)) { throw 'Expected current Russian test files are missing.' }
New-Item -ItemType Directory -Force -Path $backup | Out-Null
Copy-Item -LiteralPath $xTarget -Destination (Join-Path $backup 'pokemon-x-a074.before-tests')
Copy-Item -LiteralPath $yTarget -Destination (Join-Path $backup 'pokemon-y-a074.before-tests')
```

Install only the `glyph-coverage` files first:

```powershell
$xSource = (Resolve-Path '.\build\milestone-3a\glyph-coverage\pokemon-x\0004000000055D00\romfs\a\0\7\4').Path
$ySource = (Resolve-Path '.\build\milestone-3a\glyph-coverage\pokemon-y\0004000000055E00\romfs\a\0\7\4').Path
Copy-Item -LiteralPath $xSource -Destination $xTarget -Force
Copy-Item -LiteralPath $ySource -Destination $yTarget -Force
certutil -hashfile $xTarget SHA256
certutil -hashfile $yTarget SHA256
```

Both hashes must equal `f05cbd20ebdc2beb1d438d6b82a6ff61ccdd183ee41b12b208ced7be0d1e791c`. Launch X and Y separately with update 1.5 enabled, and inspect the entire help panel. Record which uppercase and lowercase letters render, specifically Ё/ё, punctuation, digits, symbols, unexpected substitutions, and clipping. Do not select or confirm a language; screenshots of the initial screen are sufficient and avoid changing game data.

### Install long-text layout probe

Close AzaharPlus. Replace only the same two mod files with the `long-text` outputs:

```powershell
$xSource = (Resolve-Path '.\build\milestone-3a\long-text\pokemon-x\0004000000055D00\romfs\a\0\7\4').Path
$ySource = (Resolve-Path '.\build\milestone-3a\long-text\pokemon-y\0004000000055E00\romfs\a\0\7\4').Path
Copy-Item -LiteralPath $xSource -Destination $xTarget -Force
Copy-Item -LiteralPath $ySource -Destination $yTarget -Force
certutil -hashfile $xTarget SHA256
certutil -hashfile $yTarget SHA256
```

Both hashes must equal `092ee4b69a085867f2547f780ff13af19826d70ab3a8b0963bd834fa01f8ab61`. In each game, observe automatic horizontal wrapping, glyph clipping, line spacing, control-code color changes, whether the panel scrolls, and whether lower lines overflow or disappear. Capture the full screen for each game.

### Restore the Russian greeting

After capturing both test variants, close AzaharPlus and restore the backups:

```powershell
Copy-Item -LiteralPath (Join-Path $backup 'pokemon-x-a074.before-tests') -Destination $xTarget -Force
Copy-Item -LiteralPath (Join-Path $backup 'pokemon-y-a074.before-tests') -Destination $yTarget -Force
```

This restores the two pre-test `a/0/7/4` files only. Do not copy entire RomFS folders. Preserve original assets, update data, saves, and unrelated mods. No Milestone 3A test patch has been installed by the project.
