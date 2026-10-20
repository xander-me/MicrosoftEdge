"""Check source launcher argument forwarding without installing dependencies."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class MacLauncherTests(unittest.TestCase):
    def test_compatible_runtime_preserves_arguments_and_avoids_setup(self):
        with tempfile.TemporaryDirectory(prefix='mac launcher ') as directory:
            folder = Path(directory)
            uname = folder / 'uname'
            uname.write_text('#!/bin/bash\necho Darwin\n')
            uname.chmod(0o755)
            runtime = folder / 'test python'
            runtime.write_text('#!/bin/bash\nif [[ "$1" == -c ]]; then exit 0; fi\nprintf "%s\\n" "$@"\n')
            runtime.chmod(0o755)
            env = dict(os.environ, PATH=str(folder) + ':' + os.environ['PATH'], EDGE_ORGANIZER_PYTHON=str(runtime))
            result = subprocess.run(['bash', str(ROOT / 'scripts/launch-mac.sh'), '--local-state', '/copied profiles/Local State'],
                                    env=env, text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.splitlines(), [str(ROOT / 'ProfileOrg/EdgeProfileOrg_GUI.py'), '--local-state', '/copied profiles/Local State'])
