#!/usr/bin/env python3
"""Preview and apply Edge profile numbering, with remembered favourites first."""
import argparse
from pathlib import Path
from profile_order import ProfileSession


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--local-state', type=Path, default=Path.home() /
                        'Library/Application Support/Microsoft Edge/Local State')
    args = parser.parse_args()
    path = args.local_state
    session = ProfileSession(path)
    profiles = session.profiles
    starred = session.starred
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
    session.starred = starred
    print('\nProposed names:')
    for index, profile in enumerate((p for p, _ in session.preview()), 1):
        name = f"{index:02d} - {profile['clean']}"
        print(f"{profile['name']} -> {name}")
    if input('Close Edge completely. Apply names and save starred order? [y/N] ').strip().lower() != 'y':
        print('Cancelled; no files changed.')
        return
    backup = session.apply()
    if backup:
        print(f'Backup created and verified: {backup}')
    else:
        print('Names and favourites already match; no files changed.')
    print(f'Starred order saved: {session.settings}')



if __name__ == '__main__':
    main()
