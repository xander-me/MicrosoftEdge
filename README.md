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

The same Python menu supports Windows (`py` instead of `python3`) and macOS. It detects the standard Edge data location. On Mac, you can also double-click **Try Demo.command** or **Start Edge Profile Organiser.command**; both now open the terminal menu and find a suitable Python without checking/installing Tk. Current terminal version: `0.5.2-terminal` (`--version`).

## Menu

One table combines existing profiles and the rename preview: **#** is the stable selection number, **\*** marks favourites, **Profile** shows the name without its numeric prefix, **Now** shows the current prefix and **Next** shows the proposed prefix. Arrows mark changes; equals marks unchanged names. Summary counts appear above the table.

Use the left **#** column for all selections—it is separate from Now/Next. Names fit the terminal width. Folder IDs and the source path are hidden by default; **V** toggles details/full names, or start with `--details`. Existing prefixes and duplicate counts are still detected. No colour or extra packages are required.

| Key | Action |
| --- | --- |
| S | Set starred profiles in top-first order, e.g. `4,2`; Enter keeps the order, `none` clears it |
| M | Move/pin a selected profile to a position among the starred profiles (`1` makes it top) |
| U | Unstar a profile, returning it to the alphabetical remainder |
| R | Refresh disk data while retaining explicit favourite edits for surviving folder IDs |
| A | Review the preview and confirm application; verified backups precede writes |
| B | Back up ALL profiles and all shared Edge data in one verified snapshot; no profile selection |
| D | Back up a selected profile, then optionally open Edge's native removal screen |
| V | Toggle full names, folder IDs and source path |
| Q | Quit; asks before discarding an edited starred order |

To promote a new profile to 01, choose **M**, enter its list number, then starred position **1**. Review the preview, choose **A**, and confirm with `y`. Favourites are remembered by stable folder ID in `EdgeProfileOrg.settings.json` beside Local State. New unstarred profiles join the A–Z remainder.

If Edge saves Local State while closing, **A** refreshes the preview without writing. Review it and choose **A** again. **R** also refreshes without discarding your proposed favourites. Strict final checks still reject changed data rather than overwriting it.

## Backups, removal and recovery

Ordering changes only profile display names and organiser favourites. Existing profile folders, passwords, cookies, account/sync metadata, encryption-key fields, extensions and policy stores remain in place. Names do not guarantee Edge's visual ordering on every version.

Before any ordering/settings write, the tool creates uniquely named, flushed and byte-verified backups of Local State and any existing organiser settings. Failed backup stops writes; true no-ops write nothing. This backup covers files ordering can overwrite; it is not a full backup of all browser/password data.

**B** first asks where to save the backup. Paste a destination folder (external drives and paths with spaces are supported), or press Enter for the displayed default; the last choice remains the default during that run. A unique snapshot folder is created inside it after confirmation. Destinations inside Edge data or pointing to an existing file are rejected.

**B** copies and hash-verifies the entire Edge user-data folder: every profile (including unregistered folders), shared data, Local State and organiser settings. It asks for one confirmation, checks disk space, prints progress and verifies the source stayed unchanged. Snapshots are unique and stored outside the source folder. The size is the total size of an uncompressed copy, including caches, databases, extensions and shared files; it reports the six largest source folders/files to show where space is used. Known Chromium runtime links are preserved as links; other symbolic links stop the backup rather than silently omit profile data.

**D** additionally copies and hash-verifies the selected profile directory before offering removal. Only a successful full snapshot receives a `READY.json` marker. Source profile data is never directly deleted by this tool. **D** offers to open the selected profile's Edge settings after backup; you confirm deletion there, so Edge handles account cleanup and managed restrictions. No cloud deletion request is sent by the organiser. Demo and copied-file modes cannot open removal for real profiles. Full backups contain private browser data: keep them locally.

For ordering recovery: close Edge and restore the printed Local State backup to its original name; restore matching organiser settings too (or remove the new settings file if none existed before). A full **B** snapshot contains a `User Data` folder and `READY.json`; use the manifest’s `original_user_data` to identify its restore location. Restore the complete directory with Edge closed, preserving the current directory separately rather than merging stale files. Full recovery is for the same machine/OS account and snapshot; it does not back up Keychain or remote sync state. Restoring Local State also restores its entire profile registry, so later profile additions/removals need reconciliation. See [Mac usage and recovery](docs/mac-first-run.md) and [required preservation acceptance](docs/profile-preservation-validation.md).

## File access and test modes

Switching to Terminal does not bypass macOS privacy controls or file permissions. If access is denied, the tool reports the operation and path and leaves permission settings unchanged. Review access for the actual terminal app in System Settings → Privacy & Security; do not use sudo or change profile ownership/permissions as a workaround. Apple documents [app file-access controls](https://support.apple.com/en-ca/guide/security/secddd1d86a6/web).

Use `--local-state "/path/to/copied/Local State"` for copied fixtures; settings/backups stay beside that fixture. `--demo` makes temporary sample profiles and default backups, removed on exit. A custom destination chosen in demo mode retains its synthetic backup after exit. `--quick` retains the earlier one-shot star-selection/apply flow. The PowerShell script remains available for the earlier Windows CLI flow; use the Python menu for the complete current functionality.

```sh
python3 -m unittest discover -s tests -v
```

Terminal integration checks run with site packages disabled. Optional historical GUI checks skip when Tk/display support is absent. Native real-profile password/autofill, sync/policy continuity and removal/recovery remain acceptance gates; synthetic tests do not certify them.

## Status

Read [STATUS.md](STATUS.md) for evidence and next actions. Earlier GUI sources/build instructions remain as a prototype in history/current files; automatic Mac GUI packaging is disabled. Current usage and launchers use the terminal edition. No real browser data is accessed by automated tests.
