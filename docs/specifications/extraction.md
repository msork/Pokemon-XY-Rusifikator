# Read-Only Extraction Specification

Inspection tools may read only source files under `workspace/`. Source files must not be modified or deleted. Extracted member files, message records, font reports, and test rebuilds must be written beneath ignored `build/` paths.

For supported GARC v4, record archive SHA-256, member entry and subfile IDs, member byte length and SHA-256, and whether the member is compressed. Decompression must be explicit and bounded. Preserve raw member bytes alongside any decoded representation.

Gen VI TextFile records must retain source archive path, entry ID, subfile ID, message line index, source member hash, TextFile hash, original encrypted 16-bit units, decoded units, and control-token sequence. Keep empty lines and duplicate English strings. IDs are scoped to a member and must never be inferred from text content.

Font inspection must be read-only and report the font signature, validated character-map blocks, mapped code points, and required-character coverage. Absence of a codepoint mapping in an inspected font does not prove whether a game or emulator provides a separate fallback.

All parser and extraction tests use synthetic fixtures. Against local copyrighted data, automated commands may emit ignored build outputs and aggregate metadata, but no extracted text or binaries may be committed.
