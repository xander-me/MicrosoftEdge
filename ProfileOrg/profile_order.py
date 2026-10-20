"""Shared profile ordering and safe file writes for the CLI and GUI."""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from uuid import uuid4


def profiles_from(data):
    if not isinstance(data, dict) or not isinstance(data.get('profile'), dict):
        raise ValueError('Invalid Local State: expected a profile object.')
    cache = data['profile'].get('info_cache', {})
    if not isinstance(cache, dict) or not cache:
        raise ValueError('No Edge profiles found in Local State.')
    profiles = []
    for folder, info in cache.items():
        if not isinstance(info, dict):
            raise ValueError(f'Invalid profile data: {folder}')
        name = info.get('name', folder)
        if not isinstance(name, str):
            raise ValueError(f'Invalid profile name: {folder}')
        match = re.match(r'^(\d+)\s*-\s*', name)
        profiles.append(dict(folder=folder, name=name,
                             clean=re.sub(r'^\d+\s*-\s*', '', name),
                             number=int(match[1]) if match else None))
    return sorted(profiles, key=lambda p: (p['number'] is None,
                  p['number'] or 0, p['clean'].casefold(), p['folder']))


def ordered_profiles(profiles, starred):
    by_folder = {p['folder']: p for p in profiles}
    first = [by_folder[f] for f in starred if f in by_folder]
    return first + sorted((p for p in profiles if p['folder'] not in starred),
                          key=lambda p: (p['clean'].casefold(), p['folder']))


def atomic_json(path, data):
    fd, temporary = tempfile.mkstemp(dir=path.parent, prefix=path.name + '.temp-')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            json.dump(data, stream, ensure_ascii=False, indent=2)
            stream.flush()
            os.fsync(stream.fileno())
        if path.exists():
            shutil.copymode(path, temporary)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def verified_backup(path, expected, token):
    """Create an exclusive, flushed, byte-verified copy before allowing writes."""
    backup = path.with_name(path.name + '.backup-before-profile-prefix-' + token)
    with backup.open('xb') as stream:
        stream.write(expected)
        stream.flush()
        os.fsync(stream.fileno())
    shutil.copymode(path, backup)
    if backup.read_bytes() != expected:
        raise OSError(f'Backup verification failed: {backup}. No changes applied.')
    return backup


def default_local_state():
    import sys
    if sys.platform == 'win32':
        return Path(os.environ['LOCALAPPDATA']) / 'Microsoft/Edge/User Data/Local State'
    return Path.home() / 'Library/Application Support/Microsoft Edge/Local State'


def require_edge_closed():
    if sys.platform == 'win32':
        result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq msedge.exe', '/FO', 'CSV', '/NH'],
                                capture_output=True, text=True,
                                creationflags=subprocess.CREATE_NO_WINDOW)
        if result.returncode != 0:
            raise OSError('Could not verify that Edge is closed. No changes applied.')
        running = 'msedge.exe' in result.stdout.lower()
    elif sys.platform == 'darwin':
        result = subprocess.run(['pgrep', '-f', r'Microsoft Edge\.app/Contents/'],
                                capture_output=True, text=True)
        if result.returncode not in (0, 1):
            raise OSError('Could not verify that Edge is closed. No changes applied.')
        running = result.returncode == 0
    else:
        return
    if running:
        raise ValueError('Close Edge completely, including background processes, before applying changes.')


class ProfileSession:
    """An in-memory preview. Only apply() writes browser data or settings."""

    def __init__(self, path, check_browser=True):
        self.check_browser = check_browser
        self.path = Path(path)
        self.original = self.path.read_bytes()
        self.data = json.loads(self.original)
        self.profiles = profiles_from(self.data)
        self.settings = self.path.with_name('EdgeProfileOrg.settings.json')
        self.original_settings = self.settings.read_bytes() if self.settings.exists() else None
        saved = json.loads(self.original_settings.decode('utf-8-sig')) if self.original_settings is not None else {}
        if not isinstance(saved, dict):
            raise ValueError('Invalid starred profile settings: expected an object.')
        stars = saved.get('starred', [])
        if not isinstance(stars, list) or any(not isinstance(f, str) for f in stars) or len(set(stars)) != len(stars):
            raise ValueError('Invalid starred profile settings.')
        self.starred = [f for f in stars if f in {p['folder'] for p in self.profiles}]
        self.backup = None
        self.initial_starred = list(self.starred)

    def pin(self, folder, position=None):
        if folder not in {p['folder'] for p in self.profiles}:
            raise ValueError('Unknown profile.')
        if folder in self.starred:
            self.starred.remove(folder)
        if position is None:
            position = len(self.starred)
        self.starred.insert(max(0, min(position, len(self.starred))), folder)

    def unpin(self, folder):
        if folder in self.starred:
            self.starred.remove(folder)

    def preview(self):
        return [(p, f"{i:02d} - {p['clean']}") for i, p in
                enumerate(ordered_profiles(self.profiles, self.starred), 1)]

    @property
    def rename_count(self):
        return sum(profile['name'] != name for profile, name in self.preview())

    @property
    def has_unsaved_edits(self):
        return self.starred != self.initial_starred

    @property
    def needs_save(self):
        return bool(self.rename_count or self.original_settings is None or
                    json.loads(self.original_settings.decode('utf-8-sig')) != {'starred': self.starred})

    def refresh_if_changed(self):
        """Reload fresh data without writing; preserve explicit favourite edits by ID."""
        if self.check_browser:
            require_edge_closed()
        latest = ProfileSession(self.path, check_browser=self.check_browser)
        if latest.original == self.original and latest.original_settings == self.original_settings:
            return False
        if self.has_unsaved_edits:
            existing = {p['folder'] for p in latest.profiles}
            latest.starred = [folder for folder in self.starred if folder in existing]
        self.__dict__.update(latest.__dict__)
        return True

    def apply(self):
        if self.check_browser:
            require_edge_closed()
        if self.path.read_bytes() != self.original:
            raise ValueError('Local State changed. Close Edge and reload before applying.')
        current_settings = self.settings.read_bytes() if self.settings.exists() else None
        if current_settings != self.original_settings:
            raise ValueError('Saved favourites changed. Reload before applying.')
        proposed = self.preview()
        changed = any(p['name'] != name for p, name in proposed)
        desired_settings = {'starred': self.starred}
        if not changed and self.original_settings is not None and json.loads(self.original_settings.decode('utf-8-sig')) == desired_settings:
            return None
        # Back up every file we overwrite, including settings-only changes.
        token = uuid4().hex
        self.backup = verified_backup(self.path, self.original, token)
        if self.original_settings is not None:
            verified_backup(self.settings, self.original_settings, token)
        if self.path.read_bytes() != self.original or (self.settings.read_bytes() if self.settings.exists() else None) != self.original_settings:
            raise ValueError('Files changed during backup. Reload before applying.')
        if self.check_browser:
            require_edge_closed()
        # Rebuild from the original: only the existing profile name fields change.
        updated = json.loads(self.original)
        for profile, name in proposed:
            updated['profile']['info_cache'][profile['folder']]['name'] = name
        if changed:
            atomic_json(self.path, updated)
        try:
            atomic_json(self.settings, desired_settings)
        except OSError as error:
            raise OSError(f'Could not save favourites. Names may already have been applied. '
                          f'Backup: {self.backup}. Reload before retrying. {error}') from error
        return self.backup
