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
9. Verify in Azahar with update 1.5 and retain evidence for each runtime check.

## Source immutability

`workspace/` contains local source trees and is protected by `.gitignore` and `AGENTS.md`. Tools must treat inputs as read-only; generated files go under `build/` or `reports/`. Hash manifests provide pre-processing fingerprints.

## Translation identity

Records will use stable IDs derived from source provenance and record index, not English text alone. Translation entries will record source hash, game/version scope, context, status, and control-code signature. Shared text may be linked only after context and formatting equivalence are established.

## Effective resources

Base and update trees remain separate. The effective manifest records each path's provider and hash. Update replacement precedence is not considered established until checked against the target Azahar build and official loader source.
