#!/usr/bin/env python3
"""Desktop Edge profile organiser: drag favourites into order and preview names."""
import argparse
import json
import tempfile
import subprocess
import sys
from pathlib import Path
from profile_order import ProfileSession, default_local_state


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group()
    source.add_argument('--local-state', type=Path, help='Use a copied Local State file for testing')
    source.add_argument('--demo', action='store_true', help='Try temporary sample profiles without touching Edge')
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

    class Organizer:
        def __init__(self, root):
            self.root = root
            self.session = None
            self.drag = None
            root.title('Edge Profile Organiser')
            root.geometry('1000x720')
            root.minsize(780, 560)
            frame = ttk.Frame(root, padding=18)
            frame.pack(fill='both', expand=True)
            ttk.Label(frame, text='Your profiles. Your order.', font=('TkDefaultFont', 18, 'bold')).pack(anchor='w')
            ttk.Label(frame, text='Star favourites and drag them into order. Everything else stays A–Z.').pack(anchor='w', pady=(4, 12))
            pathbar = ttk.Frame(frame)
            pathbar.pack(fill='x')
            self.path = tk.StringVar(value=str(args.local_state or default_local_state()))
            ttk.Entry(pathbar, textvariable=self.path).pack(side='left', fill='x', expand=True)
            ttk.Button(pathbar, text='Browse…', command=self.browse).pack(side='left', padx=6)
            ttk.Button(pathbar, text='Load / Reset', command=self.load).pack(side='left')
            self.status = tk.StringVar(value='Load your profiles to start.')
            ttk.Label(frame, textvariable=self.status, wraplength=900).pack(anchor='w', pady=10)
            lists = ttk.Frame(frame)
            lists.pack(fill='both', expand=True)
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
                box.bind('<ButtonPress-1>', self.drag_start)
                box.bind('<B1-Motion>', self.drag_motion)
                box.bind('<ButtonRelease-1>', self.drag_end)
                box.bind('<Double-Button-1>', lambda event, b=box: self.toggle(b))
                self.boxes.append(box)
            buttons = ttk.Frame(frame)
            buttons.pack(fill='x', pady=5)
            ttk.Button(buttons, text='★ Star selected', command=lambda: self.toggle(self.boxes[1])).pack(side='left')
            ttk.Button(buttons, text='Unstar selected', command=lambda: self.toggle(self.boxes[0])).pack(side='left', padx=6)
            ttk.Button(buttons, text='Move up', command=lambda: self.move(-1)).pack(side='left')
            ttk.Button(buttons, text='Move down', command=lambda: self.move(1)).pack(side='left', padx=6)
            ttk.Label(frame, text='Preview — names after applying').pack(anchor='w', pady=(12, 4))
            holder = ttk.Frame(frame)
            holder.pack(fill='both', expand=True)
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
            footer.pack(fill='x', pady=(12, 0))
            ttk.Label(footer, text='Close Edge completely before applying. A backup is created when names change.').pack(side='left')
            self.apply_button = ttk.Button(footer, text='Apply changes…', command=self.apply, state='disabled')
            self.apply_button.pack(side='right')
            root.after(0, self.load)

        def browse(self):
            path = filedialog.askopenfilename(title='Choose Edge Local State (or a copied fixture)')
            if path:
                self.path.set(path)
                self.load()

        def load(self):
            try:
                session = ProfileSession(self.path.get())
            except (OSError, ValueError, TypeError, AttributeError) as error:
                messagebox.showerror('Cannot load profiles', str(error))
                return
            self.session = session
            self.path.set(str(session.path))
            numbers = [p['number'] for p in session.profiles if p['number'] is not None]
            mode = 'DEMO — temporary sample data. ' if session.path == demo_path else ''
            self.status.set(mode + f'{len(session.profiles)} profiles · {len(numbers)} numbered · '
                            f'{len(numbers) - len(set(numbers))} duplicate numbers. '
                            'Drag from Other profiles to Starred to pin; drag back to unstar. Changes stay in preview until applied.')
            self.apply_button.configure(state='normal')
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

        def toggle(self, box):
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
            if not self.session or not self.boxes[0].curselection():
                return
            index = self.boxes[0].curselection()[0]
            folder = self.rows[0][index]
            self.session.pin(folder, index + delta)
            self.render(folder)

        def drag_start(self, event):
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

        def apply(self):
            if Path(self.path.get()) != self.session.path:
                messagebox.showerror('Load profiles first', 'The file path changed. Click Load / Reset before applying.')
                return
            is_demo = self.session.path == demo_path
            prompt = 'Apply these changes to the temporary demo profiles?' if is_demo else 'Have you closed Edge completely?\n\nApply the previewed names and save starred profiles?'
            if not messagebox.askyesno('Apply profile order?', prompt):
                return
            try:
                if sys.platform == 'win32' and not is_demo:
                    processes = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq msedge.exe', '/FO', 'CSV', '/NH'],
                                               capture_output=True, text=True, check=True, creationflags=subprocess.CREATE_NO_WINDOW)
                    if 'msedge.exe' in processes.stdout.lower():
                        raise ValueError('Close Edge completely before applying changes.')
                backup = self.session.apply()
            except (OSError, ValueError, subprocess.SubprocessError) as error:
                messagebox.showerror('Changes could not be completed', str(error))
                return
            messagebox.showinfo('Saved', 'Starred order saved.\n' +
                                (f'Backup: {backup}' if backup else 'Names already matched; Local State unchanged.'))
            self.load()

    root = tk.Tk()
    Organizer(root)
    try:
        root.mainloop()
    finally:
        if demo_directory:
            demo_directory.cleanup()


if __name__ == '__main__':
    main()
