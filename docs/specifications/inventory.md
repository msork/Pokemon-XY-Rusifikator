# Inventory and Comparison Specification

`scripts/inventory.py` is read-only. Its JSON Lines manifest has one record per regular file, ordered by normalized relative path:

```json
{"path":"a/0/0","sha256":"...64 lowercase hex...","size":123}
```

Paths use `/` separators and are relative to the supplied dataset root. SHA-256 covers the exact file bytes. Comparison reports identical paths and content, differing content, and paths present on only one side. Symlinks are not followed by `Path.is_file` traversal behavior.

Do not treat matching counts, aggregate sizes, or file names as proof of content identity. A complete comparison requires per-file hashes.
