# Mac first run

## Standalone app — no Python, Tk, Homebrew or Terminal required

1. Open the [first successful Mac app build](https://github.com/xander-me/MicrosoftEdge/actions/runs/39389135624) (or a newer successful **Mac app** run in Actions). Download the artifact matching **Apple Silicon** (M1/M2/M3/M4/etc.) or **Intel**, as shown in Apple menu → About This Mac.
2. Unzip the artifact, then unzip the `Edge-Profile-Organiser-*.zip` inside it. Keep the app bundles intact. The package includes **Edge Profile Organiser Demo.app** and **Edge Profile Organiser.app**.
3. Double-click **Edge Profile Organiser Demo.app** first. This uses disposable sample profiles; try dragging, starring, applying and reloading. Demo data disappears when the app closes.
4. These development builds are ad-hoc signed, not Developer ID signed/notarized. macOS may require approving the specific app in System Settings → Privacy & Security after the first launch attempt. Do not disable Gatekeeper system-wide. No signing credentials are configured.
5. Once the demo works, close Edge completely and make an independent backup of your Edge user-data folder. Open **Edge Profile Organiser.app**, review every proposed name and apply only when correct. It verifies backups of Local State and organiser settings before writing either file.
6. Reopen Edge and verify account identity, saved-password autofill, sync status, bookmarks/extensions and managed policies. See [the repository preservation checklist](https://github.com/xander-me/MicrosoftEdge/blob/feat/profile-order-gui/docs/profile-preservation-validation.md). Native compatibility is still under acceptance testing.

The standalone apps contain their own Python and Tcl/Tk. They do not install or modify your system Python or Homebrew. Packaging checks do not prove password/sync/policy continuity.

## Existing source checkout — dependency-aware double-click launchers

Update your `feat/profile-order-gui` checkout, then double-click **Try Demo.command** in Finder. Use **Start Edge Profile Organiser.command** for actual profiles. These work from the repository folder, including paths containing spaces; keep the folder contents together.

The launcher first checks installed Python/Tk runtimes. If missing and Homebrew is installed, it offers to run `brew install python-tk@3.14`, then launches with that exact Python. It does not install Homebrew. If Homebrew is absent, it offers the official Python macOS download page; that installer includes Tk. After completing that installer, double-click the launcher again. Setup/launch never applies profile changes automatically.

If the launcher is blocked by macOS, approve only this downloaded file in Privacy & Security. Errors remain visible in Terminal. No `pip install tkinter`, interpreter selection or manual Python commands are required.

## Building from source (maintainers)

On macOS with a Tk-enabled Python, run `scripts/build-mac.sh`. Set `EDGE_ORGANIZER_PYTHON` to a specific interpreter if needed. The script creates an isolated build environment, installs the pinned build requirements, and writes both apps to `dist/`. GitHub Actions builds Apple Silicon and Intel separately, runs regression/widget tests and smoke-checks both frozen Tcl/Tk runtimes before uploading artifacts. Artifacts are development builds retained for 30 days, not a published stable release. A successful build/run link and commit should be recorded in STATUS.md.
