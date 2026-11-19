# Milestone 3C Test Plan

## Automated validation

Run these commands from the repository root. The build writes only under ignored `build/milestone-3c/`.

```powershell
python scripts/build_pilot_translations.py
python scripts/validate_translation_data.py
python scripts/verify_text_roundtrips.py
python scripts/build_gameplay_pilot.py --include-machine-drafts
python -m unittest discover -s tests -v
```

The tests cover update-over-base selection and base fallback, distinct X/Y source variants, strict source hashes, explicit opt-in for machine drafts, exact control/placeholder preservation, unchanged messages and GARC members, archive round trips, backup hashes, path confinement, and rollback that affects only named target files.

Before owner installation, compare each generated and installed file SHA-256 with the table in [Milestone 3C findings](../research/milestone-3c.md). Also verify the source backup manifest. Do not stage or distribute `build/milestone-3c/`; it contains full derived game archives and local backup copies.

## Owner runtime test

The patch is not installed and AzaharPlus has not been launched as part of this milestone. When the owner elects to proceed, follow the exact backup/install/rollback sequence and the message-by-message X/Y checklist in [Milestone 3C findings](../research/milestone-3c.md). Use AzaharPlus 2126.2-A with update 1.5 enabled, test each title separately, and use a fresh or disposable save session. Record screenshots and runtime observations; leave all translation records at `machine_draft` until a human has approved the text and the owner reports the in-game result.
