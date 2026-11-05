"""Neon cyberpunk look for ProtonMD (GTK4 + libadwaita named colours and CSS)."""
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gdk, Gtk  # noqa: E402

INK, PANEL, TERMINAL = "#0D0F14", "#12151C", "#0A0C10"
CYAN, MAGENTA, MINT, AMBER = "#00C8D6", "#FF2BD6", "#2BFFB0", "#FFC145"

CSS = f"""
@define-color window_bg_color {INK};
@define-color window_fg_color #E6EBF2;
@define-color view_bg_color {TERMINAL};
@define-color view_fg_color #E6EBF2;
@define-color headerbar_bg_color {INK};
@define-color headerbar_fg_color #E6EBF2;
@define-color headerbar_border_color alpha({CYAN}, .45);
@define-color sidebar_bg_color {PANEL};
@define-color sidebar_fg_color #E6EBF2;
@define-color sidebar_border_color alpha({CYAN}, .35);
@define-color card_bg_color {PANEL};
@define-color card_fg_color #E6EBF2;
@define-color popover_bg_color {PANEL};
@define-color dialog_bg_color {INK};
@define-color accent_color {CYAN};
@define-color accent_bg_color {CYAN};
@define-color accent_fg_color {INK};
@define-color success_color {MINT};
@define-color warning_color {AMBER};
@define-color error_color {MAGENTA};
@define-color destructive_bg_color {MAGENTA};
@define-color destructive_fg_color {INK};

window, .background {{ background-color: {INK}; }}

/* title bars: dark with a glowing cyan underline */
headerbar {{
  background-image: linear-gradient(to bottom, #151922, {INK});
  border-bottom: 1px solid alpha({CYAN}, .55);
  box-shadow: 0 1px 14px alpha({CYAN}, .20);
}}
.neon-title {{
  font-family: "JetBrains Mono", "Fira Code", monospace;
  font-weight: 800;
  font-size: 17px;
  letter-spacing: 5px;
  color: #F2F4F8;
  text-shadow: 0 0 10px alpha({CYAN}, .95), 2px 0 alpha({MAGENTA}, .7), -2px 0 alpha({CYAN}, .7);
}}
windowtitle .title {{ font-family: "JetBrains Mono", monospace; font-size: 14px; letter-spacing: 0; }}
windowtitle .subtitle {{ color: {CYAN}; }}

/* sidebar */
.navigation-sidebar {{ background: transparent; padding: 6px 4px; }}
.navigation-sidebar row {{
  border-radius: 6px; margin: 2px 4px; padding: 2px 4px;
  border: 1px solid transparent;
  transition: all 150ms ease;
}}
.navigation-sidebar row:hover {{
  background-color: alpha({CYAN}, .08);
  border-color: alpha({CYAN}, .25);
}}
.navigation-sidebar row:selected {{
  background-color: alpha({CYAN}, .16);
  border-color: alpha({CYAN}, .70);
  box-shadow: inset 3px 0 0 {CYAN}, 0 0 14px alpha({CYAN}, .30);
  color: #FFFFFF;
}}
.navigation-sidebar row:selected image {{ color: {MAGENTA}; -gtk-icon-shadow: 0 0 6px alpha({MAGENTA}, .9); }}

/* the Libraries button: big, magenta, pulsing so it can't be missed */
@keyframes neon-pulse {{
  0%   {{ box-shadow: 0 0 6px alpha({MAGENTA}, .35), inset 0 0 6px alpha({MAGENTA}, .15); }}
  50%  {{ box-shadow: 0 0 20px alpha({MAGENTA}, .85), inset 0 0 10px alpha({MAGENTA}, .30); }}
  100% {{ box-shadow: 0 0 6px alpha({MAGENTA}, .35), inset 0 0 6px alpha({MAGENTA}, .15); }}
}}
button.libraries-btn {{
  margin: 8px 10px; padding: 10px 12px;
  background-image: none; background-color: alpha({MAGENTA}, .10);
  color: #FFE9FB; font-weight: 800; letter-spacing: 1px;
  border: 1px solid {MAGENTA}; border-radius: 8px;
  animation: neon-pulse 2.6s ease-in-out infinite;
}}
button.libraries-btn:hover {{ background-color: alpha({MAGENTA}, .26); }}

/* result cards */
list.boxed-list, .card {{
  background-color: {PANEL};
  border: 1px solid alpha({CYAN}, .30);
  border-radius: 10px;
  box-shadow: 0 0 16px alpha({CYAN}, .07);
}}
list.boxed-list > row {{ border-color: alpha({CYAN}, .14); }}
list.boxed-list > row:hover {{ background-color: alpha({CYAN}, .06); }}
preferencesgroup .heading, preferencesgroup .title-4 {{
  color: {CYAN}; font-family: "JetBrains Mono", monospace; letter-spacing: 2px; font-weight: 800;
  text-shadow: 0 0 8px alpha({CYAN}, .5);
}}
row .subtitle {{ color: #A9B4C2; }}

/* buttons */
button.suggested-action {{
  background-image: none; background-color: alpha({CYAN}, .16); color: {CYAN};
  border: 1px solid {CYAN}; box-shadow: 0 0 10px alpha({CYAN}, .35);
}}
button.suggested-action:hover {{ background-color: alpha({CYAN}, .32); }}
button.destructive-action {{
  background-image: none; background-color: alpha({MAGENTA}, .16); color: {MAGENTA};
  border: 1px solid {MAGENTA}; box-shadow: 0 0 10px alpha({MAGENTA}, .35);
}}
button.destructive-action:hover {{ background-color: alpha({MAGENTA}, .32); }}
headerbar button {{ border-radius: 6px; }}

/* problem rows get a glowing edge so they stand out at a glance */
list.boxed-list > row.st-warn {{
  background-image: linear-gradient(to right, alpha({AMBER}, .10), transparent 60%);
  box-shadow: inset 3px 0 0 {AMBER};
}}
list.boxed-list > row.st-fail {{
  background-image: linear-gradient(to right, alpha({MAGENTA}, .14), transparent 60%);
  box-shadow: inset 3px 0 0 {MAGENTA};
}}
list.boxed-list > row.st-fail .title {{ color: #FFD6F6; text-shadow: 0 0 8px alpha({MAGENTA}, .6); }}

/* status icons glow */
image.success {{ -gtk-icon-shadow: 0 0 6px alpha({MINT}, .8); }}
image.warning {{ -gtk-icon-shadow: 0 0 6px alpha({AMBER}, .8); }}
image.error   {{ -gtk-icon-shadow: 0 0 8px alpha({MAGENTA}, .9); }}

/* scrollbars + switches */
scrollbar slider {{ background-color: alpha({CYAN}, .45); border-radius: 6px; }}
switch:checked {{ background-color: alpha({CYAN}, .55); box-shadow: 0 0 8px alpha({CYAN}, .55); }}
separator {{ background-color: alpha({CYAN}, .20); }}
"""


def apply():
    Adw.StyleManager.get_default().set_color_scheme(Adw.ColorScheme.FORCE_DARK)
    provider = Gtk.CssProvider()
    if hasattr(provider, "load_from_string"):
        provider.load_from_string(CSS)
    else:
        provider.load_from_data(CSS.encode())
    Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), provider,
                                              Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
