# Author: Using-IT
"""Live keyboard preview in a native terminal, using Python's standard curses module."""
import subprocess


class LiveSelection:
    def __init__(self, organizer):
        self.organizer = organizer
        self.folder = organizer.session.preview()[0][0]['folder']
        self.top = 0
        self.status = 'Preview only. Space stars a profile; M pins it first. A saves after confirmation.'

    @property
    def rows(self):
        return self.organizer.session.preview()

    @property
    def index(self):
        folders = [profile['folder'] for profile, _ in self.rows]
        if self.folder not in folders:
            self.folder = folders[0]
        return folders.index(self.folder)

    def navigate(self, offset):
        rows = self.rows
        index = max(0, min(self.index + offset, len(rows) - 1))
        self.folder = rows[index][0]['folder']

    def edit(self, key):
        session = self.organizer.session
        profile = self.rows[self.index][0]
        folder = profile['folder']
        if key in (' ', 's'):
            if folder in session.starred:
                session.unpin(folder)
                self.status = f'Unstarred {profile["clean"]}; it returns to A-Z. Preview only.'
            else:
                session.pin(folder)
                self.status = f'Starred {profile["clean"]}. Preview updated; not saved.'
        elif key == 'm':
            session.pin(folder, 0)
            self.status = f'{profile["clean"]} pinned first. Preview updated; not saved.'
        elif key == 'u':
            session.unpin(folder)
            self.status = f'{profile["clean"]} returned to A-Z. Preview only.'
        elif key in ('+', '=', '-', '_'):
            if folder not in session.starred:
                self.status = 'Star this profile first (Space), or press M to pin it at the top.'
                return
            position = session.starred.index(folder)
            delta = 1 if key in ('+', '=') else -1
            session.pin(folder, position + delta)
            self.status = f'{profile["clean"]} moved within starred profiles. Preview updated; not saved.'


