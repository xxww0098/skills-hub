#!/usr/bin/env python3
"""Cua Lab on WebKitGTK 4.1 — the same Linux surface Tauri embeds (Wry/WebKitGTK)."""
import os
import sys

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("WebKit2", "4.1")
from gi.repository import Gtk, WebKit2, GLib  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
HTML = os.path.abspath(os.path.join(HERE, "..", "web", "index.html"))
TITLE = os.environ.get("CUA_LAB_TITLE", "Cua Lab")


def main() -> int:
    if not os.path.isfile(HTML):
        print(f"missing {HTML}", file=sys.stderr)
        return 2
    win = Gtk.Window(title=TITLE)
    win.set_default_size(920, 780)
    web = WebKit2.WebView()
    settings = web.get_settings()
    settings.set_enable_developer_extras(True)
    web.load_uri("file://" + HTML)
    win.add(web)
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    GLib.timeout_add(250, lambda: win.set_title(TITLE) or False)
    Gtk.main()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
