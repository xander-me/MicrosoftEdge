# Microsoft Edge profile utilities

**Status: utility scripts; browser/OS integration has not been revalidated by the repository-organization review.**

Detect existing profile numbering, choose starred profiles in a fixed top-first order, and number the remaining profiles alphabetically. Work on these utilities in this repository.

| Platform | Script | Prerequisites |
| --- | --- | --- |
| Windows | [EdgeProfileOrg_V1.0.ps1](ProfileOrg/EdgeProfileOrg_V1.0.ps1) | PowerShell 5.1+, Edge profiles in the current user's Local AppData |
| macOS | [EdgeProfileOrg_V1.0.py](ProfileOrg/EdgeProfileOrg_V1.0.py) | Python 3, Edge profiles in the current user's Library |

## Desktop GUI

The shared Windows/macOS GUI requires Python 3 with Tk support. On Windows, the python.org installer includes Tcl/Tk when that component is selected; on macOS, use a Python installation with Tk support. Check with `python3 -m tkinter` (Windows: `py -m tkinter`): it should open a small test window. Tk is a Python installation component, not a pip package.

Try temporary sample profiles first:

```sh
# macOS
python3 ProfileOrg/EdgeProfileOrg_GUI.py --demo
```

```powershell
# Windows
py .\ProfileOrg\EdgeProfileOrg_GUI.py --demo
```

Remove `--demo` to load the current user's Edge profiles automatically. Use `--local-state "/path/to/copied/Local State"` to work with a copied fixture instead. Demo changes are temporary and disappear when the app closes.

- Click **Star selected**, or drag a profile from **Other profiles** into **Starred**.
- Drag starred profiles into your preferred top-first order. **Move up/down** provides the same control without dragging.
- Drag back to **Other profiles**, or click **Unstar selected**, to return a profile to the A–Z remainder. Double-click also toggles starring.
- Check the live **Current name → New name** preview. Selecting or dragging does not write files.
- Close Edge completely, click **Apply changes**, and confirm. The GUI saves the same favourites file used by the scripts and prints the backup location in its completion dialog.
- **Load / Reset** discards the preview and reloads saved data. Closing the window without applying also discards the preview.

Existing numeric prefixes and duplicate counts are detected when loading. The first preview uses saved favourites followed by A–Z; existing numbered names alone do not establish favourites. Application checks for running Edge processes on Windows and macOS and refuses to save until they are closed (demo mode uses temporary data). The GUI refuses stale browser/settings files and asks you to reload.

Native desktop drag/drop, scaling and Edge integration on Windows/macOS still need acceptance testing. This repository does not yet provide a packaged executable or installer.

## Use and recovery

Run the script for the account whose profiles you want to rename. It displays existing numeric prefixes, flags duplicate numbers, and lists profiles in detected numeric order (unnumbered profiles follow alphabetically). This detects name prefixes, not Edge’s internal display order.

Enter the displayed list numbers of your starred profiles in the order you want them at the top, for example `4,2`. These become `01` and `02`; all remaining profiles sort A–Z. Press Enter to keep saved favourites, or enter `none` to clear them. Existing numbered names are never automatically assumed to be favourites.

Review the proposed names, close Edge completely, and enter `y` to apply. Any other answer cancels without writing files. The tools refuse to apply while Edge is detected running on Windows or macOS. Neither script force-stops the browser. Both check that Local State has not changed during the preview.

Favourites are saved by profile folder ID in `EdgeProfileOrg.settings.json` beside `Local State`, so they survive renaming. New profiles join the alphabetical remainder unless you explicitly star them. Removed profiles are dropped from the saved favourites on the next confirmed run. Before any names or favourites are written, Local State and any existing favourites settings receive uniquely named, flushed, byte-verified backups. Backup failure aborts without overwriting either source file. This includes changes to favourites alone. If both names and favourites already match, no files are written and no new backup is needed.

From the repository root:

```powershell
# Windows, in the intended user's session
.\ProfileOrg\EdgeProfileOrg_V1.0.ps1
```

```sh
# macOS
python3 ProfileOrg/EdgeProfileOrg_V1.0.py
```

To recover, close Edge and restore the saved backup as `Local State` in the same directory before reopening the browser. To restore favourites as well, use the matching `EdgeProfileOrg.settings.json.backup-before-profile-prefix-<same ID>` backup; if no favourites file existed before the operation, remove the new settings file. Keep backups until you have verified the renamed profiles.

## Profile identity and preservation

Dragging changes only the displayed numeric name prefix in `profile.info_cache.<existing folder>.name` in Local State. Profile directory names and IDs stay fixed. The tools do not move, recreate, merge or delete profiles; do not sign accounts out or change sync; and do not edit password databases, cookies, history, bookmarks, extensions, Preferences/Secure Preferences, policy stores or Local State encryption-key fields. The Python writer rebuilds from the loaded original and assigns only the previewed name fields.

Microsoft documents [profile directory identity](https://learn.microsoft.com/en-us/deployedge/edge-learnmore-create-user-directory-vars) and [enterprise sync/policy configuration](https://learn.microsoft.com/en-us/deployedge/microsoft-edge-enterprise-sync) separately. Keeping those paths and settings untouched is the preservation design; it is not a vendor guarantee that editing Local State is supported or that all Edge versions retain these names.

The automatic backup covers the files this tool can overwrite: Local State and its own favourites settings. It is **not a full backup of passwords or all browser data**, and is not a migration between computers or OS accounts. It restores this tool's local changes, not cloud sync state or policy changes made elsewhere. No password export is performed. Real password decryption/autofill, account sign-in, sync health and policy continuity are acceptance gates in [the preservation checklist](docs/profile-preservation-validation.md), currently unverified in a real browser.

## Next work and validation

Run `python3 -m unittest discover -s tests -v` for isolated synthetic-fixture checks of both CLIs (PowerShell checks require `pwsh`). GUI model checks also cover drag ordering, unstar, removed profiles, concurrent file changes and settings-write recovery. Coverage includes choosing favourites, invalid selections, cancellation, repeated runs, new profiles, clearing favourites, unrelated configuration preservation and byte-for-byte backup recovery.

For copied fixtures, pass `--local-state /path/to/Local State` to Python or `-LocalStatePath "C:\path\Local State"` to PowerShell. These also place settings/backups beside the supplied fixture.

Representative real-world fixtures, Windows PowerShell 5.1, and disposable Edge integration on Windows/macOS remain untested. Numeric names do not guarantee how a particular Edge version displays or persists profile order. Alphabetical collation uses each platform’s native sorting and may differ for accented names.

Restoring Local State restores names; to reset remembered favourites instead of restoring their backup, remove `EdgeProfileOrg.settings.json` or select `none` next time. The two files are saved separately: if saving favourites fails after a successful rename, restore the printed backup or rerun and select favourites again.

## Current work and handoff

Read [STATUS.md](STATUS.md) for current work, evidence, blockers and the next action. This README remains the project entry point; the handoff is a dated record and must be checked against live Git/issue state.
