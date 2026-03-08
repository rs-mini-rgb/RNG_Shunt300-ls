# v1.0.1 Release Notes

Release date: March 8, 2026

## Security Fixes

- Fixed a path traversal risk in static file serving logic (`src/shunt300_live_simulator.py`).
- Hardened `resolve_resource_path()` to resolve canonical paths and only allow files under `RESOURCE_DIR`.
- Requests that attempt to escape the resource directory are now rejected and return `404`.

## Impact

This is a security patch release and is recommended for all users.

## Integrity and Signing

- Installer: `Renogy_Shunt300LS_Setup.exe`
- Portable package: `Renogy_Shunt300LS_Portable.zip`
- Signed release assets continue to be produced by the existing signing workflow.

## Upgrade Notes

- Replace previous installer/portable artifacts with the v1.0.1 builds.
- No configuration changes are required.
