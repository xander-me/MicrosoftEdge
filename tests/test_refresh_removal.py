"""Fresh previews and verified full-profile backup must not mutate source data."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'ProfileOrg'))
from profile_order import ProfileSession
from profile_removal import backup_for_removal


class RefreshRemovalTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'User Data' / 'Local State'
        self.path.parent.mkdir()
        self.data = {'os_crypt': {'encrypted_key': 'SYNTHETIC'}, 'profile': {'info_cache': {
            'Default': {'name': '01 - Alpha'}, 'Profile 1': {'name': 'Beta'}}}}
        self.path.write_text(json.dumps(self.data))
        self.profile = self.path.parent / 'Profile 1'
        (self.profile / 'Network').mkdir(parents=True)
        (self.profile / 'Login Data').write_bytes(b'synthetic encrypted-password database')
        (self.profile / 'Preferences').write_bytes(b'{"sync":{"requested":true}}')
        (self.profile / 'Network/Cookies').write_bytes(b'synthetic cookie database')
        self.session = ProfileSession(self.path, check_browser=False)

    def test_refresh_preserves_edits_and_latest_unknown_fields(self):
        self.session.pin('Profile 1')
        self.data['new_background_field'] = {'keep': 'latest'}
        self.path.write_text(json.dumps(self.data))
        self.assertTrue(self.session.refresh_if_changed())
        self.assertEqual(self.session.starred, ['Profile 1'])
        self.assertFalse(self.session.refresh_if_changed())
        self.session.apply()
        updated = json.loads(self.path.read_bytes())
        self.assertEqual(updated['new_background_field'], {'keep': 'latest'})
        self.assertEqual(updated['profile']['info_cache']['Profile 1']['name'], '01 - Beta')

    def test_refresh_drops_removed_and_keeps_new_profiles(self):
        self.session.pin('Profile 1')
        del self.data['profile']['info_cache']['Profile 1']
        self.data['profile']['info_cache']['Profile 2'] = {'name': 'New profile'}
        self.path.write_text(json.dumps(self.data))
        self.session.refresh_if_changed()
        self.assertEqual(self.session.starred, [])
        self.assertEqual({p['folder'] for p, _ in self.session.preview()}, {'Default', 'Profile 2'})

    def test_full_backup_is_complete_and_source_is_untouched(self):
        settings = self.path.with_name('EdgeProfileOrg.settings.json')
        settings.write_bytes(b'{"starred":["Profile 1"]}')
        session = ProfileSession(self.path, check_browser=False)
        original = self.path.read_bytes()
        original_files = {p.relative_to(self.profile): p.read_bytes() for p in self.profile.rglob('*') if p.is_file()}
        backup = backup_for_removal(session, 'Profile 1')
        self.assertEqual((backup / 'Local State').read_bytes(), original)
        self.assertEqual((backup / settings.name).read_bytes(), settings.read_bytes())
        self.assertEqual(self.path.read_bytes(), original)
        for file, content in original_files.items():
            self.assertEqual((backup / 'Profile 1' / file).read_bytes(), content)
            self.assertEqual((self.profile / file).read_bytes(), content)
        manifest = json.loads((backup / 'READY.json').read_bytes())
        self.assertEqual(manifest['profile_folder'], 'Profile 1')
        self.assertTrue(manifest['settings_existed'])

    def test_copy_failure_has_no_ready_marker_and_keeps_source(self):
        with patch('profile_removal.shutil.copytree', side_effect=OSError('disk full')):
            with self.assertRaisesRegex(OSError, 'disk full'):
                backup_for_removal(self.session, 'Profile 1')
        self.assertTrue((self.profile / 'Login Data').exists())
        self.assertFalse(list(Path(self.temp.name).rglob('READY.json')))

    def test_corrupt_profile_backup_is_refused(self):
        import profile_removal
        actual = profile_removal.durable_copy
        def corrupt(source, destination):
            result = actual(source, destination)
            if Path(destination).name == 'Login Data':
                Path(destination).write_bytes(b'corrupt')
            return result
        with patch('profile_removal.durable_copy', side_effect=corrupt):
            with self.assertRaisesRegex(OSError, 'verification failed'):
                backup_for_removal(self.session, 'Profile 1')
        self.assertFalse(list(Path(self.temp.name).rglob('READY.json')))
        self.assertEqual((self.profile / 'Login Data').read_bytes(), b'synthetic encrypted-password database')

    def test_stale_snapshot_and_unsafe_folder_refused(self):
        self.path.write_text('{}')
        with self.assertRaisesRegex(ValueError, 'Files changed'):
            backup_for_removal(self.session, 'Profile 1')
        for folder in ('../other', 'missing', '/tmp'):
            with self.subTest(folder=folder):
                with self.assertRaises(ValueError):
                    backup_for_removal(self.session, folder)

    def test_symbolic_link_is_refused(self):
        try:
            (self.profile / 'linked').symlink_to(self.path)
        except OSError:
            self.skipTest('Symlinks unavailable')
        with self.assertRaisesRegex(ValueError, 'symbolic link'):
            backup_for_removal(self.session, 'Profile 1')
        self.assertFalse(list(Path(self.temp.name).rglob('READY.json')))
