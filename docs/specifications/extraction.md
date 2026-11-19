# Read-Only Extraction Specification

Inspection tools may read only source files under `workspace/`. Source files must not be modified or deleted. Extracted member files, message records, font reports, and test rebuilds must be written beneath ignored `build/` paths.

For supported GARC v4, record archive SHA-256, member entry and subfile IDs, member byte length and SHA-256, and whether the member is compressed. Decompression must be explicit and bounded. Preserve raw member bytes alongside any decoded representation.

Gen VI TextFile records must retain source archive path, entry ID, subfile ID, message line index, source member hash, TextFile hash, original encrypted 16-bit units, decoded units, and control-token sequence. Keep empty lines and duplicate English strings. IDs are scoped to a member and must never be inferred from text content.

No-change serialization must preserve header fields, section metadata, per-line reserved table fields, message order, encrypted words, gaps/padding, terminators, and all offsets; checked source members must round-trip byte-exactly. Replacement serialization may change message lengths and subsequent offsets, but must preserve message IDs, per-message encryption-key progression, table metadata, and control-code/placeholder token sequence. Plain-string replacements are limited to valid BMP code points and reject empty values and unsupported control characters.

Font inspection must be read-only and report the font signature, validated character-map blocks, mapped code points, required-character coverage, and CWDH advance metrics where a codepoint maps to a glyph. CMAP `codeEnd` is inclusive. Absence of a codepoint mapping in an inspected font does not prove whether a game or emulator provides a separate fallback. Static advance units are not screen pixels; use runtime screenshots for actual wrapping and clipping.

All parser and extraction tests use synthetic fixtures. Against local copyrighted data, automated commands may emit ignored build outputs and aggregate metadata, but no extracted text or binaries may be committed.
