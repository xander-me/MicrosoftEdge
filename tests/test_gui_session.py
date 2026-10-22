"""Exercise the GUI's preview/save model without a desktop or real Edge data."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'ProfileOrg'))
from profile_order import ProfileSession


class GuiSessionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'Local State'
        self.data = {'unrelated': {'preserve': 'æ'}, 'profile': {'info_cache': {
            'a': {'name': '01 - Alpha', 'extra': 42},
            'b': {'name': '02 - Beta'}, 'z': {'name': 'Zebra'}}}}
        self.path.write_text(json.dumps(self.data), encoding='utf-8')
        self.original = self.path.read_bytes()

    def test_drag_preview_cancel_and_save(self):
        session = ProfileSession(self.path)
        session.pin('z')
        session.pin('b', 0)
        self.assertEqual([p['folder'] for p, _ in session.preview()], ['b', 'z', 'a'])
        session.pin('z', 0)
        self.assertEqual([n for _, n in session.preview()], ['01 - Zebra', '02 - Beta', '03 - Alpha'])
        self.assertEqual(self.path.read_bytes(), self.original)
        self.assertFalse(session.settings.exists())
        backup = session.apply()
        self.assertEqual(backup.read_bytes(), self.original)
        actual = json.loads(self.path.read_bytes())
        self.assertEqual(actual['unrelated'], self.data['unrelated'])
        self.assertEqual(actual['profile']['info_cache']['a']['extra'], 42)
        reloaded = ProfileSession(self.path)
        self.assertEqual(reloaded.starred, ['z', 'b'])
        before = self.path.read_bytes()
        self.assertIsNone(reloaded.apply())
        self.assertEqual(self.path.read_bytes(), before)

    def test_unstar_and_removed_profiles(self):
        session = ProfileSession(self.path)
        session.pin('z')
        session.pin('a')
        session.unpin('z')
        self.assertEqual([p['folder'] for p, _ in session.preview()], ['a', 'b', 'z'])
        session.apply()
        data = json.loads(self.path.read_bytes())
        del data['profile']['info_cache']['a']
        self.path.write_text(json.dumps(data), encoding='utf-8')
        self.assertEqual(ProfileSession(self.path).starred, [])

    def test_changed_browser_data_refused(self):
        session = ProfileSession(self.path)
        session.pin('z')
        self.path.write_text('{}', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'Local State changed'):
            session.apply()
        self.assertEqual(self.path.read_text(), '{}')
        self.assertEqual(len(list(self.path.parent.iterdir())), 1)

    def test_concurrent_settings_change_refused(self):
        session = ProfileSession(self.path)
        session.settings.write_text('{"starred":["b"]}', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'favourites changed'):
            session.apply()
        self.assertEqual(self.path.read_bytes(), self.original)

    def test_invalid_settings_refused(self):
        for stars in ['z', ['z', 'z'], [None]]:
            with self.subTest(stars=stars):
                self.path.with_name('EdgeProfileOrg.settings.json').write_text(json.dumps({'starred': stars}))
                with self.assertRaisesRegex(ValueError, 'Invalid starred'):
                    ProfileSession(self.path)

    def test_running_browser_prevents_backup_and_writes(self):
        session = ProfileSession(self.path)
        session.pin('z')
        with patch('profile_order.require_edge_closed', side_effect=ValueError('Close Edge completely')):
            with self.assertRaisesRegex(ValueError, 'Close Edge completely'):
                session.apply()
        self.assertEqual(self.path.read_bytes(), self.original)
        self.assertEqual(len(list(self.path.parent.iterdir())), 1)

    def test_failed_backup_prevents_all_writes(self):
        session = ProfileSession(self.path)
        session.pin('z')
        with patch('profile_order.verified_backup', side_effect=OSError('disk full')):
            with self.assertRaisesRegex(OSError, 'disk full'):
                session.apply()
        self.assertEqual(self.path.read_bytes(), self.original)
        self.assertFalse(session.settings.exists())

    def test_failed_settings_backup_prevents_all_writes(self):
        settings = self.path.with_name('EdgeProfileOrg.settings.json')
        settings.write_bytes(b'{"starred": []}')
        session = ProfileSession(self.path)
        session.pin('z')
        from profile_order import verified_backup
        def backup(path, expected, token):
            if path == settings:
                raise OSError('settings backup denied')
            return verified_backup(path, expected, token)
        with patch('profile_order.verified_backup', side_effect=backup):
            with self.assertRaisesRegex(OSError, 'settings backup denied'):
                session.apply()
        self.assertEqual(self.path.read_bytes(), self.original)
        self.assertEqual(settings.read_bytes(), b'{"starred": []}')

    def test_corrupt_backup_prevents_all_writes(self):
        session = ProfileSession(self.path)
        session.pin('z')
        actual_read = Path.read_bytes
        def read(path):
            if '.backup-before-profile-prefix-' in path.name:
                return b'corrupt backup'
            return actual_read(path)
        with patch.object(Path, 'read_bytes', read):
            with self.assertRaisesRegex(OSError, 'Backup verification failed'):
                session.apply()
        self.assertEqual(self.path.read_bytes(), self.original)
        self.assertFalse(session.settings.exists())

    def test_settings_only_change_is_backed_up_before_write(self):
        # Alpha is already first: pinning it only changes favourites.
        session = ProfileSession(self.path)
        session.apply()
        before = self.path.read_bytes()
        settings_before = session.settings.read_bytes()
        session = ProfileSession(self.path)
        session.pin('a')
        backup = session.apply()
        self.assertEqual(backup.read_bytes(), before)
        settings_backup = session.settings.with_name(session.settings.name + '.backup-before-profile-prefix-' + backup.name.split('profile-prefix-')[1])
        self.assertEqual(settings_backup.read_bytes(), settings_before)
        self.assertEqual(self.path.read_bytes(), before)

    def test_settings_write_failure_reports_recovery(self):
        session = ProfileSession(self.path)
        session.pin('z')
        from profile_order import atomic_json
        def write(path, data):
            if path == session.settings:
                raise OSError('permission denied')
            atomic_json(path, data)
        with patch('profile_order.atomic_json', side_effect=write):
            with self.assertRaisesRegex(OSError, 'Names may already have been applied.*Backup:'):
                session.apply()
        self.assertEqual(session.backup.read_bytes(), self.original)


if __name__ == '__main__':
    unittest.main()
