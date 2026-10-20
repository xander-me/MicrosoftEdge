# MicrosoftEdge — current work and handoff

Updated: 2026-10-20. Owner: Maintainer. State: Profile ordering implemented on a task branch; browser acceptance pending. [Scope](README.md).

## Objective and authorization

Maintainer requested detection of existing profile order and the option to promote new profiles, with starred profiles first and the remainder A–Z. Both platform scripts now support an interactive preview and confirmed application. Remembering favourites is the implementation default pending any preference correction.

## Completed and evidence

- Existing numeric prefixes are detected and displayed, including partial numbering and duplicate counts. Existing numbering does not imply favourite status.
- Users select favourites in top-first order; stable folder IDs persist beside Local State. Enter retains favourites; `none` clears them. Remaining profiles sort alphabetically.
- Cancel performs no writes. Changed Local State receives a unique backup. Unchanged names avoid a rewrite. Both scripts detect changes during preview; Windows requires Edge to be closed instead of force-stopping it. Python uses temporary-file replacement.
- `python3 -m unittest discover -s tests -v`: passed both Python and PowerShell CLI fixture tests on Linux using Python 3 and pwsh. Tests cover invalid choices, cancellation, promotion, persistence, newly added profiles, clearing favourites, unrelated data and exact backup restoration.
- Earlier documentation handoff PR #1 is merged; the old pending-rollout status is superseded.

## Remaining acceptance and limitations

Windows PowerShell 5.1, representative real-world Local State fixtures, and disposable-browser Windows/macOS integration: NOT RUN. Maintainer owns access to those environments. Name numbering is detected; Edge’s internal visual order is not queried. Sorting uses platform collation. Local State and favourite settings are separate writes; see README recovery guidance.

## Next action

Review the task PR, then verify preview/apply/restart and backup recovery using disposable Edge profiles on Windows and macOS. Confirm that the browser retains the names and displays the intended order before wider use.

## Branch and local work

Work is on `feat/starred-profile-order`, based on synchronized main `6a3b590`. Checkout was clean at session start; no pre-existing work was moved. Changes will be committed and published through a PR; see the live repository PR list for review status. No real browser data was accessed or changed.
