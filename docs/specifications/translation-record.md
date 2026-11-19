# Translation Record Specification (Draft)

Each source row in the local JSONL catalog includes a stable coordinate ID, exact source-variant SHA-256, decoded source text, ordered text/control segments, source language, every game/version/path occurrence, archive/member/TextFile hashes, member/message indices, and raw control words. A translation row is keyed by `(record_id, source_variant_sha256)`, includes game scope (`shared`, `x`, or `y`), version scope (`base`, `update-1.5`, or both), ordered Russian text/control segments, and one status: `untranslated`, `machine_draft`, `reviewed`, `validated`, or `tested_in_game`.

Equal source wording does not establish shared identity. Sharing requires equivalent context, placeholders, and formatting. Machine-generated drafts must never be marked reviewed.

## Stable identity and provenance

Use the stable coordinate ID `gen6:<resource path>:<entry>/<subfile>:<message index>`, not translated text. The source-variant hash disambiguates changed message words at a stable coordinate. Group occurrences only when the coordinate and exact decoded source words match; preserve all X/Y and base/update hashes. Equal wording at different coordinates remains separate. Keep raw encrypted words in local generated build data only; committed translation data retains the exact source hash and control-word sequence required for safe import without duplicating full English source archives.

## Local batch workflow

1. Export all discovered TextFile messages to ignored `build/translation-export/` JSONL with context and provenance.
2. Compare records across X/Y and base/update resources using source text plus context and token signatures. Create a shared record only when those dimensions match; otherwise create a game/version override.
3. Store approved Russian glossary terms and translation memory entries as project-authored data. Mark conflicts for review rather than choosing silently.
4. Generate drafts only through an explicitly approved local workflow. Do not send copyrighted source strings to paid or third-party services without authorization.
5. Validate UTF-16/BMP constraints, control and placeholder preservation, glossary consistency, game-font mappings/fallback observations, and length/layout limits.
6. Review translations before changing `machine_draft` to `reviewed`; run asset rebuild and emulator checks before using `validated` or `tested_in_game`.

The X/Y runtime and glyph work must be complete before bulk translation begins. The batch exporter is not a license to commit full English text archives or generated copyrighted binaries.
