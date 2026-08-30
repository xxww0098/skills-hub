#!/usr/bin/env python3
"""Native Qt5 Widgets Cua Lab — third-toolkit path when PyQt5 is installed."""
import os
import sys

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QApplication,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

TITLE = os.environ.get("CUA_LAB_TITLE", "Cua Lab Qt")


class Lab(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(TITLE)
        self.resize(640, 520)
        self.acc = 0
        self.pending = None
        self.op = None
        self.fresh = True
        self.counter = 0

        root = QVBoxLayout(self)
        title = QLabel("Cua Lab Qt")
        title.setAccessibleName("Cua Lab Qt")
        root.addWidget(title)

        row = QHBoxLayout()
        self.counter_l = QLabel("0")
        self.counter_l.setAccessibleName("Probe Counter")
        inc = QPushButton("Increment")
        inc.setAccessibleName("Probe Increment")
        inc.clicked.connect(self.on_inc)
        row.addWidget(QLabel("Counter:"))
        row.addWidget(self.counter_l)
        row.addWidget(inc)
        row.addStretch()
        root.addLayout(row)

        nrow = QHBoxLayout()
        self.name = QLineEdit()
        self.name.setAccessibleName("Probe Name Field")
        sub = QPushButton("Submit")
        sub.setAccessibleName("Probe Submit")
        sub.clicked.connect(self.on_submit)
        self.hello = QLabel("")
        self.hello.setAccessibleName("Probe Hello")
        nrow.addWidget(self.name)
        nrow.addWidget(sub)
        nrow.addWidget(self.hello)
        root.addLayout(nrow)

        grow = QHBoxLayout()
        self.gain = QSlider(Qt.Horizontal)
        self.gain.setRange(0, 100)
        self.gain.setValue(25)
        self.gain.setAccessibleName("Probe Gain")
        self.gain.valueChanged.connect(self.on_gain)
        self.gain_l = QLabel("25")
        self.gain_l.setAccessibleName("Probe Gain Value")
        grow.addWidget(QLabel("Gain"))
        grow.addWidget(self.gain)
        grow.addWidget(self.gain_l)
        root.addLayout(grow)

        rrow = QHBoxLayout()
        a = QPushButton("Row Alpha")
        a.setAccessibleName("Probe Row Alpha")
        a.clicked.connect(lambda: self.set_row("alpha"))
        b = QPushButton("Row Beta")
        b.setAccessibleName("Probe Row Beta")
        b.clicked.connect(lambda: self.set_row("beta"))
        self.row_out = QLabel("none")
        self.row_out.setAccessibleName("Probe Row")
        rrow.addWidget(a)
        rrow.addWidget(b)
        rrow.addWidget(self.row_out)
        rrow.addStretch()
        root.addLayout(rrow)

        self.result = QLabel("0")
        self.result.setAccessibleName("Probe Result")
        root.addWidget(self.result)

        grid = QGridLayout()
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
            btn = QPushButton(text)
            btn.setAccessibleName(name)
            btn.clicked.connect(lambda _=False, n=name: self.on_key(n))
            grid.addWidget(btn, i // 4, i % 4)
        root.addLayout(grid)

        self.log = QLabel("ready")
        self.log.setAccessibleName("Probe Log")
        root.addWidget(self.log)

    def say(self, msg: str) -> None:
        self.log.setText(msg)

    def on_inc(self) -> None:
        self.counter += 1
        self.counter_l.setText(str(self.counter))
        self.say(f"increment={self.counter}")

    def on_submit(self) -> None:
        v = self.name.text()
        self.hello.setText("hello " + v)
        self.say("submit=" + v)

    def on_gain(self, v: int) -> None:
        self.gain_l.setText(str(v))
        self.say(f"gain={v}")

    def set_row(self, name: str) -> None:
        self.row_out.setText(name)
        self.say("row=" + name)

    def on_key(self, label: str) -> None:
        if label.startswith("Probe Key "):
            d = int(label.split()[-1])
            if self.fresh:
                self.pending = 0
                self.fresh = False
            self.pending = (self.pending or 0) * 10 + d
            self.result.setText(str(self.pending))
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
            self.result.setText("0")
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
            self.result.setText(str(self.acc))
            self.say(f"result={self.acc}")


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Cua Lab Qt")
    w = Lab()
    w.show()
    return app.exec_()


if __name__ == "__main__":
    raise SystemExit(main())
