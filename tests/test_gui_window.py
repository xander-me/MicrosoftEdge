"""Real Tk widget checks; use a desktop or Xvfb. No real browser data."""
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'ProfileOrg'))
try:
    import tkinter as tk
except ImportError:
    tk = None
from EdgeProfileOrg_GUI import create_window


@unittest.skipUnless(tk and (sys.platform != 'linux' or os.environ.get('DISPLAY')), 'Tk/display unavailable')
class WindowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'Local State'
        self.path.write_text(json.dumps({'profile': {'info_cache': {
            'a': {'name': '01 - Alpha'}, 'b': {'name': '02 - Beta'}, 'z': {'name': 'Zebra'}}}}))
        self.root = tk.Tk()
        self.addCleanup(self.root.destroy)
        self.errors = []
        self.root.report_callback_exception = lambda *error: self.errors.append(error)
        self.app = create_window(self.root, self.path, demo_path=self.path)
        self.root.update()
        self.assertFalse(self.errors)

    def drag(self, source, index, target, target_index=0):
        self.root.update()
        bounds = source.bbox(index)
        source.event_generate('<ButtonPress-1>', x=12, y=bounds[1] + bounds[3] // 2)
        self.root.update()
        dest = target.bbox(target_index) if target.size() else None
        y = dest[1] + 1 if dest else 12
        rootx, rooty = target.winfo_rootx() + 12, target.winfo_rooty() + y
        source.event_generate('<B1-Motion>', x=rootx - source.winfo_rootx(), y=rooty - source.winfo_rooty(), rootx=rootx, rooty=rooty)
        source.event_generate('<ButtonRelease-1>', x=rootx - source.winfo_rootx(), y=rooty - source.winfo_rooty(), rootx=rootx, rooty=rooty)
        self.root.update()
        self.assertFalse(self.errors)

    def test_drag_star_reorder_unstar(self):
        starred, others = self.app.boxes
        self.drag(others, 2, starred)
        self.assertEqual(self.app.session.starred, ['z'])
        self.drag(others, 1, starred)
        self.assertEqual(self.app.session.starred, ['b', 'z'])
        self.drag(starred, 1, starred, 0)
        self.assertEqual(self.app.session.starred, ['z', 'b'])
        self.drag(starred, 0, others)
        self.assertEqual(self.app.session.starred, ['b'])
        self.assertEqual(self.app.rows[1], ['a', 'z'])

    def test_apply_backup_summary_and_noop(self):
        self.app.session.pin('z')
        self.app.render()
        self.assertIn('3 names will change', self.app.summary.get())
        with patch('tkinter.messagebox.askyesno', return_value=True), patch('tkinter.messagebox.showinfo'):
            self.app.apply()
        self.assertTrue(Path(self.app.backup_path.get()).exists())
        self.assertEqual(str(self.app.apply_button['state']), 'disabled')
        self.assertIn('Everything is saved', self.app.summary.get())
        self.assertFalse(self.errors)

    def test_controls_fit_minimum_window(self):
        self.root.geometry('780x560')
        self.root.update()
        for widget in (*self.app.boxes, self.app.preview, self.app.apply_button, self.app.backup_entry):
            self.assertTrue(widget.winfo_ismapped())
            self.assertGreater(widget.winfo_height(), 10)
            self.assertLessEqual(widget.winfo_rooty() + widget.winfo_height(), self.root.winfo_rooty() + self.root.winfo_height())
            self.assertLessEqual(widget.winfo_rootx() + widget.winfo_width(), self.root.winfo_rootx() + self.root.winfo_width())
        self.assertFalse(self.errors)

    def test_discard_and_failed_load(self):
        self.app.session.pin('z')
        with patch('tkinter.messagebox.askyesno', return_value=False):
            self.app.load()
            self.app.close()
        self.assertEqual(self.app.session.starred, ['z'])
        self.assertTrue(self.root.winfo_exists())
        self.app.path.set(str(self.path.parent / 'missing'))
        self.assertEqual(str(self.app.apply_button['state']), 'disabled')
        with patch('tkinter.messagebox.askyesno', return_value=True), patch('tkinter.messagebox.showerror'):
            self.app.load()
        self.assertIsNone(self.app.session)
        self.assertEqual(self.app.boxes[0].size(), 0)
        self.assertEqual(len(self.app.preview.get_children()), 0)
        self.assertEqual(str(self.app.apply_button['state']), 'disabled')
        self.assertFalse(self.errors)
