# MicrosoftEdge — current work and handoff

Updated: 2026-10-20. Owner: Maintainer. State: CLI ordering and desktop GUI implemented on review branches; native desktop/browser acceptance pending. [Scope and launch instructions](README.md).

## Objective and authorization

Maintainer requested detection of existing numbering and ordered favourites before an A–Z remainder, then requested a GUI with drag/drop and stars. These features are implemented for review; no real Edge data was accessed or changed.

## Completed and evidence

- CLI ordering is published in [PR #3](https://github.com/xander-me/MicrosoftEdge/pull/3), tracking [#2](https://github.com/xander-me/MicrosoftEdge/issues/2); still open at session start.
- Shared Python/Tk desktop GUI: starred and alphabetical lists, drag between lists to star/unstar, drag favourites into order, buttons and double-click alternatives, live preview, browse/load/reset and explicit confirmed apply.
- `--demo` uses disposable sample profiles. `--local-state` supports copied fixtures. Default paths cover Windows and macOS. GUI and CLI share the existing folder-ID favourite settings format.
- Shared Python ordering/file-write helpers extracted without changing CLI behavior. GUI save model adds stale-settings detection, existing browser-data checks, unique backups and settings-write recovery messages. Windows checks for running Edge; macOS relies on the user closing it.
- `python3 -m unittest discover -s tests -v`: all 8 tests passed on Linux (Python 3 and pwsh). Includes both CLI fixture tests and six GUI model tests for ordering, preview-only edits, persistence, stale files, removed profiles, invalid settings and partial-write recovery.
- GUI/shared modules compiled successfully; CLI help verified. No real profiles used.

## Remaining acceptance and limitations

Tk and a display server are absent in this environment: actual window rendering, mouse drag/drop and keyboard interaction NOT RUN. Native Windows/macOS GUI, Windows PowerShell 5.1 and disposable-browser integration NOT RUN. Maintainer owns access to those environments. Numeric names do not guarantee Edge's visual ordering. Platform collation can differ. Browser data and settings are separate writes; recovery guidance is in README. GUI requires Python with Tk; no packaged installer.

## Next action

Review CLI PR #3 and its dependent GUI PR. On Windows/macOS with Tk, launch the GUI using `--demo`, verify drag-to-star/unstar, favourite reordering, preview and apply/reload. Then test copied real-world fixtures and disposable Edge profiles, checking restart persistence and backup recovery before wider use.

## Branch and local work

GUI work is on `feat/profile-order-gui`, branched from clean, synchronized `feat/starred-profile-order` at `194a3f7`. It depends on PR #3 and will be submitted with that branch as its PR base, keeping the GUI diff separate. Tracks [issue #4](https://github.com/xander-me/MicrosoftEdge/issues/4). No earlier work was moved or overwritten. Final PR/publication details are recorded below.
