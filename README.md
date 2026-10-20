# Microsoft Edge profile utilities

**Status: utility scripts; browser/OS integration has not been revalidated by the repository-organization review.**

Detect existing profile numbering, choose starred profiles in a fixed top-first order, and number the remaining profiles alphabetically. Work on these utilities in this repository.

| Platform | Script | Prerequisites |
| --- | --- | --- |
| Windows | [EdgeProfileOrg_V1.0.ps1](ProfileOrg/EdgeProfileOrg_V1.0.ps1) | PowerShell 5.1+, Edge profiles in the current user's Local AppData |
| macOS | [EdgeProfileOrg_V1.0.py](ProfileOrg/EdgeProfileOrg_V1.0.py) | Python 3, Edge profiles in the current user's Library |

## Use and recovery

Run the script for the account whose profiles you want to rename. It displays existing numeric prefixes, flags duplicate numbers, and lists profiles in detected numeric order (unnumbered profiles follow alphabetically). This detects name prefixes, not Edge’s internal display order.

Enter the displayed list numbers of your starred profiles in the order you want them at the top, for example `4,2`. These become `01` and `02`; all remaining profiles sort A–Z. Press Enter to keep saved favourites, or enter `none` to clear them. Existing numbered names are never automatically assumed to be favourites.

Review the proposed names, close Edge completely, and enter `y` to apply. Any other answer cancels without writing files. Windows refuses to apply while `msedge` is running; macOS relies on you closing Edge. Neither script force-stops the browser. Both check that Local State has not changed during the preview.

Favourites are saved by profile folder ID in `EdgeProfileOrg.settings.json` beside `Local State`, so they survive renaming. New profiles join the alphabetical remainder unless you explicitly star them. Removed profiles are dropped from the saved favourites on the next confirmed run. Each changed Local State receives a uniquely named backup; note the printed path. If names already match, Local State is left untouched.

From the repository root:

```powershell
# Windows, in the intended user's session
.\ProfileOrg\EdgeProfileOrg_V1.0.ps1
```

```sh
# macOS
python3 ProfileOrg/EdgeProfileOrg_V1.0.py
```

To recover, close Edge and restore the saved backup as `Local State` in the same directory before reopening the browser. Keep backups until you have verified the renamed profiles.

## Next work and validation

Run `python3 -m unittest discover -s tests -v` for isolated synthetic-fixture checks of both CLIs (PowerShell checks require `pwsh`). Coverage includes choosing favourites, invalid selections, cancellation, repeated runs, new profiles, clearing favourites, unrelated configuration preservation and byte-for-byte backup recovery.

For copied fixtures, pass `--local-state /path/to/Local State` to Python or `-LocalStatePath "C:\path\Local State"` to PowerShell. These also place settings/backups beside the supplied fixture.

Representative real-world fixtures, Windows PowerShell 5.1, and disposable Edge integration on Windows/macOS remain untested. Numeric names do not guarantee how a particular Edge version displays or persists profile order. Alphabetical collation uses each platform’s native sorting and may differ for accented names.

Restoring Local State restores names; to reset remembered favourites as well, remove `EdgeProfileOrg.settings.json` or select `none` next time. The two files are saved separately: if saving favourites fails after a successful rename, restore the printed backup or rerun and select favourites again.

## Current work and handoff

Read [STATUS.md](STATUS.md) for current work, evidence, blockers and the next action. This README remains the project entry point; the handoff is a dated record and must be checked against live Git/issue state.
