"""Run both CLIs against temporary browser data; never touch real profiles."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class OrderingTests(unittest.TestCase):
    def exercise(self, command, option):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'Local State'
            original = {'unrelated': {'keep': [1, 'æ', True]}, 'profile': {'info_cache': {
                'a': {'name': '01 - Alpha', 'extra': 7},
                'z': {'name': '02 - Zebra'}, 'n': {'name': 'New favourite'},
                'b': {'name': '100 - beta'}}}}
            path.write_text(json.dumps(original), encoding='utf-8')
            before = path.read_bytes()

            def run(answers):
                result = subprocess.run(command + [option, str(path)], input=answers,
                                        text=True, capture_output=True)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                return result.stdout

            # New profile is fourth in detected numeric order. Cancel writes nothing.
            output = run('4,2\nn\n')
            self.assertIn('3/4 profiles', output)
            self.assertEqual(path.read_bytes(), before)
            self.assertEqual(len(list(Path(directory).iterdir())), 1)
            # Reject duplicate and out-of-range choices before accepting favourites.
            run('4,4\n0\n4,2\ny\n')
            updated = json.loads(path.read_text(encoding='utf-8-sig'))
            self.assertEqual(updated['unrelated'], original['unrelated'])
            cache = updated['profile']['info_cache']
            self.assertEqual({f: p['name'] for f, p in cache.items()},
                             {'n': '01 - New favourite', 'z': '02 - Zebra',
                              'a': '03 - Alpha', 'b': '04 - beta'})
            self.assertEqual(cache['a']['extra'], 7)
            backups = list(Path(directory).glob('Local State.backup-*'))
            self.assertEqual(len(backups), 1)
            self.assertEqual(backups[0].read_bytes(), before)
            # Saved favourites persist, and a repeated run does not rewrite Local State.
            applied = path.read_bytes()
            run('\ny\n')
            self.assertEqual(path.read_bytes(), applied)
            self.assertEqual(len(list(Path(directory).glob('Local State.backup-*'))), 1)
            # New non-starred profiles join the alphabetical remainder.
            updated['profile']['info_cache']['new'] = {'name': 'Aaron'}
            path.write_text(json.dumps(updated), encoding='utf-8')
            run('\ny\n')
            cache = json.loads(path.read_text(encoding='utf-8-sig'))['profile']['info_cache']
            self.assertEqual(cache['new']['name'], '03 - Aaron')
            self.assertEqual(cache['n']['name'], '01 - New favourite')
            # Clearing stars restores full alphabetical order.
            run('none\ny\n')
            cache = json.loads(path.read_text(encoding='utf-8-sig'))['profile']['info_cache']
            self.assertEqual(cache['new']['name'], '01 - Aaron')
            # Restore original browser data from the exact backup.
            shutil.copy2(backups[0], path)
            self.assertEqual(path.read_bytes(), before)

    def test_python(self):
        self.exercise([sys.executable, str(ROOT / 'ProfileOrg/EdgeProfileOrg_V1.0.py')], '--local-state')

    @unittest.skipUnless(shutil.which('pwsh'), 'PowerShell unavailable')
    def test_powershell(self):
        self.exercise(['pwsh', '-NoProfile', '-File', str(ROOT / 'ProfileOrg/EdgeProfileOrg_V1.0.ps1')], '-LocalStatePath')


if __name__ == '__main__':
    unittest.main()
