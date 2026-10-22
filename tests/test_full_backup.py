"""All-profile snapshots must include shared data and never report partial copies ready."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'ProfileOrg'))
from profile_order import ProfileSession
from profile_backup import backup_all_profiles


class FullBackupTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'Edge Data'
        self.root.mkdir()
        self.path = self.root / 'Local State'
        self.path.write_text(json.dumps({'os_crypt': {'encrypted_key': 'SYNTHETIC'}, 'profile': {
            'info_cache': {'Default': {'name': 'Personal'}, 'Profile 1': {'name': 'Work'}}}}))
        for name in ('Default/Login Data', 'Default/Network/Cookies', 'Profile 1/Preferences', 'Shared Dictionary/data', 'Unregistered profile/Bookmarks'):
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b'synthetic ' + name.encode())
        self.session = ProfileSession(self.path, check_browser=False)

    def test_all_profiles_shared_and_unregistered_data_are_preserved(self):
        original = {p.relative_to(self.root): p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        backup = backup_all_profiles(self.session)
        manifest = json.loads((backup / 'READY.json').read_bytes())
        self.assertEqual(manifest['profiles'], ['Default', 'Profile 1'])
        self.assertEqual(manifest['file_count'], len(original))
        for name, content in original.items():
            self.assertEqual((backup / 'User Data' / name).read_bytes(), content)
            self.assertEqual((self.root / name).read_bytes(), content)
        first_manifest_bytes = (backup / 'READY.json').read_bytes()
        second = backup_all_profiles(self.session)
        self.assertNotEqual(backup, second)
        self.assertEqual((backup / 'READY.json').read_bytes(), first_manifest_bytes)

    def test_custom_destination_contains_complete_snapshot(self):
        target = Path(self.temp.name) / 'Other disk' / 'Snapshots'
        backup = backup_all_profiles(self.session, destination=target)
        self.assertTrue(backup.parent.samefile(target))
        self.assertTrue((backup / 'READY.json').exists())
        self.assertEqual((backup / 'User Data/Local State').read_bytes(), self.path.read_bytes())
        self.assertFalse((Path(self.temp.name) / 'Edge Profile Organiser Backups').exists())

    def test_destination_inside_source_is_refused_before_copy(self):
        with patch('profile_backup.shutil.copytree') as copied:
            for target in (self.root, self.root / 'nested-backup'):
                with self.subTest(target=target):
                    with self.assertRaisesRegex(ValueError, 'outside Edge data'):
                        backup_all_profiles(self.session, destination=target)
        copied.assert_not_called()
        self.assertFalse((self.root / 'nested-backup').exists())

    def test_copy_failure_never_marks_ready(self):
        with patch('profile_backup.shutil.copytree', side_effect=OSError('disk full')):
            with self.assertRaisesRegex(OSError, 'incomplete copy'):
                backup_all_profiles(self.session)
        self.assertFalse(list(Path(self.temp.name).rglob('READY.json')))
        self.assertTrue((self.root / 'Default/Login Data').exists())

    def test_corruption_or_concurrent_change_never_marks_ready(self):
        import profile_backup
        actual = profile_backup.durable_copy
        for change_source in (False, True):
            with self.subTest(change_source=change_source):
                def change(source, destination):
                    result = actual(source, destination)
                    if Path(source).name == 'Login Data':
                        Path(source if change_source else destination).write_bytes(b'changed')
                    return result
                with patch('profile_backup.durable_copy', side_effect=change):
                    with self.assertRaisesRegex(OSError, 'incomplete copy'):
                        backup_all_profiles(self.session)
                self.assertFalse(list(Path(self.temp.name).rglob('READY.json')))

    def test_low_disk_space_stops_before_copy(self):
        from collections import namedtuple
        usage = namedtuple('usage', 'total used free')(100, 100, 0)
        with patch('profile_backup.shutil.disk_usage', return_value=usage), patch('profile_backup.shutil.copytree') as copied:
            with self.assertRaisesRegex(OSError, 'Not enough free disk space'):
                backup_all_profiles(self.session)
        copied.assert_not_called()

    def test_runtime_links_preserved_but_profile_links_refused(self):
        try:
            (self.root / 'RunningChromeVersion').symlink_to('999.0-synthetic')
        except OSError:
            self.skipTest('Symlinks unavailable')
        backup = backup_all_profiles(self.session)
        self.assertEqual((backup / 'User Data/RunningChromeVersion').readlink(), Path('999.0-synthetic'))
        (self.root / 'linked-profile').symlink_to(self.root / 'Default', target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'symbolic link'):
            backup_all_profiles(self.session)

    def test_running_edge_prevents_copy(self):
        self.session.check_browser = True
        with patch('profile_backup.require_edge_closed', side_effect=ValueError('Close Edge completely')), patch('profile_backup.shutil.copytree') as copied:
            with self.assertRaisesRegex(ValueError, 'Close Edge completely'):
                backup_all_profiles(self.session)
        copied.assert_not_called()
