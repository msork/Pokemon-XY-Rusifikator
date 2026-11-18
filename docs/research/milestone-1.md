# Milestone 1 Research Log

Date: 2026-11-18

## Local inventory

SHA-256 manifests were generated for all four trees under ignored `reports/`. Verified dataset totals:

| Dataset | Files | Bytes |
|---|---:|---:|
| X base | 653 | 1,783,776,455 |
| Y base | 653 | 1,783,776,439 |
| X update 1.5 | 147 | 28,575,664 |
| Y update 1.5 | 147 | 28,575,648 |

Combined size is 3,624,704,206 bytes. Sampled extensionless resources under `a/` begin with `43 52 41 47` (`CRAG`). Milestone 2A now confirms the candidate GARC structures and message formats.

## X/Y and update comparisons

Base comparison: 625 identical paths, 28 differing paths, no path-only entries. Update comparison: 109 identical paths, 38 differing paths, no path-only entries. For each game, all 147 update paths exist in base; 27 have identical bytes and 120 differ. There are 506 base-only paths and no update-only paths. These results establish byte differences, not semantic purpose or runtime precedence.

Candidate-specific findings are recorded in [Milestone 2A research](milestone-2a.md): `a/0/7/4` exists in base and update 1.5, while `a/0/8/2` and `a/1/8/5` are base-only.

## Research references

- pk3DS has Gen VI GARC and TextFile implementations: https://github.com/kwsch/pk3DS. Milestone 2A uses it as a format reference only; no source code was copied.
- Project Pokemon's X/Y file map identifies text and font candidate paths: https://projectpokemon.org/home/docs/gen-6/xy-file-system-r89/. This is a discovery reference, validated against local data in Milestone 2A.
- AzaharPlus project: https://github.com/AzaharPlus/AzaharPlus. AzaharPlus is the project's primary target as of Milestone 2A. Local user-data and LayeredFS observations are documented there.
- Upstream Azahar LayeredFS implementation: https://github.com/azahar-emu/azahar/blob/master/src/core/file_sys/layered_fs.cpp. This is background evidence only, not proof of X/Y update precedence in the local fork.

## Local emulator evidence and limitations

An earlier inspection found standard Azahar MSYS2 profile data; this is superseded by the user's target update to AzaharPlus 2126.2-A. The local AzaharPlus installation is at `C:\Users\maxim\Games\azaharplus-2126.2-A-windows`, and its observed user profile is `%APPDATA%\AzaharPlus`. Existing LayeredFS replacement logs for other games confirm the local build uses RomFS replacements, but X/Y title and update behavior are not yet runtime-verified. No game runtime test was performed in Milestone 1 or 2A.
