# Release and Recovery Requirements

Release artifacts must not contain original game files or complete derived archives. Evaluate delta patches against applicable law and source-specific compatibility; publish only with a clear target fingerprint and exact game/version metadata. Installation must preserve user saves and original `.3ds` files. Uninstallation removes only the project-owned mod folder after a clear path check. Back up existing mod contents before installation and document restoration.

Milestone test patches containing modified game resources are generated only under ignored `build/` and are never committed or pushed. They must not be installed automatically by build scripts.
