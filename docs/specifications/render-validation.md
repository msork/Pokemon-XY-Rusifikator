# Text and Glyph Validation Specification

## Character coverage

Report static game-font mappings separately from confirmed runtime glyph support. A CMAP gap is a missing explicit game-font mapping; it must not be labeled a runtime failure if AzaharPlus or the title supplies fallback behavior. Required Russian coverage includes U+0410-U+044F and Ё/ё (U+0401/U+0451), plus the approved punctuation, digits, and special symbols. Report unmapped codepoints as U+XXXX values with affected source font IDs.

## Storage and layout limits

- Reject codepoints outside the BMP and isolated surrogate codepoints for Gen VI TextFile strings.
- Enforce the 16-bit TextFile message word-count limit against actual encoded words, including preserved control words and the terminator.
- Preserve message IDs and exact control/placeholder token sequences during replacement.
- Report explicit line lengths in Unicode codepoints and total visible BMP code units. These are storage/layout proxies, not pixel widths.
- If a character maps to the selected CFNT, calculate CWDH character advances through its glyph index. Record unmapped glyphs and missing advances as unknown; do not substitute guessed widths.
- Treat runtime wrapping, clipping, overlap, panel scrolling, and vertical overflow as emulator-test results. Store separate observations for Pokémon X and Pokémon Y.

## Rendering test fixtures

Test fixtures must be generated from the update-effective source archive into ignored `build/`, never written into `workspace/`. Each fixture must include game/title ID, source path/version/hash, GARC member and message ID, replacement text spans, expected control signature, output hash, and install/rollback steps. Keep coverage tests and deliberately overlong layout tests as separate variants. Do not install automatically.

## Translation pipeline preparation

Before drafting translations, export discoverable messages to local generated JSONL with stable source IDs, relative provenance, source hash, context, raw tokens/placeholders, and status. Keep source strings local; do not upload them to an external service without approval. Share records only when source context, control signature, and formatting match. Maintain game-specific overrides for divergent resources. Validate drafts against glossary terms, tokens, encoding, glyph coverage, storage limits, and layout proxies before any in-game test. Machine-generated drafts remain distinct from reviewed and tested records.
