"""Live preview edits and a real pseudo-terminal apply, using synthetic data."""
import json
import os
from pathlib import Path
import select
import subprocess
import sys
import tempfile
import time
import unittest
from test_terminal_menu import terminal, ROOT
from terminal_live import LiveSelection


class LiveTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'Local State'
        self.path.write_text(json.dumps({'profile': {'info_cache': {
            'a': {'name': '01 - Alpha'}, 'b': {'name': '02 - Beta'}}}}))

    def test_selection_follows_edits_without_writes(self):
        before = self.path.read_bytes()
        organizer = terminal.TerminalOrganizer(self.path)
        state = LiveSelection(organizer)
        state.navigate(1)
        state.edit('m')
        self.assertEqual(state.folder, 'b')
        self.assertEqual(state.index, 0)
        self.assertEqual(state.rows[0][1], '01 - Beta')
        state.navigate(1)
        state.edit(' ')
        state.edit('-')
        self.assertEqual(organizer.session.starred, ['a', 'b'])
        state.edit('+')
        self.assertEqual(organizer.session.starred, ['b', 'a'])
        state.edit('u')
        self.assertEqual(organizer.session.starred, ['b'])
        self.assertEqual(self.path.read_bytes(), before)
        self.assertFalse(organizer.session.settings.exists())

    @unittest.skipUnless(os.name == 'posix', 'Requires a POSIX pseudo-terminal')
    def test_live_keyboard_apply_in_pty(self):
        import fcntl
        import pty
        import struct
        import termios
        master, slave = pty.openpty()
        self.addCleanup(os.close, master)
        fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack('HHHH', 24, 100, 0, 0))
        process = subprocess.Popen([sys.executable, '-S', str(ROOT / 'ProfileOrg/EdgeProfileOrg_V1.0.py'),
                                    '--live', '--local-state', str(self.path)],
                                   stdin=slave, stdout=slave, stderr=slave,
                                   env={**os.environ, 'TERM': 'xterm-256color'}, start_new_session=True)
        os.close(slave)
        output = bytearray()

        def until(needle):
            deadline = time.monotonic() + 15
            while needle not in output:
                self.assertLess(time.monotonic(), deadline, output.decode(errors='replace'))
                if select.select([master], [], [], 0.1)[0]:
                    try:
                        chunk = os.read(master, 65536)
                    except OSError:
                        self.fail(output.decode(errors='replace'))
                    self.assertTrue(chunk, output.decode(errors='replace'))
                    output.extend(chunk)
        try:
            until(b'PREVIEW')
            os.write(master, b'jm')
            until(b'pinned first')
            os.write(master, b'a')
            until(b'[y/N]')
            os.write(master, b'y\n')
            until(b'Press Enter to return')
            os.write(master, b'\n')
            until(b'Returned from Apply preview')
            os.write(master, b'q')
            deadline = time.monotonic() + 15
            while process.poll() is None:
                self.assertLess(time.monotonic(), deadline, output.decode(errors='replace'))
                if select.select([master], [], [], 0.1)[0]:
                    try:
                        output.extend(os.read(master, 65536))
                    except OSError:
                        break
            self.assertEqual(process.wait(timeout=5), 0, output.decode(errors='replace'))
            data = json.loads(self.path.read_bytes())
            self.assertEqual(data['profile']['info_cache']['b']['name'], '01 - Beta')
        finally:
            if process.poll() is None:
                process.kill()
                process.wait(timeout=5)
