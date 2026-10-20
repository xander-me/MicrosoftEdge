"""Verified local backup followed by Edge's native profile-removal screen.

Never directly delete folders or edit Edge's profile registration/policy records.
"""
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from profile_order import atomic_json, require_edge_closed


def fingerprint(folder):
    """Hash every regular file, retaining directory names; refuse linked/special data."""
    result = {}
    for path in sorted(folder.rglob('*')):
        key = path.relative_to(folder).as_posix()
        if path.is_symlink():
            raise ValueError(f'Profile contains a symbolic link; backup cannot be guaranteed: {key}')
        if path.is_dir():
            result[key] = {'directory': True}
        elif path.is_file():
            digest = hashlib.sha256()
            with path.open('rb') as stream:
                for chunk in iter(lambda: stream.read(1024 * 1024), b''):
                    digest.update(chunk)
            result[key] = {'bytes': path.stat().st_size, 'sha256': digest.hexdigest()}
        else:
            raise ValueError(f'Profile contains an unsupported file: {key}')
    return result


def durable_copy(source, destination):
    shutil.copyfile(source, destination)
    with open(destination, 'r+b') as stream:
        stream.flush()
        os.fsync(stream.fileno())
    shutil.copystat(source, destination)
    return destination


def backup_for_removal(session, folder):
    if session.check_browser:
        require_edge_closed()
    if folder not in {p['folder'] for p in session.profiles}:
        raise ValueError('Unknown profile. Refresh the list first.')
    if not folder or folder in ('.', '..') or '/' in folder or '\\' in folder:
        raise ValueError('Invalid profile folder ID.')
    root = session.path.parent.resolve()
    source = root / folder
    if source.is_symlink() or source.resolve().parent != root or not source.is_dir():
        raise ValueError('The profile folder is missing or linked. No removal screen was opened.')
    if session.path.read_bytes() != session.original or (session.settings.read_bytes() if session.settings.exists() else None) != session.original_settings:
        raise ValueError('Files changed. Refresh the preview before backing up.')
    before = fingerprint(source)
    backup_root = root.parent / 'Edge Profile Organiser Backups'
    backup_root.mkdir(mode=0o700, exist_ok=True)
    if backup_root.is_symlink():
        raise ValueError('Backup location is linked. No removal screen was opened.')
    backup = Path(tempfile.mkdtemp(prefix='profile-', dir=backup_root))
    # A READY.json marker is written only after every copy and concurrency check passes.
    shutil.copytree(source, backup / folder, copy_function=durable_copy)
    if fingerprint(backup / folder) != before or fingerprint(source) != before:
        raise OSError(f'Profile changed or backup verification failed. No removal screen opened. Incomplete backup: {backup}')
    for path, expected in ((session.path, session.original), (session.settings, session.original_settings)):
        if expected is None:
            continue
        destination = backup / path.name
        with destination.open('xb') as stream:
            stream.write(expected)
            stream.flush()
            os.fsync(stream.fileno())
        shutil.copymode(path, destination)
        if destination.read_bytes() != expected:
            raise OSError(f'Backup verification failed: {destination}')
    if session.check_browser:
        require_edge_closed()
    if session.path.read_bytes() != session.original or (session.settings.read_bytes() if session.settings.exists() else None) != session.original_settings:
        raise ValueError(f'Files changed during backup. No removal screen opened. Incomplete backup: {backup}')
    atomic_json(backup / 'READY.json', {
        'created_utc': datetime.now(timezone.utc).isoformat(),
        'profile_folder': folder,
        'original_user_data': str(root),
        'settings_existed': session.original_settings is not None,
        'files': before,
        'local_state_sha256': hashlib.sha256(session.original).hexdigest(),
        'settings_sha256': hashlib.sha256(session.original_settings).hexdigest() if session.original_settings is not None else None,
        'purpose': 'Local recovery on the same machine and OS account before native Edge profile removal',
    })
    return backup


def open_native_removal(folder):
    """Open the selected profile's settings; the user and Edge confirm removal."""
    require_edge_closed()
    arguments = [f'--profile-directory={folder}', 'edge://settings/profiles']
    if sys.platform == 'darwin':
        subprocess.run(['/usr/bin/open', '-a', 'Microsoft Edge', '--args', *arguments], check=True)
    elif sys.platform == 'win32':
        candidates = [Path(os.environ.get(key, '')) / tail for key, tail in (
            ('PROGRAMFILES(X86)', 'Microsoft/Edge/Application/msedge.exe'),
            ('PROGRAMFILES', 'Microsoft/Edge/Application/msedge.exe'),
            ('LOCALAPPDATA', 'Microsoft/Edge/Application/msedge.exe')) if os.environ.get(key)]
        executable = next((path for path in candidates if path.is_file()), None)
        if executable is None:
            raise OSError('Edge executable not found. Your backup is complete; open Edge profile settings manually.')
        subprocess.Popen([str(executable), *arguments])
    else:
        raise OSError('Open Edge profile settings manually. Your backup is complete.')
