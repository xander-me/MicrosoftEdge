#!/usr/bin/env python3
# Author: Using-IT
"""Desktop Edge profile organiser: drag favourites into order and preview names."""
import argparse
import json
import tempfile
import queue
import threading
from pathlib import Path
from profile_order import ProfileSession, default_local_state
from profile_removal import backup_for_removal, open_native_removal


def create_window(root, initial_path, demo_path=None):
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk

    class Organizer:
        def __init__(self, root):
            self.root = root
            self.session = None
            self.drag = None
            self.busy = False
            root.title('Edge Profile Organiser')
            root.geometry('1000x720')
            root.minsize(780, 560)
            frame = ttk.Frame(root, padding=18)
            frame.pack(fill='both', expand=True)
            frame.columnconfigure(0, weight=1)
            frame.rowconfigure(4, weight=1, minsize=80)
            frame.rowconfigure(7, weight=1, minsize=80)
            ttk.Label(frame, text='Your profiles. Your order.', font=('TkDefaultFont', 18, 'bold')).grid(row=0, column=0, sticky='w')
            ttk.Label(frame, text='Star favourites and drag them into order. Everything else stays A–Z.').grid(row=1, column=0, sticky='w', pady=(4, 12))
            pathbar = ttk.Frame(frame)
            pathbar.grid(row=2, column=0, sticky='ew')
            self.path = tk.StringVar(value=str(initial_path))
            self.path_entry = ttk.Entry(pathbar, textvariable=self.path)
            self.path_entry.pack(side='left', fill='x', expand=True)
            ttk.Button(pathbar, text='Browse…', command=self.browse).pack(side='left', padx=6)
            ttk.Button(pathbar, text='Refresh', command=self.refresh).pack(side='left', padx=(0, 6))
            ttk.Button(pathbar, text='Load / Reset', command=self.load).pack(side='left')
            self.status = tk.StringVar(value='Load your profiles to start.')
            ttk.Label(frame, textvariable=self.status, wraplength=700).grid(row=3, column=0, sticky='w', pady=10)
            lists = ttk.Frame(frame)
            lists.grid(row=4, column=0, sticky='nsew')
            lists.columnconfigure(0, weight=1)
            lists.columnconfigure(1, weight=1)
            lists.rowconfigure(1, weight=1)
            ttk.Label(lists, text='★ Starred — drag to reorder').grid(row=0, column=0, sticky='w')
            ttk.Label(lists, text='Other profiles — A–Z').grid(row=0, column=1, sticky='w', padx=(12, 0))
            self.boxes = []
            for column in range(2):
                holder = ttk.Frame(lists)
                holder.grid(row=1, column=column, sticky='nsew', padx=(0 if column == 0 else 12, 0), pady=5)
                box = tk.Listbox(holder, exportselection=False, activestyle='dotbox', height=7)
                scroll = ttk.Scrollbar(holder, orient='vertical', command=box.yview)
                box.configure(yscrollcommand=scroll.set)
                scroll.pack(side='right', fill='y')
                box.pack(fill='both', expand=True)
                box.bind('<<ListboxSelect>>', self.selection_changed)
                box.bind('<ButtonPress-1>', self.drag_start)
                box.bind('<B1-Motion>', self.drag_motion)
                box.bind('<ButtonRelease-1>', self.drag_end)
                box.bind('<Double-Button-1>', lambda event, b=box: self.toggle(b))
                self.boxes.append(box)
            buttons = ttk.Frame(frame)
            buttons.grid(row=5, column=0, sticky='ew', pady=5)
            ttk.Button(buttons, text='★ Star selected', command=lambda: self.toggle(self.boxes[1])).pack(side='left')
            ttk.Button(buttons, text='Unstar selected', command=lambda: self.toggle(self.boxes[0])).pack(side='left', padx=6)
            ttk.Button(buttons, text='Move up', command=lambda: self.move(-1)).pack(side='left')
            ttk.Button(buttons, text='Move down', command=lambda: self.move(1)).pack(side='left', padx=6)
            self.remove_button = ttk.Button(buttons, text='Back up & remove…', command=self.remove_selected)
            self.remove_button.pack(side='right')
            ttk.Label(frame, text='Preview — names after applying').grid(row=6, column=0, sticky='w', pady=(8, 4))
            holder = ttk.Frame(frame)
            holder.grid(row=7, column=0, sticky='nsew')
            self.preview = ttk.Treeview(holder, columns=('current', 'new'), show='headings', height=7)
            self.preview.heading('current', text='Current name')
            self.preview.heading('new', text='New name')
            self.preview.column('current', width=400)
            self.preview.column('new', width=400)
            scroll = ttk.Scrollbar(holder, orient='vertical', command=self.preview.yview)
            self.preview.configure(yscrollcommand=scroll.set)
            scroll.pack(side='right', fill='y')
            self.preview.pack(fill='both', expand=True)
            footer = ttk.Frame(frame)
            footer.grid(row=8, column=0, sticky='ew', pady=(8, 0))
            ttk.Label(footer, text='Display names only; profile folders stay in place. Verified backup required before saving.', wraplength=560).pack(side='left')
            self.apply_button = ttk.Button(footer, text='Apply changes…', command=self.apply, state='disabled')
            self.apply_button.pack(side='right')
            self.summary = tk.StringVar()
            ttk.Label(frame, textvariable=self.summary).grid(row=9, column=0, sticky='w')
            self.backup_path = tk.StringVar()
            ttk.Label(frame, text='Last verified backup (copy this path for recovery):').grid(row=10, column=0, sticky='w', pady=(6, 0))
            self.backup_entry = ttk.Entry(frame, textvariable=self.backup_path, state='readonly')
            self.backup_entry.grid(row=11, column=0, sticky='ew')
            self.path.trace_add('write', lambda *_: self.update_apply_state())
            root.protocol('WM_DELETE_WINDOW', self.close)
            root.after(0, self.load)

        def confirm_discard(self):
            return not (self.session and self.session.has_unsaved_edits) or messagebox.askyesno('Discard preview edits?', 'You have changed your starred order without saving. Discard these edits?')

        def close(self):
            if self.busy:
                messagebox.showinfo('Backup in progress', 'Please wait for backup verification to finish before closing.')
                return
            if self.confirm_discard():
                self.root.destroy()

        def update_apply_state(self):
            ready = not self.busy and self.session and Path(self.path.get()) == self.session.path and self.session.needs_save
            self.apply_button.configure(state='normal' if ready else 'disabled')
            self.remove_button.configure(state='normal' if not self.busy and self.session else 'disabled')

        def browse(self):
            if self.busy:
                return
            if not self.confirm_discard():
                return
            path = filedialog.askopenfilename(title='Choose Edge Local State (or a copied fixture)')
            if path:
                self.path.set(path)
                self.load(confirm=False)

        def load(self, confirm=True):
            if self.busy:
                return
            if confirm and not self.confirm_discard():
                return
            try:
                session = ProfileSession(self.path.get(), check_browser=Path(self.path.get()) != demo_path)
            except (OSError, ValueError, TypeError, AttributeError) as error:
                self.session = None
                self.drag = None
                for box in self.boxes:
                    box.delete(0, 'end')
                self.preview.delete(*self.preview.get_children())
                self.apply_button.configure(state='disabled')
                self.summary.set('')
                self.status.set('No profiles loaded. Choose a valid Local State file and click Load / Reset.')
                messagebox.showerror('Cannot load profiles', str(error))
                return
            self.session = session
            self.path.set(str(session.path))
            numbers = [p['number'] for p in session.profiles if p['number'] is not None]
            mode = 'DEMO — temporary sample data. ' if session.path == demo_path else ''
            self.status.set(mode + f'{len(session.profiles)} profiles · {len(numbers)} numbered · '
                            f'{len(numbers) - len(set(numbers))} duplicate numbers. '
                            'Drag from Other profiles to Starred to pin; drag back to unstar. Changes stay in preview until applied.')
            self.render()

        def render(self, selected=None):
            ordered = self.session.preview()
            self.rows = [[p['folder'] for p, _ in ordered if p['folder'] in self.session.starred],
                         [p['folder'] for p, _ in ordered if p['folder'] not in self.session.starred]]
            names = {p['folder']: p['clean'] for p in self.session.profiles}
            for box, folders in zip(self.boxes, self.rows):
                box.delete(0, 'end')
                for folder in folders:
                    box.insert('end', f'{names[folder]} [{folder}]')
                if selected in folders:
                    index = folders.index(selected)
                    box.selection_set(index)
                    box.see(index)
            self.preview.delete(*self.preview.get_children())
            for profile, name in ordered:
                self.preview.insert('', 'end', values=(profile['name'], name))
            self.summary.set(f'{self.session.rename_count} names will change · {len(self.session.starred)} starred profiles' if self.session.needs_save else 'Everything is saved. No changes to apply.')
            self.update_apply_state()

        def selection_changed(self, event):
            if event.widget.curselection():
                for box in self.boxes:
                    if box is not event.widget:
                        box.selection_clear(0, 'end')

        def toggle(self, box):
            if self.busy:
                return
            if not self.session or not box.curselection():
                return
            column = self.boxes.index(box)
            folder = self.rows[column][box.curselection()[0]]
            if column == 0:
                self.session.unpin(folder)
            else:
                self.session.pin(folder)
            self.render(folder)

        def move(self, delta):
            if self.busy:
                return
            if not self.session or not self.boxes[0].curselection():
                return
            index = self.boxes[0].curselection()[0]
            folder = self.rows[0][index]
            self.session.pin(folder, index + delta)
            self.render(folder)

        def drag_start(self, event):
            if self.busy:
                return
            self.drag = None
            if not self.session or not event.widget.size():
                return
            index = event.widget.nearest(event.y)
            bounds = event.widget.bbox(index)
            if bounds and bounds[1] <= event.y <= bounds[1] + bounds[3]:
                self.drag = (self.rows[self.boxes.index(event.widget)][index], event.x_root, event.y_root)

        def drag_motion(self, event):
            target = self.root.winfo_containing(event.x_root, event.y_root)
            if target in self.boxes:
                y = event.y_root - target.winfo_rooty()
                if y < 20:
                    target.yview_scroll(-1, 'units')
                elif y > target.winfo_height() - 20:
                    target.yview_scroll(1, 'units')

        def drag_end(self, event):
            if self.busy:
                return
            drag, self.drag = self.drag, None
            if not drag or abs(event.x_root - drag[1]) + abs(event.y_root - drag[2]) < 5:
                return
            target = self.root.winfo_containing(event.x_root, event.y_root)
            if target not in self.boxes:
                return
            folder = drag[0]
            if target is self.boxes[1]:
                self.session.unpin(folder)
            else:
                y = event.y_root - target.winfo_rooty()
                index = target.nearest(y) if target.size() else 0
                bounds = target.bbox(index) if target.size() else None
                if bounds and y > bounds[1] + bounds[3] / 2:
                    index += 1
                old = self.session.starred.index(folder) if folder in self.session.starred else None
                if old is not None and old < index:
                    index -= 1
                self.session.pin(folder, index)
            self.render(folder)

        def refresh(self):
            if self.busy or not self.session:
                return False
            if Path(self.path.get()) != self.session.path:
                messagebox.showerror('Load profiles first', 'The path changed. Click Load / Reset to switch files.')
                return False
            try:
                changed = self.session.refresh_if_changed()
            except (OSError, ValueError) as error:
                messagebox.showerror('Cannot refresh profiles', str(error))
                return False
            self.render()
            self.status.set('Refreshed from disk. Your proposed favourites were kept where those profiles still exist. Review the preview before applying.')
            return changed

        def remove_selected(self):
            if self.busy or not self.session:
                return
            if Path(self.path.get()) != self.session.path:
                messagebox.showerror('Load profiles first', 'Load the selected file before removal.')
                return
            # Both listboxes can retain selection; require a single unambiguous choice.
            selected = [self.rows[i][box.curselection()[0]] for i, box in enumerate(self.boxes) if box.curselection()]
            if len(selected) != 1:
                messagebox.showinfo('Select one profile', 'Select exactly one profile to back up and remove.')
                return
            folder = selected[0]
            profile = next(p for p in self.session.profiles if p['folder'] == folder)
            if self.session.path == demo_path:
                messagebox.showinfo('Demo only', 'Profile removal is disabled in the demo. Your real Edge profiles are never accessed.')
                return
            if self.session.path.resolve() != default_local_state().resolve():
                messagebox.showinfo('Copied profile data', 'Native removal is available only for the standard Edge data file. Copied fixtures cannot open removal for your real profiles.')
                return
            try:
                if self.session.refresh_if_changed():
                    self.render()
                    messagebox.showinfo('Profiles refreshed', 'Local State or favourites changed since loading. Your proposed order is retained. Review the list and select the profile again before removal.')
                    return
            except (OSError, ValueError) as error:
                messagebox.showerror('Cannot prepare removal', str(error))
                return
            if not messagebox.askyesno('Back up and open Edge removal?',
                    f"Profile: {profile['name']}\nFolder: {folder}\n\nClose Edge completely. A full verified local profile backup will be made first; this can take time and disk space. Edge will then open its own removal screen, where you confirm deletion. No deletion happens automatically. Continue?"):
                return
            self.busy = True
            self.path_entry.configure(state='readonly')
            self.update_apply_state()
            self.status.set(f'Backing up and verifying {profile["name"]}… Please keep Edge closed. No profile has been deleted.')
            results = queue.Queue()
            session = self.session
            def work():
                try:
                    results.put((backup_for_removal(session, folder), None))
                except Exception as error:
                    results.put((None, error))
            def finish():
                try:
                    backup, error = results.get_nowait()
                except queue.Empty:
                    self.root.after(100, finish)
                    return
                self.busy = False
                self.path_entry.configure(state='normal')
                self.update_apply_state()
                if error:
                    self.status.set('Backup did not complete. No removal screen was opened.')
                    messagebox.showerror('Removal stopped', str(error))
                    return
                self.backup_path.set(str(backup))
                self.status.set('Full profile backup verified. Removal requires confirmation inside Edge; refresh this list after closing Edge again.')
                if messagebox.askyesno('Backup verified', f'Full local backup: {backup}\n\nOpen the selected profile in Edge now? Choose its Remove option and confirm there. Managed policies may prevent removal.'):
                    try:
                        open_native_removal(folder)
                    except Exception as error:
                        messagebox.showerror('Could not open Edge', f'Your backup is complete: {backup}\n{error}')
            threading.Thread(target=work, daemon=True).start()
            self.root.after(100, finish)

        def apply(self):
            if self.busy or not self.session:
                return
            if Path(self.path.get()) != self.session.path:
                messagebox.showerror('Load profiles first', 'The file path changed. Click Load / Reset before applying.')
                return
            try:
                if self.session.refresh_if_changed():
                    self.render()
                    self.status.set('Updated from disk; proposed favourites retained. Review the fresh preview, then Apply again.')
                    messagebox.showinfo('Profiles refreshed', 'Edge or another process saved Local State after it was loaded. The latest data is now loaded and your proposed favourites are retained. Review the preview and click Apply again. No files were written.')
                    return
            except (OSError, ValueError) as error:
                messagebox.showerror('Cannot prepare changes', str(error))
                return
            is_demo = self.session.path == demo_path
            prompt = 'Apply these changes to the temporary demo profiles?' if is_demo else 'Have you closed Edge completely?\n\nOnly display names change; profile folders stay in place. Verified backups must succeed before saving names and favourites.\n\nApply the preview?'
            if not messagebox.askyesno('Apply profile order?', prompt):
                return
            try:
                backup = self.session.apply()
            except (OSError, ValueError) as error:
                messagebox.showerror('Changes could not be completed', str(error))
                return
            if backup:
                self.backup_path.set(str(backup))
            messagebox.showinfo('Saved', 'Starred order saved.\n' +
                                (f'Backup created and verified: {backup}' if backup else 'Names already matched; Local State unchanged.'))
            self.load(confirm=False)

    return Organizer(root)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group()
    source.add_argument('--local-state', type=Path, help='Use a copied Local State file for testing')
    source.add_argument('--demo', action='store_true', help='Try temporary sample profiles without touching Edge')
    parser.add_argument('--smoke-test', action='store_true', help=argparse.SUPPRESS)
    args = parser.parse_args()
    try:
        import tkinter as tk
        from tkinter import filedialog, messagebox, ttk
    except ImportError:
        parser.exit(1, 'This GUI needs Python with Tk support. See the README installation instructions.\n')

    demo_directory = tempfile.TemporaryDirectory(prefix='edge-profile-demo-') if args.demo else None
    demo_path = None
    if demo_directory:
        demo_path = Path(demo_directory.name) / 'Local State'
        demo_path.write_text(json.dumps({'profile': {'info_cache': {
            'Default': {'name': '01 - Personal'},
            'Profile 1': {'name': '02 - Work'},
            'Profile 2': {'name': '03 - Customer A'},
            'Profile 3': {'name': 'New customer'},
        }}}), encoding='utf-8')
        args.local_state = demo_path

    try:
        root = tk.Tk()
    except tk.TclError as error:
        parser.exit(1, f'Cannot open a desktop window: {error}\nRun from a desktop session with Python/Tk installed.\n')
    if args.smoke_test:
        # Verify the packaged Tcl/Tk runtime and widgets without reading browser data.
        ttk.Label(root, text='Runtime check').pack()
        root.update()
        root.destroy()
        if demo_directory:
            demo_directory.cleanup()
        return
    create_window(root, args.local_state or default_local_state(), demo_path)
    try:
        root.mainloop()
    finally:
        if demo_directory:
            demo_directory.cleanup()


if __name__ == '__main__':
    main()
