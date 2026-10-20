# MicrosoftEdge — current work and handoff

Updated: 2026-10-20. Owner: Alexander. State: CLI ordering and desktop GUI implemented on review branches; native desktop/browser acceptance pending. [Scope and launch instructions](README.md).

## Objective and authorization

Alexander requested detection of existing numbering and ordered favourites before an A–Z remainder, then requested a GUI with drag/drop and stars. These features are implemented for review; no real Edge data was accessed or changed.

## Completed and evidence

- CLI ordering is published in [PR #3](https://github.com/xander-me/MicrosoftEdge/pull/3), tracking [#2](https://github.com/xander-me/MicrosoftEdge/issues/2); still open at session start.
- Shared Python/Tk desktop GUI: starred and alphabetical lists, drag between lists to star/unstar, drag favourites into order, buttons and double-click alternatives, live preview, browse/load/reset and explicit confirmed apply.
- `--demo` uses disposable sample profiles. `--local-state` supports copied fixtures. Default paths cover Windows and macOS. GUI and CLI share the existing folder-ID favourite settings format.
- Shared Python ordering/file-write helpers extracted without changing CLI behavior. GUI save model adds stale-settings detection, existing browser-data checks, unique backups and settings-write recovery messages. Python checks for running Edge on Windows and macOS (temporary GUI demo exempt); PowerShell checks msedge.
- `python3 -m unittest discover -s tests -v`: all 13 tests passed on Linux (Python 3 and pwsh). Includes both CLI fixture tests and eleven GUI model tests for ordering, preview-only edits, persistence, stale files, removed profiles, invalid settings and partial-write recovery.
- GUI/shared modules compiled successfully; CLI help verified. No real profiles used.

## Preservation requirement added

Alexander requires existing passwords, sync, policies and all other profile behaviour to continue working, with a backup before anything is changed. Ordering remains a display-name operation with stable folder IDs; no physical profile movement or recreation. Both Python entry points now share the save model. All writes require a flushed, byte-verified Local State backup plus a backup of existing favourites settings; failed backup aborts before source writes, including settings-only changes. True no-ops write nothing. Regression fixtures compare the full Local State except name fields, preserve synthetic encryption/account fields, and byte-compare synthetic password, preferences, cookies, sync and extension files. Tests also cover failed/corrupt backups and running-browser rejection. Automatic backups cover only files this tool overwrites, not a full browser/password backup.

Real password/autofill, sign-in, sync and policy continuity are REQUIRED but NOT RUN; [acceptance checklist](docs/profile-preservation-validation.md). Synthetic file preservation cannot certify these behaviours. Latest hardening is in PR #5; do not treat earlier PR #3 alone as satisfying this requirement.

## Remaining acceptance and limitations

Tk and a display server are absent in this environment: actual window rendering, mouse drag/drop and keyboard interaction NOT RUN. Native Windows/macOS GUI, Windows PowerShell 5.1 and disposable-browser integration NOT RUN. Alexander owns access to those environments. Numeric names do not guarantee Edge's visual ordering. Platform collation can differ. Browser data and settings are separate writes; recovery guidance is in README. GUI requires Python with Tk; no packaged installer.

## Next action

Review CLI PR #3 and its dependent GUI PR. On Windows/macOS with Tk, launch the GUI using `--demo`, verify drag-to-star/unstar, favourite reordering, preview and apply/reload. Then test copied real-world fixtures and disposable Edge profiles, checking restart persistence, saved-password/autofill continuity, account and sync health, unchanged policies and backup recovery using the preservation checklist before wider use.

## Branch and local work

GUI work is on `feat/profile-order-gui`, branched from clean, synchronized `feat/starred-profile-order` at `194a3f7`. It depends on PR #3 and will be submitted with that branch as its PR base, keeping the GUI diff separate. Tracks [issue #4](https://github.com/xander-me/MicrosoftEdge/issues/4). No earlier work was moved or overwritten. Implementation and validation are committed and pushed in [PR #5](https://github.com/xander-me/MicrosoftEdge/pull/5), targeting `feat/starred-profile-order`. Both PRs remain open. After #3 merges, retarget #5 to main before merging it. No local/unpushed work remains after this handoff update.
