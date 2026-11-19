# Architecture Overview

## Pipeline

1. Inventory source trees and record hashes before any processing.
2. Resolve the effective resource set for each game/update combination.
3. Identify formats using local signatures and published implementations.
4. Extract records losslessly with stable source provenance.
5. Store shared and game-specific translation records in structured UTF-8 data.
6. Validate control sequences, placeholders, glyph coverage, length, and glossary rules.
7. Rebuild only the necessary resources in isolated build directories.
8. Package a legally reviewed delta patch, with X and Y target metadata.
9. Verify in AzaharPlus 2126.2-A with update 1.5 enabled and retain evidence for each runtime check.

## Source immutability

`workspace/` contains local source trees and is protected by `.gitignore` and `AGENTS.md`. Tools must treat inputs as read-only; generated files go under `build/` or `reports/`. Hash manifests provide pre-processing fingerprints.

## Translation identity

Source records use `gen6:<resource path>:<GARC entry>/<subfile>:<TextFile message index>` as the stable coordinate ID. A SHA-256 over exact decoded message words distinguishes version-specific source variants. Identical coordinates and words across X/Y/base/update merge provenance; different source variants remain separate even when their English display text matches. Equal words at different coordinates are not merged. The local ignored catalog preserves source segments, ordered control words, offsets/reserved/padding metadata, message word count, source hash, and each source occurrence. The committed translation file references the stable coordinate plus variant hash and preserves control events as ordered segments.

The 721-species glossary is keyed by National Pokédex number and English lookup name. Current Cyrillic spellings come from Bulbapedia and carry a separate CC BY-NC-SA 2.5 attribution/license; they are not covered by the repository's WTFPL code/documentation license. Other terminology entries carry explicit established/provisional/research-needed states.

## Effective resources

Base and update trees remain separate. The effective manifest records each path's provider and hash. Owner runtime tests confirmed the update-1.5 `a/0/7/4` LayeredFS replacement is loaded in both X and Y. The update contains no `a/0/8/2`; that script archive therefore has only a base candidate, though its actual open path has not been independently traced in the running game. Other resource precedence remains unverified. The local AzaharPlus user-data path is `%APPDATA%\\AzaharPlus`.
