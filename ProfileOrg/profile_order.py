"""Shared profile ordering and safe file writes for the CLI and GUI."""
import json
import os
import re
import shutil
import tempfile
from pathlib import Path
from uuid import uuid4


def profiles_from(data):
    cache = data.get('profile', {}).get('info_cache', {})
    if not isinstance(cache, dict) or not cache:
        raise ValueError('No Edge profiles found in Local State.')
    profiles = []
    for folder, info in cache.items():
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


def default_local_state():
    import sys
    if sys.platform == 'win32':
        return Path(os.environ['LOCALAPPDATA']) / 'Microsoft/Edge/User Data/Local State'
    return Path.home() / 'Library/Application Support/Microsoft Edge/Local State'


class ProfileSession:
    """An in-memory preview. Only apply() writes browser data or settings."""

    def __init__(self, path):
        self.path = Path(path)
        self.original = self.path.read_bytes()
        self.data = json.loads(self.original)
        self.profiles = profiles_from(self.data)
        self.settings = self.path.with_name('EdgeProfileOrg.settings.json')
        self.original_settings = self.settings.read_bytes() if self.settings.exists() else None
        saved = json.loads(self.original_settings.decode('utf-8-sig')) if self.original_settings is not None else {}
        stars = saved.get('starred', [])
        if not isinstance(stars, list) or any(not isinstance(f, str) for f in stars) or len(set(stars)) != len(stars):
            raise ValueError('Invalid starred profile settings.')
        self.starred = [f for f in stars if f in {p['folder'] for p in self.profiles}]
        self.backup = None

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

    def apply(self):
        if self.path.read_bytes() != self.original:
            raise ValueError('Local State changed. Close Edge and reload before applying.')
        current_settings = self.settings.read_bytes() if self.settings.exists() else None
        if current_settings != self.original_settings:
            raise ValueError('Saved favourites changed. Reload before applying.')
        changed = any(p['name'] != name for p, name in self.preview())
        if changed:
            self.backup = self.path.with_name(self.path.name + '.backup-before-profile-prefix-' + uuid4().hex)
            shutil.copy2(self.path, self.backup)
            for profile, name in self.preview():
                self.data['profile']['info_cache'][profile['folder']]['name'] = name
            atomic_json(self.path, self.data)
        try:
            atomic_json(self.settings, {'starred': self.starred})
        except OSError as error:
            raise OSError(f'Could not save favourites. Names may already have been applied. '
                          f'Backup: {self.backup}. Reload before retrying. {error}') from error
        return self.backup
