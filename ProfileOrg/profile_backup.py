"""Verified snapshots of registered Edge profiles and essential recovery metadata."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import shutil
import tempfile
from profile_order import atomic_json, require_edge_closed
from profile_removal import durable_copy, fingerprint


def backup_destination(root, destination=None):
    root = Path(root).resolve()
    target = Path(destination).expanduser() if destination is not None else root.parent / 'Edge Profile Organiser Backups'
    if target.is_symlink() or target.resolve() == root or root in target.resolve().parents:
        raise ValueError('Choose a backup folder outside Edge data that is not a symbolic link.')
    if target.exists() and not target.is_dir():
        raise ValueError('Choose a destination folder, not an existing file.')
    return target.resolve()


def size_label(size):
    return f'{size / (1024 ** 3):.1f} GiB' if size >= 1024 ** 3 else f'{size / (1024 ** 2):.1f} MiB'


def profile_scope(session):
    root = session.path.parent.resolve()
    folders = [profile['folder'] for profile in session.profiles]
    for folder in folders:
        path = root / folder
        if not folder or folder in ('.', '..') or '/' in folder or '\\' in folder or path.is_symlink() or path.resolve().parent != root or not path.is_dir():
            raise ValueError(f'Profile folder is missing, linked or unsafe: {folder}. Backup stopped.')
    support = [session.path.name]
    if session.original_settings is not None:
        support.append(session.settings.name)
    return folders, support


def scoped_fingerprint(root, folders, support):
    result = {}
    for folder in folders:
        result[folder] = {'directory': True}
        result.update({f'{folder}/{name}': info for name, info in fingerprint(root / folder).items()})
    for name in support:
        path = root / name
        if path.is_symlink() or not path.is_file():
            raise ValueError(f'Recovery metadata is missing or linked: {name}')
        digest = hashlib.sha256()
        with path.open('rb') as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b''):
                digest.update(chunk)
        result[name] = {'bytes': path.stat().st_size, 'sha256': digest.hexdigest()}
    return result


def backup_all_profiles(session, progress=None, destination=None):
    notify = progress or (lambda message: None)
    if session.check_browser:
        require_edge_closed()
    root = session.path.parent.resolve()
    backup_root = backup_destination(root, destination)
    folders, support = profile_scope(session)
    if session.path.read_bytes() != session.original or (session.settings.read_bytes() if session.settings.exists() else None) != session.original_settings:
        raise ValueError('Edge data changed. Refresh before starting the profile backup.')
    notify('Scanning registered profile folders and essential recovery metadata only…')
    before = scoped_fingerprint(root, folders, support)
    total_bytes = sum(item.get('bytes', 0) for item in before.values())
    backup_root.mkdir(mode=0o700, parents=True, exist_ok=True)
    if shutil.disk_usage(backup_root).free < total_bytes + 1024 * 1024:
        raise OSError('Not enough free disk space for a complete profile backup. No source files changed.')
    backup = Path(tempfile.mkdtemp(prefix='profiles-', dir=backup_root))
    snapshot = backup / 'User Data'
    snapshot.mkdir(mode=0o700)
    file_count = sum('sha256' in item for item in before.values())
    groups = {}
    for name, info in before.items():
        group = name.split('/')[0]
        groups[group] = groups.get(group, 0) + info.get('bytes', 0)
    notify('Largest included profiles/files (complete profile folders, including their caches):')
    for name, size in sorted(groups.items(), key=lambda item: item[1], reverse=True)[:6]:
        notify(f'  {size_label(size):>10}  {name}')
    notify(f'Backup destination: {backup}')
    notify(f'Copying {len(folders)} profiles plus {", ".join(support)} ({file_count} files, {size_label(total_bytes)})…')
    try:
        for folder in folders:
            shutil.copytree(root / folder, snapshot / folder, copy_function=durable_copy)
        for name in support:
            durable_copy(root / name, snapshot / name)
        notify('Verifying copied profile data and checking that included source files stayed unchanged…')
        if scoped_fingerprint(snapshot, folders, support) != before:
            raise OSError('Copied profile data did not match its source hashes.')
        if session.check_browser:
            require_edge_closed()
        if scoped_fingerprint(root, folders, support) != before:
            raise ValueError('Included profile data changed during backup. Keep Edge closed and retry.')
        atomic_json(backup / 'READY.json', {
            'backup_type': 'profiles_only',
            'created_utc': datetime.now(timezone.utc).isoformat(),
            'original_user_data': str(root),
            'data_directory': 'User Data',
            'profiles': folders,
            'support_files': support,
            'file_count': file_count,
            'total_bytes': total_bytes,
            'files': before,
            'purpose': 'Registered local profiles and essential metadata; restore included items only on the same machine/OS account',
        })
    except Exception as error:
        raise OSError(f'Profile backup did not complete; do not use this incomplete copy: {backup}. '
                      f'The organiser did not modify source files. {error}') from error
    notify('All included profile files verified. READY.json written.')
    return backup
