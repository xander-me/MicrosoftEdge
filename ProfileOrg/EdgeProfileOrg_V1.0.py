#!/usr/bin/env python3
"""Preview and apply Edge profile numbering, with remembered favourites first."""
import argparse
import json
import shutil
from pathlib import Path
from uuid import uuid4
from profile_order import profiles_from, ordered_profiles, atomic_json


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
