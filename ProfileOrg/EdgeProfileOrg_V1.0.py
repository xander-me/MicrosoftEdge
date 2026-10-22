#!/usr/bin/env python3
"""Preview and apply Edge profile numbering, with remembered favourites first."""
import argparse
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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--local-state', type=Path, default=Path.home() /
                        'Library/Application Support/Microsoft Edge/Local State')
    args = parser.parse_args()
    path = args.local_state
    original = path.read_bytes()
    data = json.loads(original)
    profiles = profiles_from(data)
    settings = path.with_name('EdgeProfileOrg.settings.json')
    saved = json.loads(settings.read_text(encoding='utf-8-sig')) if settings.exists() else {}
    starred = saved.get('starred', [])
    if not isinstance(starred, list) or any(not isinstance(f, str) for f in starred) or len(set(starred)) != len(starred):
        raise ValueError('Invalid starred profile settings.')
    numbers = [p['number'] for p in profiles if p['number'] is not None]
    print(f'Existing numbering: {len(numbers)}/{len(profiles)} profiles; '
          f'{len(numbers) - len(set(numbers))} duplicate numbers.')
    for index, profile in enumerate(profiles, 1):
        marker = '*' if profile['folder'] in starred else ' '
        print(f"{index}. {marker} {profile['name']} [{profile['folder']}]")
    while True:
        choice = input('Starred profiles in top-first order (e.g. 3,1); Enter keeps saved stars; none clears: ').strip()
        if not choice:
            break
        if choice.lower() == 'none':
            starred = []
            break
        try:
            selected = [int(value.strip()) for value in choice.split(',')]
            if len(set(selected)) != len(selected) or any(i < 1 or i > len(profiles) for i in selected):
                raise ValueError()
            starred = [profiles[i - 1]['folder'] for i in selected]
            break
        except ValueError:
            print('Enter unique list numbers separated by commas.')
    starred = [f for f in starred if any(p['folder'] == f for p in profiles)]
    changed = False
    print('\nProposed names:')
    for index, profile in enumerate(ordered_profiles(profiles, starred), 1):
        name = f"{index:02d} - {profile['clean']}"
        print(f"{profile['name']} -> {name}")
        changed |= profile['name'] != name
        data['profile']['info_cache'][profile['folder']]['name'] = name
    if input('Close Edge completely. Apply names and save starred order? [y/N] ').strip().lower() != 'y':
        print('Cancelled; no files changed.')
        return
    if path.read_bytes() != original:
        raise ValueError('Local State changed during preview. Run again with Edge closed.')
    if changed:
        backup = path.with_name(path.name + '.backup-before-profile-prefix-' + uuid4().hex)
        shutil.copy2(path, backup)
        print(f'Backup created: {backup}')
        atomic_json(path, data)
    else:
        print('Profile names already match; Local State unchanged.')
    atomic_json(settings, {'starred': starred})
    print(f'Starred order saved: {settings}')


if __name__ == '__main__':
    main()
