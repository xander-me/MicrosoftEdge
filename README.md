# Microsoft Edge profile utilities

**Status: utility scripts; browser/OS integration has not been revalidated by the repository-organization review.**

Rename Edge profiles with alphabetical numeric prefixes. Work on these utilities in this repository.

| Platform | Script | Prerequisites |
| --- | --- | --- |
| Windows | [EdgeProfileOrg_V1.0.ps1](ProfileOrg/EdgeProfileOrg_V1.0.ps1) | PowerShell 5.1+, Edge profiles in the current user's Local AppData |
| macOS | [EdgeProfileOrg_V1.0.py](ProfileOrg/EdgeProfileOrg_V1.0.py) | Python 3, Edge profiles in the current user's Library |

## Use and recovery

Close Edge completely and run the script for the account whose profiles you want to rename. The Windows script also force-stops Edge processes. Each script makes a timestamped backup of `Local State` before writing changes; note the backup path printed by the script.

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

Validate renaming, repeated runs and backup restoration on copies of representative Windows/macOS `Local State` fixtures, then test in disposable browser profiles. There is no committed automated test suite. Script inspection is not evidence of browser integration acceptance.

## Current work and handoff

Read [STATUS.md](STATUS.md) for current work, evidence, blockers and the next action. This README remains the project entry point; the handoff is a dated record and must be checked against live Git/issue state.
