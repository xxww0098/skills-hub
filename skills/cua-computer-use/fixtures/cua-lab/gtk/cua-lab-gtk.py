#!/usr/bin/env python3
"""Native GTK3 Cua Lab — AT-SPI widgets, no webview."""
import os

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib  # noqa: E402

TITLE = os.environ.get("CUA_LAB_TITLE", "Cua Lab GTK")


class Lab(Gtk.Window):
    def __init__(self) -> None:
        super().__init__(title=TITLE)
        self.set_default_size(640, 520)
        self.acc = 0
        self.pending = None
        self.op = None
        self.fresh = True
        self.counter = 0

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        box.set_margin_top(12)
        box.set_margin_bottom(12)
        box.set_margin_start(12)
        box.set_margin_end(12)
        self.add(box)

        title = Gtk.Label(label="Cua Lab GTK")
        title.get_accessible().set_name("Cua Lab GTK")
        box.pack_start(title, False, False, 0)

        row = Gtk.Box(spacing=8)
        self.counter_l = Gtk.Label(label="0")
        self.counter_l.get_accessible().set_name("Probe Counter")
        inc = Gtk.Button(label="Increment")
        inc.get_accessible().set_name("Probe Increment")
        inc.connect("clicked", self.on_inc)
        row.pack_start(Gtk.Label(label="Counter:"), False, False, 0)
        row.pack_start(self.counter_l, False, False, 0)
        row.pack_start(inc, False, False, 0)
        box.pack_start(row, False, False, 0)

        nrow = Gtk.Box(spacing=8)
        self.name = Gtk.Entry()
        self.name.get_accessible().set_name("Probe Name Field")
        sub = Gtk.Button(label="Submit")
        sub.get_accessible().set_name("Probe Submit")
        sub.connect("clicked", self.on_submit)
        self.hello = Gtk.Label(label="")
        self.hello.get_accessible().set_name("Probe Hello")
        nrow.pack_start(self.name, True, True, 0)
        nrow.pack_start(sub, False, False, 0)
        nrow.pack_start(self.hello, False, False, 0)
        box.pack_start(nrow, False, False, 0)

        grow = Gtk.Box(spacing=8)
        self.gain = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 100, 1)
        self.gain.set_value(25)
        self.gain.get_accessible().set_name("Probe Gain")
        self.gain.connect("value-changed", self.on_gain)
        self.gain_l = Gtk.Label(label="25")
        self.gain_l.get_accessible().set_name("Probe Gain Value")
        grow.pack_start(Gtk.Label(label="Gain"), False, False, 0)
        grow.pack_start(self.gain, True, True, 0)
        grow.pack_start(self.gain_l, False, False, 0)
        box.pack_start(grow, False, False, 0)

        rrow = Gtk.Box(spacing=8)
        a = Gtk.Button(label="Row Alpha")
        a.get_accessible().set_name("Probe Row Alpha")
        a.connect("clicked", lambda *_: self.set_row("alpha"))
        b = Gtk.Button(label="Row Beta")
        b.get_accessible().set_name("Probe Row Beta")
        b.connect("clicked", lambda *_: self.set_row("beta"))
        self.row_out = Gtk.Label(label="none")
        self.row_out.get_accessible().set_name("Probe Row")
        rrow.pack_start(a, False, False, 0)
        rrow.pack_start(b, False, False, 0)
        rrow.pack_start(self.row_out, False, False, 0)
        box.pack_start(rrow, False, False, 0)

        self.result = Gtk.Label(label="0")
        self.result.set_name("result")
        self.result.get_accessible().set_name("Probe Result")
        box.pack_start(self.result, False, False, 0)

        grid = Gtk.Grid()
        grid.set_row_spacing(6)
        grid.set_column_spacing(6)
        keys = [
            ("7", "Probe Key 7"),
            ("8", "Probe Key 8"),
            ("9", "Probe Key 9"),
            ("/", "Divide"),
            ("4", "Probe Key 4"),
            ("5", "Probe Key 5"),
            ("6", "Probe Key 6"),
            ("×", "Multiply"),
            ("1", "Probe Key 1"),
            ("2", "Probe Key 2"),
            ("3", "Probe Key 3"),
            ("−", "Minus"),
            ("0", "Probe Key 0"),
            ("C", "Clear"),
            ("=", "Equals"),
            ("+", "Plus"),
        ]
        for i, (text, name) in enumerate(keys):
            btn = Gtk.Button(label=text)
            btn.get_accessible().set_name(name)
            btn.connect("clicked", self.on_key, name)
            grid.attach(btn, i % 4, i // 4, 1, 1)
        box.pack_start(grid, False, False, 0)

        self.log = Gtk.Label(label="ready")
        self.log.set_xalign(0)
        self.log.get_accessible().set_name("Probe Log")
        box.pack_start(self.log, False, False, 0)

        self.connect("destroy", Gtk.main_quit)

    def say(self, msg: str) -> None:
        self.log.set_text(msg)

    def on_inc(self, *_a) -> None:
        self.counter += 1
        self.counter_l.set_text(str(self.counter))
        self.say(f"increment={self.counter}")

    def on_submit(self, *_a) -> None:
        v = self.name.get_text()
        self.hello.set_text("hello " + v)
        self.say("submit=" + v)

    def on_gain(self, scale) -> None:
        v = int(scale.get_value())
        self.gain_l.set_text(str(v))
        self.say(f"gain={v}")

    def set_row(self, name: str) -> None:
        self.row_out.set_text(name)
        self.say("row=" + name)

    def on_key(self, _btn, label: str) -> None:
        if label.startswith("Probe Key "):
            d = int(label.split()[-1])
            if self.fresh:
                self.pending = 0
                self.fresh = False
            self.pending = (self.pending or 0) * 10 + d
            self.result.set_text(str(self.pending))
            self.say(f"digit={d}")
            return
        if label in {"Multiply", "Plus", "Minus", "Divide"}:
            self.acc = self.pending if self.pending is not None else self.acc
            self.op = {"Multiply": "mul", "Plus": "add", "Minus": "sub", "Divide": "div"}[label]
            self.fresh = True
            self.say("op=" + label)
            return
        if label == "Clear":
            self.acc = 0
            self.pending = None
            self.op = None
            self.fresh = True
            self.result.set_text("0")
            self.say("clear")
            return
        if label == "Equals":
            x = self.pending if self.pending is not None else self.acc
            if self.op == "mul":
                self.acc = self.acc * x
            elif self.op == "add":
                self.acc = self.acc + x
            elif self.op == "sub":
                self.acc = self.acc - x
            elif self.op == "div":
                self.acc = float("nan") if x == 0 else self.acc / x
            else:
                self.acc = x
            self.op = None
            self.pending = None
            self.fresh = True
            self.result.set_text(str(self.acc))
            self.say(f"result={self.acc}")


def main() -> None:
    win = Lab()
    win.show_all()
    GLib.timeout_add(200, lambda: win.set_title(TITLE) or False)
    Gtk.main()


if __name__ == "__main__":
    main()