def run_live(organizer, version):
    import curses

    def view(screen):
        state = LiveSelection(organizer)
        screen.keypad(True)
        try:
            curses.curs_set(0)
        except curses.error:
            pass
        if hasattr(curses, 'set_escdelay'):
            curses.set_escdelay(30)

        def write(row, text, style=0):
            height, width = screen.getmaxyx()
            if 0 <= row < height:
                safe = ''.join(char if char.isprintable() else ' ' for char in str(text))
                try:
                    screen.addnstr(row, 0, safe, max(0, width - 1), style)
                except curses.error:
                    pass

        def draw():
            screen.erase()
            height, width = screen.getmaxyx()
            write(0, f'Edge Profile Organiser {version}' + (' [DEMO]' if organizer.demo else ''), curses.A_BOLD)
            if height < 14 or width < 56:
                write(2, 'Enlarge Terminal to at least 56 columns x 14 rows.')
                write(4, 'Q quits. Your preview is retained during resize.')
                screen.refresh()
                return False
            rows = state.rows
            index = state.index
            visible = height - 10
            state.top = min(state.top, max(0, len(rows) - visible))
            if index < state.top:
                state.top = index
            if index >= state.top + visible:
                state.top = index - visible + 1
            session = organizer.session
            write(1, f'{len(rows)} profiles | {len(session.starred)} starred | {session.rename_count} pending names | PREVIEW, not saved')
            name_width = max(12, width - 27)
            write(3, f"    #  *  {'Profile':<{name_width}} {'Now':>4}   {'Next':>4}", curses.A_BOLD)
            ids = {profile['folder']: i for i, profile in enumerate(session.profiles, 1)}
            for offset, (profile, name) in enumerate(rows[state.top:state.top + visible]):
                actual_index = state.top + offset
                star = '*' if profile['folder'] in session.starred else ' '
                now = f"{profile['number']:02d}" if profile['number'] is not None else '-'
                next_label = f'{actual_index + 1:02d}'
                change = '->' if name != profile['name'] else ' ='
                clean = profile['clean']
                if len(clean) > name_width:
                    clean = clean[:name_width - 1] + '…'
                cursor = '>' if actual_index == index else ' '
                line = f'{cursor} {ids[profile["folder"]]:>3}  {star}  {clean:<{name_width}} {now:>4} {change} {next_label:>4}'
                write(4 + offset, line, curses.A_REVERSE if actual_index == index else 0)
            selected = rows[index][0]
            detail = f"[{selected['folder']}] {selected['name']}" if organizer.details else 'Rows follow the proposed order. * starred; -> change; = unchanged.'
            write(height - 6, f'{index + 1}/{len(rows)} selected | {detail}')
            write(height - 5, state.status, curses.A_BOLD)
            write(height - 4, 'Up/Down select | Space/S star | M pin first | - up / + down')
            write(height - 3, 'A Apply | B Back up profiles | D Back up & remove selected')
            write(height - 2, 'R Refresh | V Details | PgUp/PgDn/Home/End navigate | Q Quit')
            if organizer.last_backup:
                write(height - 1, f'Last backup: {organizer.last_backup}')
            screen.refresh()
            return True

        def confirm_quit():
            if not organizer.session.has_unsaved_edits:
                return True
            write(screen.getmaxyx()[0] - 1, 'Discard unsaved starred order and quit? [y/N]', curses.A_BOLD)
            screen.clrtoeol()
            screen.refresh()
            answer = screen.get_wch()
            return isinstance(answer, str) and answer.lower() == 'y'

        def action(callback, label):
            # Existing destination/confirmation prompts run in normal terminal mode;
            # edits themselves stay in the continuously updated preview above.
            curses.def_prog_mode()
            curses.endwin()
            try:
                print(f'\n{label}\n', flush=True)
                callback()
            except (OSError, ValueError, subprocess.SubprocessError) as error:
                organizer.report_error(error, label)
                state.status = f'{label} did not complete. See the terminal message.'
            else:
                state.status = f'Returned from {label}; review the current preview.'
            try:
                input('Press Enter to return to the live preview… ')
            finally:
                curses.reset_prog_mode()
                screen.refresh()
                screen.clearok(True)
                try:
                    curses.curs_set(0)
                except curses.error:
                    pass

        while True:
            ready = draw()
            key = screen.get_wch()
            if isinstance(key, str):
                key = key.lower()
            if key == 'q':
                if confirm_quit():
                    return
                state.status = 'Kept the preview; nothing discarded.'
                continue
            if not ready:
                continue
            if key in (curses.KEY_DOWN, 'j'):
                state.navigate(1)
            elif key in (curses.KEY_UP, 'k'):
                state.navigate(-1)
            elif key == curses.KEY_NPAGE:
                state.navigate(screen.getmaxyx()[0] - 10)
            elif key == curses.KEY_PPAGE:
                state.navigate(-(screen.getmaxyx()[0] - 10))
            elif key == curses.KEY_HOME:
                state.navigate(-len(state.rows))
            elif key == curses.KEY_END:
                state.navigate(len(state.rows))
            elif key in (' ', 's', 'm', 'u', '+', '=', '-', '_'):
                state.edit(key)
            elif key == 'v':
                organizer.details = not organizer.details
            elif key == 'r':
                try:
                    changed = organizer.session.refresh_if_changed()
                    state.status = 'Refreshed; favourite edits retained. Review the new preview.' if changed else 'Disk data is current; preview edits retained.'
                except (OSError, ValueError) as error:
                    state.status = f'Refresh stopped: {error}'
            elif key == 'a':
                action(organizer.apply, 'Apply preview')
            elif key == 'b':
                action(organizer.full_backup, 'Back up registered profiles only')
            elif key == 'd':
                folder = state.folder
                action(lambda: organizer.backup(remove=True, folder=folder), 'Back up and remove selected profile')

    curses.wrapper(view)
