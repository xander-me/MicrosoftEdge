#!/usr/bin/env python3
"""Terminal Edge profile organiser: starred profiles first, then A-Z."""
import argparse
import errno
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from profile_order import ProfileSession, default_local_state
from profile_removal import backup_for_removal, open_native_removal
from profile_backup import backup_all_profiles

VERSION = '0.5.0-terminal'


class TerminalOrganizer:
    def __init__(self, path, demo=False):
        self.demo = demo
        self.session = ProfileSession(path, check_browser=not demo)
        self.last_backup = None

    def show(self):
        session = self.session
        numbers = [p['number'] for p in session.profiles if p['number'] is not None]
        print(f'\nEdge Profile Organiser {VERSION}' + (' [DEMO: temporary data]' if self.demo else ''))
        print(f'File: {session.path}')
        print(f'Existing numbering: {len(numbers)}/{len(session.profiles)} profiles; '
              f'{len(numbers) - len(set(numbers))} duplicate numbers.')
        for index, profile in enumerate(session.profiles, 1):
            marker = '*' if profile['folder'] in session.starred else ' '
            print(f"{index:>3}. {marker} {profile['name']} [{profile['folder']}]")
        print('\nPreview:')
        for profile, name in session.preview():
            print(f"  {profile['name']} -> {name}")
        print(f'{session.rename_count} names will change; {len(session.starred)} starred.')
        if self.last_backup:
            print(f'Last verified backup: {self.last_backup}')

    def select(self):
        value = input('Profile list number (Enter cancels): ').strip()
        if not value:
            return None
        if not value.isdecimal() or not 1 <= int(value) <= len(self.session.profiles):
            raise ValueError('Choose a profile number from the displayed list.')
        return self.session.profiles[int(value) - 1]['folder']

    def stars(self):
        while True:
            choice = input('Starred profiles in top-first order (e.g. 3,1); Enter keeps; none clears: ').strip()
            if not choice:
                return
            if choice.lower() == 'none':
                self.session.starred = []
                return
            try:
                selected = [int(value.strip()) for value in choice.split(',')]
                if len(set(selected)) != len(selected) or any(i < 1 or i > len(self.session.profiles) for i in selected):
                    raise ValueError()
                self.session.starred = [self.session.profiles[i - 1]['folder'] for i in selected]
                return
            except ValueError:
                print('Enter unique list numbers separated by commas.')

    def refresh(self):
        changed = self.session.refresh_if_changed()
        print('Latest data loaded; proposed favourites retained where profiles still exist.' if changed else 'No disk changes detected.')
        return changed

    def apply(self):
        if self.refresh():
            print('Review the refreshed preview, then choose Apply again. No files written.')
            return
        self.show()
        if input('Close Edge completely. Apply preview and save favourites? [y/N] ').strip().lower() != 'y':
            print('Cancelled; no files changed.')
            return
        backup = self.session.apply()
        if backup:
            self.last_backup = backup
            print(f'Backup created and verified: {backup}')
        else:
            print('Names and favourites already match; no files changed.')
        print(f'Starred order saved: {self.session.settings}')
        self.session = ProfileSession(self.session.path, check_browser=not self.demo)

    def full_backup(self):
        self.refresh()
        print(f'Back up ALL {len(self.session.profiles)} profiles and all shared Edge data.')
        print(f'Source folder: {self.session.path.parent}')
        print('Keep Edge completely closed. Existing backups are never overwritten.')
        if input('Create and verify a full Edge backup? [y/N] ').strip().lower() != 'y':
            print('Cancelled; no backup or source changes made.')
            return
        self.last_backup = backup_all_profiles(self.session, progress=lambda message: print(message, flush=True))
        print(f'Full backup verified (ALL profiles): {self.last_backup}')

    def backup(self, remove=False):
        if remove and (self.demo or self.session.path.resolve() != default_local_state().resolve()):
            print('Removal is disabled for demo/copied files. You can still test full backup with B.')
            return
        if self.refresh():
            print('Review the refreshed profile list before choosing a profile to back up.')
            return
        folder = self.select()
        if folder is None:
            return
        print(f'Full local backup of [{folder}], Local State and organiser settings. Keep Edge closed.')
        if remove:
            print('After backup verification, you can open Edge and confirm deletion in its own settings. Nothing is deleted automatically.')
        if input('Create and verify backup? [y/N] ').strip().lower() != 'y':
            print('Cancelled; no profile changed.')
            return
        print('Copying, flushing and verifying profile files. This may take time…', flush=True)
        self.last_backup = backup_for_removal(self.session, folder)
        print(f'Full backup verified: {self.last_backup}')
        if remove and input('Open this profile in Edge to confirm removal there? [y/N] ').strip().lower() == 'y':
            open_native_removal(folder)
            print('Complete removal inside Edge. Close Edge, then choose R here to refresh.')

    def report_error(self, error, action):
        print(f'\nCould not complete {action}: {error}', file=sys.stderr)
        if isinstance(error, OSError) and error.errno in (errno.EPERM, errno.EACCES):
            print('The operating system denied file access. Running in Terminal does not bypass macOS privacy controls. '
                  'Review Terminal access in System Settings > Privacy & Security; do not use sudo or change profile permissions.', file=sys.stderr)
        backup = self.session.backup or self.last_backup
        if backup:
            print(f'Last verified backup: {backup}', file=sys.stderr)

    def run(self):
        while True:
            self.show()
            print('\nS Set starred order | M Move/pin | U Unstar | R Refresh')
            print('A Apply | B Back up ALL profiles | D Back up & remove | Q Quit')
            command = input('Choose: ').strip().lower()
            try:
                if command == 'q':
                    if not self.session.has_unsaved_edits or input('Discard unsaved starred order and quit? [y/N] ').strip().lower() == 'y':
                        return
                elif command == 's':
                    self.stars()
                elif command == 'm':
                    folder = self.select()
                    if folder is not None:
                        value = input('Position within starred profiles (1 = top): ').strip()
                        limit = len(self.session.starred) + (folder not in self.session.starred)
                        if not value.isdecimal() or not 1 <= int(value) <= limit:
                            raise ValueError(f'Choose a starred position from 1 to {limit}.')
                        self.session.pin(folder, int(value) - 1)
                elif command == 'u':
                    folder = self.select()
                    if folder is not None:
                        self.session.unpin(folder)
                elif command == 'r':
                    self.refresh()
                elif command == 'a':
                    self.apply()
                elif command == 'b':
                    self.full_backup()
                elif command == 'd':
                    self.backup(remove=True)
                else:
                    print('Choose S, M, U, R, A, B, D or Q.')
            except (OSError, ValueError, subprocess.SubprocessError) as error:
                self.report_error(error, {'a': 'Apply', 'b': 'full backup', 'd': 'profile removal', 'r': 'refresh'}.get(command, 'selection'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--version', action='version', version=VERSION)
    source = parser.add_mutually_exclusive_group()
    source.add_argument('--local-state', type=Path, help='Use a copied Local State file')
    source.add_argument('--demo', action='store_true', help='Use disposable sample profiles; never access real Edge data')
    parser.add_argument('--quick', action='store_true', help='One-shot star selection and apply (legacy CLI flow)')
    args = parser.parse_args()
    organizer = None
    demo = tempfile.TemporaryDirectory(prefix='edge-terminal-demo-') if args.demo else None
    try:
        if demo:
            path = Path(demo.name) / 'User Data' / 'Local State'
            path.parent.mkdir()
            profiles = {'Default': {'name': '01 - Personal'}, 'Profile 1': {'name': '02 - Work'},
                        'Profile 2': {'name': '03 - Customer A'}, 'Profile 3': {'name': 'New customer'}}
            path.write_text(json.dumps({'profile': {'info_cache': profiles}}), encoding='utf-8')
            for folder in profiles:
                (path.parent / folder).mkdir()
                (path.parent / folder / 'Preferences').write_text('{"demo":true}')
        else:
            path = args.local_state or default_local_state()
        try:
            organizer = TerminalOrganizer(path, demo=args.demo)
        except (OSError, ValueError) as error:
            print(f'Cannot load profiles: {error}', file=sys.stderr)
            if isinstance(error, OSError) and error.errno in (errno.EPERM, errno.EACCES):
                print('macOS may need to grant Terminal access to Edge data in System Settings > Privacy & Security. No permissions were changed.', file=sys.stderr)
            return 1
        if args.quick:
            organizer.show()
            organizer.stars()
            organizer.apply()
        else:
            organizer.run()
    except (EOFError, KeyboardInterrupt):
        print('\nExited. Unapplied preview edits were discarded.')
        if organizer and (organizer.session.backup or organizer.last_backup):
            print(f'Last verified backup: {organizer.session.backup or organizer.last_backup}')
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        if organizer:
            organizer.report_error(error, 'operation')
        else:
            print(f'Cannot start organiser: {error}', file=sys.stderr)
        return 1
    finally:
        if demo:
            demo.cleanup()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
