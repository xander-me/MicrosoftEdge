# Required profile-preservation acceptance

Status: NOT RUN in real Windows/macOS Edge. Owner: Maintainer. Synthetic regression checks pass; they do not prove browser behaviour. Do not mark password/sync/policy compatibility accepted until this checklist has evidence for the target Edge/OS versions.

## What the organiser changes

Only existing profile display names in Local State and the organiser's own favourites settings. Folder IDs, profile contents, sign-in/sync fields, encryption keys and policy stores must remain unchanged. No folders are moved and no profiles are recreated.

## Before testing

1. Use disposable Edge profiles and test accounts on the intended Windows/macOS OS account; use synthetic passwords, bookmarks, extensions and cookies. Include a managed test profile when validating policy continuity. Do not record credentials or real profile dumps in Git.
2. Record OS/Edge version, each profile's folder path from `edge://version`, signed-in account identity, sync status/settings, a sample password/autofill result and test extension/bookmark/session behaviour.
3. Export the active policy list from `edge://policy` for before/after comparison. Record whether each profile is managed. [Microsoft profile diagnostics](https://github.com/MicrosoftDocs/SupportArticles-docs/blob/main/support/microsoft-edge/security/edge-profile-wont-load-locked.md) also identifies policy exports and profile folder listings as diagnostic evidence.
4. Close Edge completely, including background processes. Keep an independent environment backup appropriate to the test environment. The tool's automatic backup covers Local State and organiser settings, not all profile data or system credential storage.

## Apply and verify

1. Load the GUI or CLI. Promote a new profile to 01, keep at least two favourites and leave an A–Z remainder. Cancel once: source files must be unchanged and no backup is required for cancelled preview-only edits.
2. Apply. Before writes, the organiser must create and verify Local State and any existing settings backups. A backup failure must stop writes. Note the backup ID/locations without storing contents in Git.
3. Before reopening Edge, compare the complete Local State JSON with its backup: only `profile.info_cache.<same folder ID>.name` may differ. Byte-compare profile files and confirm all directory names/paths are identical. The settings backup must match the previous favourites file.
4. Reopen Edge. For every profile verify unchanged folder path/account identity, saved password/autofill, cookies/session, bookmarks/extensions, sync status/settings and policy list. Confirm the intended names persist and note actual visual ordering.
5. Add a new profile, rerun, and verify favourites persist and only the remainder sorts A–Z. Repeat apply with no changes: no source writes and no extra backup. Test star-only changes: backups must still precede settings writes.
6. Close Edge and restore Local State and the matching organiser settings backup (or remove the newly created settings file if none existed). Reopen and verify original names and the same continuity checks. Local backups do not undo remote sync or external policy changes.

## Evidence to retain

Record pass/fail per OS/Edge version, test scope, exact commit, date, owner and unresolved behaviour in STATUS.md, with redacted findings here or in the issue. Password/sync/policy failures block wider use. Never infer acceptance from synthetic fixtures or a successful rename alone.
