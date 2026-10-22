# Mac terminal usage

The active tool uses Python 3.10+ with its standard library. Tk, pip and Homebrew setup are unnecessary. Do not use the earlier GUI app downloads for the current terminal flow.

From your existing checkout:

```sh
git switch feat/profile-order-gui
git pull --ff-only
python3 ProfileOrg/EdgeProfileOrg_V1.0.py --demo
```

The branch name is historical; the default interface is now Terminal. Use S/M/U to set favourites and move a new profile to the top. Use A to preview/confirm, B for backup of ALL profiles, D for backed-up native removal, R for refresh and Q to quit. Demo D is disabled; B backs up all synthetic profiles without asking for a profile number. Demo source files and default backups disappear on exit; backups to a chosen external destination persist.

After the demo, close Edge completely and launch real-profile mode:

```sh
python3 ProfileOrg/EdgeProfileOrg_V1.0.py
```

Finder alternatives: double-click **Try Demo.command** or **Start Edge Profile Organiser.command**. They locate Python and open the same terminal menu; they do not install anything or apply changes automatically.

If macOS reports Operation not permitted, this is still an OS file-access restriction, not proof Edge is running. The process now runs under your terminal app. Review its access in Privacy & Security; no automatic permission changes or sudo are used. Exact privacy/file-permission diagnosis on Alexander's Mac remains unconfirmed.

## Back up all profiles before the first real test

Quit Edge completely. In the terminal menu choose **B — Back up ALL profiles**, choose the destination folder (or Enter for the default), then confirm with `y`. No profile number is needed. Version `0.5.0-terminal` or later provides this all-profile flow.

The tool snapshots registered profile folders plus Local State and existing organiser settings for recovery. Other shared/root files and unregistered folders are excluded. Complete profile folders include their caches. It checks space, flushes copied files, verifies hashes and confirms included source data stayed unchanged. Symlinks stop the backup. Existing backups are never overwritten.

A successful snapshot is stored in the folder you choose; the default is **Edge Profile Organiser Backups**, beside the source data directory. The destination prompt accepts a folder on your Mac or external drive. New destination folders can be created, including on an external drive. The tool rejects a destination inside the source directory and checks space on the selected volume. The displayed backup size is an uncompressed full copy, including caches inside registered profile folders; the largest included folders/files are listed after scanning. The terminal prints its path. It contains **User Data/** and **READY.json**. Treat a copy without READY.json as incomplete. The backup stays local and contains sensitive browser data. It does not include macOS Keychain, externally stored system policies or remote sync data; it is intended for the same Mac and OS account, not password migration to another machine.

For recovery, close Edge and independently preserve current data first. Restore only the profile folders and support files listed in READY.json into the recorded original_user_data location. Do not replace the entire Edge data root with this profile-only snapshot; unrelated shared files were not backed up. Restoring Local State restores its whole profile registry at snapshot time, so later additions/removals need reconciliation. Real-user recovery remains an acceptance test.

## Local State changed, even with Edge closed

Closing Edge can save a new Local State after the organiser first loads it. The organiser detects this as a stale preview; it does not mean Edge is necessarily still running. Choose **R (Refresh)** to reload while keeping your proposed favourite order by folder ID. **A (Apply)** also detects changes and refreshes the preview without writing; review it and choose A again. Added/removed profiles are reflected in the fresh preview. Q asks before discarding an edited starred order. If repeated refreshes keep detecting new changes, keep Edge closed and investigate the writer rather than bypassing the guard.

## Back up and remove a local profile

Choose **D**, then select a profile by its displayed list number. Close Edge first. The organiser copies the selected profile's complete local directory, Local State and any favourites settings to **Edge Profile Organiser Backups** beside the Edge user-data directory, then verifies file hashes and flushes copied data. It does not alter the source profile. Backup runs in Terminal; wait for verification to finish. A `READY.json` marker is created only after successful verification. Incomplete backups must not be used as validated recovery copies.

After verification, choose whether to open Edge. The selected profile's native settings screen opens; use Edge's Remove control and confirm there. Edge handles account cleanup and managed restrictions. The organiser sends no cloud-data deletion request. Demo/copy-file modes never open removal against real profiles, and only the standard Edge data location supports this flow. This feature backs up data; it does not bypass Edge policies or directly delete folders/profile registration.

Keep the private backup locally; it contains sensitive browser data. To recover on the same Mac/OS account: close Edge, independently back up its current data, then restore the selected profile folder and the snapshot's Local State and organiser settings to their original locations (remove organiser settings only if `settings_existed` in READY.json is false). Restoring the full Local State also restores its entire profile registry at the snapshot time, so do not overwrite a later state after creating/removing other profiles without reconciling those changes. The backup does not include macOS Keychain or remote sync state. Native removal/recovery and password/sync/policy continuity remain required real-browser acceptance tests.

## Live preview (0.6.0)

In Terminal.app, use arrows to select, Space to star/unstar, M to pin first, and -/+ to move within the starred group. The proposed rows and numbers update immediately. A saves only after confirmation and verified backups. B asks where to store the profile-only snapshot. Use --plain for the earlier numbered-command menu.
