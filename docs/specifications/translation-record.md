# Translation Record Specification (Draft)

Each extracted message record must include a stable ID, source text, source language, target scope (`shared`, `x`, or `y`), source game/version and relative path, archive/member/message indices, source resource hash, context, raw control-code signature, translation text, and one status: `untranslated`, `machine_draft`, `reviewed`, `validated`, or `tested_in_game`.

Equal source wording does not establish shared identity. Sharing requires equivalent context, placeholders, and formatting. Machine-generated drafts must never be marked reviewed.

## Stable identity and provenance

Use a stable ID derived from the game/resource scope and source location, not translated text: game scope, relative RomFS path, GARC entry/subfile ID, and TextFile message index. Record every contributing X/Y and base/update source hash when equivalent messages are shared. Keep the raw encrypted words in local generated build data only; translation records retain decoded source, exact control-word sequence, and placeholders needed for safe rebuilding.

## Local batch workflow

1. Export all discovered TextFile messages to ignored `build/translation-export/` JSONL with context and provenance.
2. Compare records across X/Y and base/update resources using source text plus context and token signatures. Create a shared record only when those dimensions match; otherwise create a game/version override.
3. Store approved Russian glossary terms and translation memory entries as project-authored data. Mark conflicts for review rather than choosing silently.
4. Generate drafts only through an explicitly approved local workflow. Do not send copyrighted source strings to paid or third-party services without authorization.
5. Validate UTF-16/BMP constraints, control and placeholder preservation, glossary consistency, game-font mappings/fallback observations, and length/layout limits.
6. Review translations before changing `machine_draft` to `reviewed`; run asset rebuild and emulator checks before using `validated` or `tested_in_game`.

The X/Y runtime and glyph work must be complete before bulk translation begins. The batch exporter is not a license to commit full English text archives or generated copyrighted binaries.
