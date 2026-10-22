"""Verified snapshot of the complete Edge user-data directory, without source writes."""
from datetime import datetime, timezone
from pathlib import Path
import shutil
import tempfile
from profile_order import atomic_json, require_edge_closed
from profile_removal import durable_copy, fingerprint

# Chromium runtime markers are links, not browser data. Preserve the links without
# following their targets. Other links stop a full backup rather than omit data.
RUNTIME_LINKS = frozenset({'SingletonLock', 'SingletonCookie', 'SingletonSocket', 'RunningChromeVersion'})


def backup_all_profiles(session, progress=None):
    notify = progress or (lambda message: None)
    if session.check_browser:
        require_edge_closed()
    root = session.path.parent.resolve()
    if session.path.read_bytes() != session.original or (session.settings.read_bytes() if session.settings.exists() else None) != session.original_settings:
        raise ValueError('Edge data changed. Refresh before starting the full backup.')
    notify('Scanning and hashing all Edge profile and shared files…')
    before = fingerprint(root, allowed_links=RUNTIME_LINKS)
    total_bytes = sum(item.get('bytes', 0) for item in before.values())
    backup_root = root.parent / 'Edge Profile Organiser Backups'
    if backup_root.is_symlink() or backup_root.resolve() == root or root in backup_root.resolve().parents:
        raise ValueError('The backup destination must be outside the source and must not be linked.')
    backup_root.mkdir(mode=0o700, exist_ok=True)
    if shutil.disk_usage(backup_root).free < total_bytes + 1024 * 1024:
        raise OSError('Not enough free disk space for a complete Edge backup. No source files changed.')
    backup = Path(tempfile.mkdtemp(prefix='all-profiles-', dir=backup_root))
    snapshot = backup / 'User Data'
    file_count = sum('sha256' in item for item in before.values())
    notify(f'Copying {len(session.profiles)} profiles and shared data ({file_count} files, {total_bytes / (1024 * 1024):.1f} MiB)…')
    try:
        shutil.copytree(root, snapshot, symlinks=True, copy_function=durable_copy)
        notify('Verifying every copied file and checking that the source stayed unchanged…')
        if fingerprint(snapshot, allowed_links=RUNTIME_LINKS) != before:
            raise OSError('Copied Edge data did not match its source hashes.')
        if session.check_browser:
            require_edge_closed()
        if fingerprint(root, allowed_links=RUNTIME_LINKS) != before:
            raise ValueError('Edge data changed during backup. Keep Edge closed and retry.')
        atomic_json(backup / 'READY.json', {
            'backup_type': 'all_profiles',
            'created_utc': datetime.now(timezone.utc).isoformat(),
            'original_user_data': str(root),
            'data_directory': 'User Data',
            'profiles': [profile['folder'] for profile in session.profiles],
            'file_count': file_count,
            'total_bytes': total_bytes,
            'files': before,
            'purpose': 'Complete local Edge user-data snapshot for recovery on the same machine and OS account',
        })
    except Exception as error:
        raise OSError(f'Full backup did not complete; do not use this incomplete copy: {backup}. '
                      f'The organiser did not modify source files. {error}') from error
    notify('All profile and shared files verified. READY.json written.')
    return backup
