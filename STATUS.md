# MicrosoftEdge — current work and handoff

Updated: 2026-10-20. Owner: Maintainer. State: CLI ordering and desktop GUI implemented on review branches; native desktop/browser acceptance pending. [Scope and launch instructions](README.md).

## Objective and authorization

Maintainer requested detection of existing numbering and ordered favourites before an A–Z remainder, then requested a GUI with drag/drop and stars. These features are implemented for review; no real Edge data was accessed or changed.

## Completed and evidence

- CLI ordering is published in [PR #3](https://github.com/xander-me/MicrosoftEdge/pull/3), tracking [#2](https://github.com/xander-me/MicrosoftEdge/issues/2); still open at session start.
- Shared Python/Tk desktop GUI: starred and alphabetical lists, drag between lists to star/unstar, drag favourites into order, buttons and double-click alternatives, live preview, browse/load/reset and explicit confirmed apply.
- `--demo` uses disposable sample profiles. `--local-state` supports copied fixtures. Default paths cover Windows and macOS. GUI and CLI share the existing folder-ID favourite settings format.
- Shared Python ordering/file-write helpers extracted without changing CLI behavior. GUI save model adds stale-settings detection, existing browser-data checks, unique backups and settings-write recovery messages. Python checks for running Edge on Windows and macOS (temporary GUI demo exempt); PowerShell checks msedge.
- `python3 -m unittest discover -s tests -v`: all 17 tests passed on Linux (Python 3, pwsh, Tk 8.6 and Xvfb). Includes both CLI fixture tests, four real-widget tests and eleven GUI model tests for ordering, preview-only edits, persistence, stale files, removed profiles, invalid settings and partial-write recovery.
- GUI/shared modules compiled successfully; CLI help verified. No real profiles used.

## Preservation requirement added

Maintainer requires existing passwords, sync, policies and all other profile behaviour to continue working, with a backup before anything is changed. Ordering remains a display-name operation with stable folder IDs; no physical profile movement or recreation. Both Python entry points now share the save model. All writes require a flushed, byte-verified Local State backup plus a backup of existing favourites settings; failed backup aborts before source writes, including settings-only changes. True no-ops write nothing. Regression fixtures compare the full Local State except name fields, preserve synthetic encryption/account fields, and byte-compare synthetic password, preferences, cookies, sync and extension files. Tests also cover failed/corrupt backups and running-browser rejection. Automatic backups cover only files this tool overwrites, not a full browser/password backup.

Real password/autofill, sign-in, sync and policy continuity are REQUIRED but NOT RUN; [acceptance checklist](docs/profile-preservation-validation.md). Synthetic file preservation cannot certify these behaviours. Latest hardening is in PR #5; do not treat earlier PR #3 alone as satisfying this requirement.

## Remaining acceptance and limitations

Earlier lack of Tk/display support was resolved for tests using packages unpacked under temporary storage, without a system installation. Real Tk window creation, generated mouse drag/drop, save/reset flows and the 780×560 minimum layout now pass under Linux/Xvfb. This is automated widget evidence, not manual native-platform acceptance. Full native keyboard/accessibility/scaling behaviour remains NOT RUN. Native Windows/macOS GUI, Windows PowerShell 5.1 and disposable-browser integration NOT RUN. Maintainer owns access to those environments. Numeric names do not guarantee Edge's visual ordering. Platform collation can differ. Browser data and settings are separate writes; recovery guidance is in README. Source GUI requires Python with Tk; launchers handle setup. Native app artifacts are being added and must pass their build/smoke checks before use.

## First-test polish

Maintainer asked for polish/optimisation before the first test. Added a pending-name count, no-op Apply disabling, copyable persistent backup path, discard prompts for edited starred order, stale-list clearing on load failure, clearer startup errors and input-shape validation. Extracted the window builder so actual widgets can be exercised. Real-widget tests caught clipped controls at minimum size; switched the outer layout to a grid with reserved rows and confirmed Apply and backup controls stay visible at 780×560. Temporary test packages/runtime are under `/tmp/edge-gui-test-deps` (not authoritative project files); tests live in the repository and can run with standard installed Tk/Xvfb. All 17 checks pass with the temporary runtime. No real browser data was used.

## Simplified installation and usage

A Tk-free Python installation prompted dependency-aware launchers. Added executable Finder launchers (**Try Demo.command**, **Start Edge Profile Organiser.command**) that find a Tk-enabled runtime, offer Homebrew setup when available, or direct users to the official Tk-inclusive Python installer. No browser changes are applied automatically. Added native Apple Silicon/Intel CI packaging with pinned PyInstaller, embedded Python/Tk, separate demo/real apps, frozen-runtime smoke tests and downloadable development artifacts. Builds are ad-hoc signed, not Developer ID signed/notarized; no signing credentials or stable release publication configured. Source-launcher syntax/argument checks and all 18 local tests pass, including actual widgets under Linux/Xvfb. Native packaging results pending the first GitHub build; do not claim available bundles until it succeeds.

## Next action

Review CLI PR #3 and its dependent GUI PR. On Windows/macOS with Tk, launch the GUI using `--demo`, verify drag-to-star/unstar, favourite reordering, preview and apply/reload. Then test copied real-world fixtures and disposable Edge profiles, checking restart persistence, saved-password/autofill continuity, account and sync health, unchanged policies and backup recovery using the preservation checklist before wider use.

## Branch and local work

GUI work is on `feat/profile-order-gui`, branched from clean, synchronized `feat/starred-profile-order` at `194a3f7`. It depends on PR #3 and will be submitted with that branch as its PR base, keeping the GUI diff separate. Tracks [issue #4](https://github.com/xander-me/MicrosoftEdge/issues/4). No earlier work was moved or overwritten. Implementation and validation are committed and pushed in [PR #5](https://github.com/xander-me/MicrosoftEdge/pull/5), targeting `feat/starred-profile-order`. Both PRs remain open. After #3 merges, retarget #5 to main before merging it. No local/unpushed work remains after this handoff update.
