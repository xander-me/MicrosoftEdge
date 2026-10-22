# Edge Profile Organiser — terminal edition

Organise existing Edge profile names with starred profiles first and the remainder A–Z. **The terminal menu is the active interface.** It requires Python 3.10+ and the Python standard library only: no Tk, pip packages or Homebrew setup.

## Start

From your checkout, try disposable sample data first:

```sh
python3 ProfileOrg/EdgeProfileOrg_V1.0.py --demo
```

Then close Edge completely and run against your current user's profiles:

```sh
python3 ProfileOrg/EdgeProfileOrg_V1.0.py
```

The same Python menu supports Windows (`py` instead of `python3`) and macOS. It detects the standard Edge data location. On Mac, you can also double-click **Try Demo.command** or **Start Edge Profile Organiser.command**; both now open the terminal menu and find a suitable Python without checking/installing Tk. Current terminal version: `0.6.0-terminal` (`--version`).

## Live navigation

In Apple's Terminal.app, the preview stays visible and updates immediately. Rows follow the proposed order; the highlight follows the selected profile when it moves. **Now** is the existing prefix, **Next** is the proposed prefix, **\*** marks favourites and **->** marks changes. Unstarred profiles sort A–Z.

| Key | Action |
| --- | --- |
| ↑ / ↓ | Select a profile (Page Up/Down, Home/End also work) |
| Space / S | Toggle the selected profile's star |
| M | Star the selected profile and pin it first |
| - / + | Move the selected starred profile up/down |
| U | Unstar the selected profile |
| R | Refresh disk data, retaining favourite edits |
| A | Confirm and save the preview, with verified backups first |
| B | Choose a destination and back up all registered profile folders plus recovery metadata |
| D | Back up the selected profile, then optionally open Edge's native removal screen |
| V | Toggle profile details |
| Q | Quit; confirm before discarding favourite edits |

To make a new profile **01**, select it with the arrows and press **M**. Review the updated table, press **A**, then confirm. Preview edits do not write to disk. Favourites are remembered by stable folder ID in `EdgeProfileOrg.settings.json` beside Local State.

Live navigation uses Python's standard `curses` module on macOS. If unavailable (including standard Windows Python), the line-command menu is used automatically. Use `--plain` to request it explicitly; its S/M/U actions ask for selection numbers. Use `--live` to require an interactive terminal with curses. `--details` shows profile details initially.

If Edge saves Local State while closing, **A** refreshes the preview without writing. Review it and choose **A** again. **R** also refreshes without discarding your proposed favourites. Strict final checks still reject changed data rather than overwriting it.

## Backups, removal and recovery

Ordering changes only profile display names and organiser favourites. Existing profile folders, passwords, cookies, account/sync metadata, encryption-key fields, extensions and policy stores remain in place. Names do not guarantee Edge's visual ordering on every version.

Before any ordering/settings write, the tool creates uniquely named, flushed and byte-verified backups of Local State and any existing organiser settings. Failed backup stops writes; true no-ops write nothing. This backup covers files ordering can overwrite; it is not a full backup of all browser/password data.

**B** first asks where to save the backup. Paste a destination folder (external drives and paths with spaces are supported), or press Enter for the displayed default; the last choice remains the default during that run. A unique snapshot folder is created inside it after confirmation. Destinations inside Edge data or pointing to an existing file are rejected.

**B** copies only registered profile folders, plus `Local State` and existing organiser settings needed for recovery. Shared root folders, unregistered folders, runtime markers and other root files are excluded. Complete profile folders still include their own caches, databases and extensions, so backups may remain large. The scan lists the largest included folders/files. It checks free space, flushes copies, hash-verifies the snapshot and confirms included source data stayed unchanged. Symlinks fail safely. Snapshots are unique and stored outside the source folder.

**D** additionally copies and hash-verifies the selected profile directory before offering removal. Only a successful full snapshot receives a `READY.json` marker. Source profile data is never directly deleted by this tool. **D** offers to open the selected profile's Edge settings after backup; you confirm deletion there, so Edge handles account cleanup and managed restrictions. No cloud deletion request is sent by the organiser. Demo and copied-file modes cannot open removal for real profiles. Full backups contain private browser data: keep them locally.

For ordering recovery: close Edge and restore the printed Local State backup to its original name; restore matching organiser settings too (or remove the new settings file if none existed before). A full **B** snapshot contains a `User Data` folder and `READY.json`; use the manifest’s `original_user_data` to identify its restore location. With Edge closed, preserve current data separately first. Restore only the profile folders and support files listed in READY.json to their original locations; do not replace or erase the entire Edge data root with this partial snapshot. Full recovery is for the same machine/OS account and snapshot; it does not back up Keychain or remote sync state. Restoring Local State also restores its entire profile registry, so later profile additions/removals need reconciliation. See [Mac usage and recovery](docs/mac-first-run.md) and [required preservation acceptance](docs/profile-preservation-validation.md).

## File access and test modes

Switching to Terminal does not bypass macOS privacy controls or file permissions. If access is denied, the tool reports the operation and path and leaves permission settings unchanged. Review access for the actual terminal app in System Settings → Privacy & Security; do not use sudo or change profile ownership/permissions as a workaround. Apple documents [app file-access controls](https://support.apple.com/en-ca/guide/security/secddd1d86a6/web).

Use `--local-state "/path/to/copied/Local State"` for copied fixtures; settings/backups stay beside that fixture. `--demo` makes temporary sample profiles and default backups, removed on exit. A custom destination chosen in demo mode retains its synthetic backup after exit. `--quick` retains the earlier one-shot star-selection/apply flow. The PowerShell script remains available for the earlier Windows CLI flow; use the Python menu for the complete current functionality.

```sh
python3 -m unittest discover -s tests -v
```

Terminal integration checks run with site packages disabled. Optional historical GUI checks skip when Tk/display support is absent. Native real-profile password/autofill, sync/policy continuity and removal/recovery remain acceptance gates; synthetic tests do not certify them.

## Status

Read [STATUS.md](STATUS.md) for evidence and next actions. Earlier GUI sources/build instructions remain as a prototype in history/current files; automatic Mac GUI packaging is disabled. Current usage and launchers use the terminal edition. No real browser data is accessed by automated tests.
