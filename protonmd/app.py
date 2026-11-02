import os
import threading

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, GLib, Gtk  # noqa: E402

from . import APP_ID, __version__, checks, config, steam, theme  # noqa: E402
from .model import Status  # noqa: E402

ICONS = {
    Status.OK: ("emblem-ok-symbolic", "success"),
    Status.INFO: ("dialog-information-symbolic", "dim-label"),
    Status.WARN: ("dialog-warning-symbolic", "warning"),
    Status.FAIL: ("dialog-error-symbolic", "error"),
}
SYSTEM_KEY = "__system__"


class Window(Adw.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title="ProtonMD", default_width=1000, default_height=700)
        self.root = steam.find_steam_root()
        self.games = []
        self.selected = SYSTEM_KEY

        self.toasts = Adw.ToastOverlay()
        split = Adw.NavigationSplitView()
        self.toasts.set_child(split)
        self.set_content(self.toasts)

        # sidebar
        self.listbox = Gtk.ListBox(css_classes=["navigation-sidebar"])
        self.listbox.connect("row-selected", self.on_row_selected)
        side_view = Adw.ToolbarView()
        side_head = Adw.HeaderBar()
        side_head.set_title_widget(Gtk.Label(label="PROTONMD", css_classes=["neon-title"]))
        side_view.add_top_bar(side_head)
        self.libs_btn = Gtk.Button(css_classes=["libraries-btn"],
                                   tooltip_text="Choose which Steam libraries ProtonMD shows")
        self.libs_btn.connect("clicked", lambda *_: self.show_libraries())
        side_view.add_bottom_bar(self.libs_btn)
        side_view.set_content(Gtk.ScrolledWindow(child=self.listbox))
        split.set_sidebar(Adw.NavigationPage(title="ProtonMD", child=side_view))

        # content
        self.page = Adw.PreferencesPage()
        self.spinner = Adw.Spinner() if hasattr(Adw, "Spinner") else Gtk.Spinner(spinning=True)
        self.stack = Gtk.Stack()
        self.stack.add_named(self.page, "page")
        busy = Gtk.Box(halign=Gtk.Align.CENTER, valign=Gtk.Align.CENTER)
        busy.append(self.spinner)
        self.stack.add_named(busy, "busy")
        header = Adw.HeaderBar()
        rescan = Gtk.Button(icon_name="view-refresh-symbolic", tooltip_text="Re-scan")
        rescan.connect("clicked", lambda *_: self.refresh())
        header.pack_end(rescan)
        copy = Gtk.Button(icon_name="edit-copy-symbolic", tooltip_text="Copy report for a bug report")
        copy.connect("clicked", self.copy_report)
        header.pack_end(copy)
        self.content_title = Adw.WindowTitle(title="System", subtitle="")
        header.set_title_widget(self.content_title)
        cview = Adw.ToolbarView()
        cview.add_top_bar(header)
        cview.set_content(self.stack)
        split.set_content(Adw.NavigationPage(title="Report", child=cview))

        self.last_report = ""
        self.populate_sidebar()
        self.listbox.select_row(self.listbox.get_row_at_index(0))

    # ----- sidebar -----
    def populate_sidebar(self):
        while (r := self.listbox.get_row_at_index(0)):
            self.listbox.remove(r)
        self.update_libs_button()
        self._add_row("System", SYSTEM_KEY, "computer-symbolic")
        if self.root:
            self.games = [g for g in steam.scan_games(self.root, config.hidden_libraries()) if not g.is_tool]
            for g in sorted(self.games, key=lambda g: g.name.lower()):
                self._add_row(g.name, g.appid, "applications-games-symbolic", tooltip=g.library)

    def update_libs_button(self):
        hidden = len(config.hidden_libraries())
        label = "LIBRARIES" + (f"  ·  {hidden} hidden" if hidden else "")
        self.libs_btn.set_child(Adw.ButtonContent(icon_name="drive-multidisk-symbolic", label=label))

    def _add_row(self, title, key, icon, tooltip=None):
        box = Gtk.Box(spacing=10, margin_top=8, margin_bottom=8, margin_start=6, margin_end=6)
        box.append(Gtk.Image(icon_name=icon))
        box.append(Gtk.Label(label=title, xalign=0, hexpand=True, ellipsize=3))
        row = Gtk.ListBoxRow(child=box)
        row.key = key
        if tooltip:
            row.set_tooltip_text(tooltip)
        self.listbox.append(row)

    def on_row_selected(self, _lb, row):
        if row is not None:
            self.selected = row.key
            self.refresh()

    # ----- libraries -----
    def show_libraries(self):
        if not self.root:
            self.toasts.add_toast(Adw.Toast(title="Steam was not found"))
            return
        win = Adw.PreferencesWindow(transient_for=self, modal=True, title="Libraries", default_width=620, default_height=520)
        page = Adw.PreferencesPage()
        win.add(page)
        every = steam.scan_games(self.root)
        counts = {}
        for g in every:
            if not g.is_tool:
                counts[g.library] = counts.get(g.library, 0) + 1
        hidden = config.hidden_libraries()
        libs = steam.all_libraries(self.root)
        group = Adw.PreferencesGroup(
            title="Steam libraries",
            description="Turn a library off to hide its games from ProtonMD. This only changes what ProtonMD shows; "
                        "nothing is deleted. Libraries on drives you no longer use can be hidden here.")
        rows = []
        for path, registered in libs:
            real = os.path.realpath(path)
            n = counts.get(path, 0)
            where = "Listed in Steam" if registered else "Found on a mounted drive (not listed in Steam)"
            row = Adw.SwitchRow(title=GLib.markup_escape_text(path),
                                subtitle=f"{where} · {n} game{'s' if n != 1 else ''}")
            row.set_active(real not in hidden)
            row.real = real
            row.connect("notify::active", lambda *_: self._save_libraries(rows))
            rows.append(row)
            group.add(row)
        if not libs:
            group.set_description("No Steam libraries were found.")
        page.add(group)
        bulk = Adw.PreferencesGroup()
        clear = Gtk.Button(label="Clear game list (hide all libraries)", halign=Gtk.Align.CENTER, css_classes=["destructive-action"])
        clear.connect("clicked", lambda *_: [r.set_active(False) for r in rows])
        showall = Gtk.Button(label="Show all libraries", halign=Gtk.Align.CENTER)
        showall.connect("clicked", lambda *_: [r.set_active(True) for r in rows])
        box = Gtk.Box(spacing=12, halign=Gtk.Align.CENTER, margin_top=6)
        box.append(clear)
        box.append(showall)
        bulk.add(box)
        page.add(bulk)
        win.present()

    def _save_libraries(self, rows):
        config.set_hidden_libraries([r.real for r in rows if not r.get_active()])
        self.selected = SYSTEM_KEY
        self.populate_sidebar()
        self.listbox.select_row(self.listbox.get_row_at_index(0))

    # ----- running checks off the UI thread -----
    def refresh(self):
        key = self.selected
        self.stack.set_visible_child_name("busy")
        game = next((g for g in self.games if g.appid == key), None)
        self.content_title.set_title(game.name if game else "System")
        self.content_title.set_subtitle(f"App ID {game.appid}" if game else "GPU, drivers and kernel limits")

        def work():
            results = checks.run_system_checks() if key == SYSTEM_KEY else checks.run_game_checks(self.root, game)
            GLib.idle_add(self.show_results, key, results)
        threading.Thread(target=work, daemon=True).start()

    def show_results(self, key, results):
        if key != self.selected:  # user clicked elsewhere meanwhile
            return
        self.page = self._new_page()
        group = Adw.PreferencesGroup()
        if not self.root and key != SYSTEM_KEY:
            group.set_description("Steam was not found.")
        order = sorted(results, key=lambda r: -int(r.status))
        bad = sum(r.status >= Status.WARN for r in results)
        group.set_title("No problems found" if not bad else f"{bad} issue{'s' if bad != 1 else ''} found")
        for r in order:
            group.add(self._row(r))
        if key != SYSTEM_KEY and not results:
            group.set_description("Nothing to check.")
        self.page.add(group)
        if key == SYSTEM_KEY and self.root:
            gone = steam.missing_libraries(self.root)
            if gone:
                self.page.add(Adw.PreferencesGroup(
                    title="Steam library not found",
                    description="Steam lists these libraries, but they aren't reachable. Is the drive mounted?\n" + "\n".join(gone)))
        if key == SYSTEM_KEY and self.root and not self.games:
            hidden = len(config.hidden_libraries())
            msg = ("No games are shown. " + (f"{hidden} librar{'y is' if hidden == 1 else 'ies are'} hidden: "
                   "open Libraries (the drive icon at the top of the sidebar) to show them again."
                   if hidden else "Install a game in Steam, then press Re-scan."))
            self.page.add(Adw.PreferencesGroup(description=msg))
        self.stack.set_visible_child_name("page")
        self.last_report = self._report_text(key, results)

    def _new_page(self):
        old = self.page
        new = Adw.PreferencesPage()
        self.stack.remove(old)
        self.stack.add_named(new, "page")
        return new

    def _row(self, r):
        row = Adw.ActionRow(title=GLib.markup_escape_text(r.title), title_lines=1)
        text = r.detail + (f"\n→ {r.hint}" if r.hint else "")
        row.set_subtitle(GLib.markup_escape_text(text))
        row.set_subtitle_selectable(True)
        icon_name, css = ICONS[r.status]
        img = Gtk.Image(icon_name=icon_name, css_classes=[css])
        row.add_prefix(img)
        if r.fix:
            btn = Gtk.Button(label=r.fix.label, valign=Gtk.Align.CENTER, css_classes=["suggested-action"])
            btn.set_tooltip_text(f"Runs: {r.fix.command}")
            btn.connect("clicked", self.confirm_fix, r)
            row.add_suffix(btn)
        return row

    # ----- fixes -----
    def confirm_fix(self, _btn, r):
        d = Adw.AlertDialog(heading=r.fix.label, body=f"This will run:\n{r.fix.command}\n\nProceed?")
        d.add_response("cancel", "Cancel")
        d.add_response("go", "Apply")
        d.set_response_appearance("go", Adw.ResponseAppearance.SUGGESTED)
        d.connect("response", lambda _d, resp: resp == "go" and self.apply_fix(r))
        d.present(self)

    def apply_fix(self, r):
        try:
            msg = r.fix.run()
        except Exception as e:
            msg = f"Fix failed: {e}"
        self.toasts.add_toast(Adw.Toast(title=msg))
        self.refresh()

    # ----- report -----
    def _report_text(self, key, results):
        lines = [f"ProtonMD {__version__}", ""]
        for r in results:
            lines.append(f"[{r.status.name}] {r.title}: {r.detail}" + (f" | {r.hint}" if r.hint else ""))
        return "\n".join(lines)

    def copy_report(self, *_):
        self.get_clipboard().set(self.last_report)
        self.toasts.add_toast(Adw.Toast(title="Report copied to clipboard"))


class App(Adw.Application):
    def __init__(self):
        super().__init__(application_id=APP_ID)

    def do_startup(self):
        Adw.Application.do_startup(self)
        theme.apply()

    def do_activate(self):
        (self.props.active_window or Window(self)).present()


def main():
    return App().run(None)
