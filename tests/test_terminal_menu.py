"""Exercise the default terminal flow without Tk or third-party packages."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'ProfileOrg'))
spec = importlib.util.spec_from_file_location('terminal_organizer', ROOT / 'ProfileOrg/EdgeProfileOrg_V1.0.py')
terminal = importlib.util.module_from_spec(spec)
spec.loader.exec_module(terminal)


class TerminalMenuTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'User Data/Local State'
        self.path.parent.mkdir()
        self.data = {'os_crypt': {'encrypted_key': 'SYNTHETIC'}, 'profile': {'info_cache': {
            'a': {'name': '01 - Alpha'}, 'b': {'name': '02 - Beta'}, 'c': {'name': 'New profile'}}}}
        self.path.write_text(json.dumps(self.data), encoding='utf-8')
        for folder in ('a', 'b', 'c'):
            (self.path.parent / folder).mkdir()
            (self.path.parent / folder / 'Login Data').write_bytes(b'synthetic password database')

    def run_cli(self, answers, *options):
        result = subprocess.run([sys.executable, '-S', str(ROOT / 'ProfileOrg/EdgeProfileOrg_V1.0.py'), *options],
                                input=answers, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result

    def test_move_to_top_apply_and_unstar(self):
        result = self.run_cli('m\n3\n1\na\ny\nq\n', '--local-state', str(self.path))
        self.assertIn('0.5.2-terminal', result.stdout)
        data = json.loads(self.path.read_bytes())
        self.assertEqual(data['profile']['info_cache']['c']['name'], '01 - New profile')
        self.assertEqual(data['os_crypt'], self.data['os_crypt'])
        self.assertEqual(json.loads(self.path.with_name('EdgeProfileOrg.settings.json').read_bytes())['starred'], ['c'])
        self.run_cli('u\n1\na\ny\nq\n', '--local-state', str(self.path))
        data = json.loads(self.path.read_bytes())
        self.assertEqual(data['profile']['info_cache']['a']['name'], '01 - Alpha')
        for folder in ('a', 'b', 'c'):
            self.assertEqual((self.path.parent / folder / 'Login Data').read_bytes(), b'synthetic password database')

    def test_cancel_and_discard_write_nothing(self):
        before = self.path.read_bytes()
        self.run_cli('s\n3,1\na\nn\nq\ny\n', '--local-state', str(self.path))
        self.assertEqual(self.path.read_bytes(), before)
        self.assertFalse(self.path.with_name('EdgeProfileOrg.settings.json').exists())
        self.assertFalse(list(self.path.parent.glob('Local State.backup-*')))

    def test_demo_backup_and_removal_protection(self):
        result = self.run_cli('d\nb\n\ny\nq\n', '--demo')
        self.assertIn('Removal is disabled', result.stdout)
        self.assertIn('Full backup verified (ALL profiles):', result.stdout)
        self.assertNotIn('Profile list number', result.stdout)

    def test_full_backup_menu_copies_all_profiles_without_selection(self):
        before = {p.relative_to(self.path.parent): p.read_bytes() for p in self.path.parent.rglob('*') if p.is_file()}
        result = self.run_cli('b\n\ny\nq\n', '--local-state', str(self.path))
        self.assertNotIn('Profile list number', result.stdout)
        ready = list(Path(self.temp.name).rglob('READY.json'))
        self.assertEqual(len(ready), 1)
        self.assertEqual(json.loads(ready[0].read_bytes())['backup_type'], 'all_profiles')
        for name, content in before.items():
            self.assertEqual((ready[0].parent / 'User Data' / name).read_bytes(), content)
            self.assertEqual((self.path.parent / name).read_bytes(), content)

    def test_full_backup_uses_chosen_folder_with_spaces(self):
        target = Path(self.temp.name) / 'External drive' / 'Backups'
        result = self.run_cli(f'b\n"{target}"\ny\nq\n', '--local-state', str(self.path))
        self.assertIn(str(target), result.stdout)
        ready = list(target.rglob('READY.json'))
        self.assertEqual(len(ready), 1)
        self.assertTrue((ready[0].parent / 'User Data/a/Login Data').exists())
        self.assertFalse((Path(self.temp.name) / 'Edge Profile Organiser Backups').exists())

    def test_cancel_full_backup_creates_no_snapshot(self):
        result = self.run_cli('b\n\nn\nq\n', '--local-state', str(self.path))
        self.assertNotIn('Profile list number', result.stdout)
        self.assertFalse((Path(self.temp.name) / 'Edge Profile Organiser Backups').exists())

    def test_copied_profile_cannot_launch_native_removal(self):
        result = self.run_cli('d\nq\n', '--local-state', str(self.path))
        self.assertIn('Removal is disabled', result.stdout)

    def test_stale_apply_keeps_order_and_requires_new_confirmation(self):
        organizer = terminal.TerminalOrganizer(self.path)
        organizer.session.check_browser = False
        organizer.session.pin('c')
        data = json.loads(self.path.read_bytes())
        data['background_change'] = 'latest'
        self.path.write_text(json.dumps(data))
        before = self.path.read_bytes()
        with patch('builtins.input') as confirm, patch('builtins.print'):
            organizer.apply()
        confirm.assert_not_called()
        self.assertEqual(self.path.read_bytes(), before)
        self.assertEqual(organizer.session.starred, ['c'])
        with patch('builtins.input', return_value='y'), patch('builtins.print'):
            organizer.apply()
        self.assertEqual(json.loads(self.path.read_bytes())['background_change'], 'latest')
        self.assertEqual(json.loads(self.path.read_bytes())['profile']['info_cache']['c']['name'], '01 - New profile')

    def test_native_removal_requires_verified_backup_and_confirmation(self):
        organizer = terminal.TerminalOrganizer(self.path)
        organizer.session.check_browser = False
        with patch.object(terminal, 'default_local_state', return_value=self.path), patch.object(terminal, 'open_native_removal') as native, patch('builtins.input', side_effect=['2', 'y', 'y']), patch('builtins.print'):
            organizer.backup(remove=True)
        self.assertTrue((organizer.last_backup / 'READY.json').exists())
        native.assert_called_once_with('b')
        self.assertTrue((self.path.parent / 'b/Login Data').exists())

    def test_failed_backup_never_launches_removal(self):
        organizer = terminal.TerminalOrganizer(self.path)
        organizer.session.check_browser = False
        with patch.object(terminal, 'default_local_state', return_value=self.path), patch.object(terminal, 'backup_for_removal', side_effect=OSError('disk full')), patch.object(terminal, 'open_native_removal') as native, patch('builtins.input', side_effect=['2', 'y']), patch('builtins.print'):
            with self.assertRaisesRegex(OSError, 'disk full'):
                organizer.backup(remove=True)
        native.assert_not_called()
