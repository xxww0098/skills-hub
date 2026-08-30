#!/usr/bin/env python3
"""Drive a Cua Lab window the way SKILL.md says (live cua-driver)."""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
CUA = Path(os.environ.get("CUA") or (SKILL / "scripts" / "cua-use"))


def run_cua(*args: str) -> tuple[int, str]:
    env = os.environ.copy()
    env.setdefault("DISPLAY", ":1")
    env["PATH"] = os.path.expanduser("~/.local/bin") + ":" + env.get("PATH", "")
    p = subprocess.run([str(CUA), *args], capture_output=True, text=True, env=env)
    out = (p.stdout or "").strip()
    if p.returncode != 0 and p.stderr:
        out = (out + "\n" + p.stderr.strip()).strip()
    return p.returncode, out


def parse_json(raw: str) -> object:
    raw = raw.strip()
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        start = min([i for i in (raw.find("{"), raw.find("[")) if i >= 0], default=-1)
        if start >= 0:
            return json.loads(raw[start:])
        raise


def call(tool: str, payload: dict) -> tuple[int, object, str]:
    rc, raw = run_cua("call", tool, json.dumps(payload))
    data: object = raw
    if raw:
        try:
            data = parse_json(raw)
        except json.JSONDecodeError:
            pass
    return rc, data, raw


def find_window(title: str, app_name: str | None, timeout: float) -> dict:
    deadline = time.time() + timeout
    last = None
    while time.time() < deadline:
        rc, data, raw = call("list_windows", {"on_screen_only": True})
        last = raw
        if rc == 0 and isinstance(data, dict):
            for w in data.get("windows") or []:
                if title.lower() not in str(w.get("title") or "").lower():
                    continue
                if app_name and app_name.lower() != str(w.get("app_name") or "").lower():
                    continue
                return w
        time.sleep(0.35)
    raise SystemExit(f"window {title!r} app={app_name!r} not found\n{last}")


def elements_of(state: object) -> list[dict]:
    if not isinstance(state, dict):
        return []
    if isinstance(state.get("elements"), list):
        return state["elements"]
    sc = state.get("structuredContent")
    if isinstance(sc, dict) and isinstance(sc.get("elements"), list):
        return sc["elements"]
    return []


def find_el(els: list[dict], needle: str) -> dict | None:
    n = needle.lower()
    exact = next((e for e in els if str(e.get("label") or "").lower() == n), None)
    if exact:
        return exact
    for e in els:
        blob = " ".join(str(e.get(k) or "") for k in ("label", "role", "value")).lower()
        if n in blob:
            return e
    return None


def click_el(pid: int, el: dict, foreground: bool = False) -> tuple[int, object, str]:
    payload: dict = {"pid": pid, "element_token": el["element_token"]}
    if foreground:
        payload["delivery_mode"] = "foreground"
    return call("click", payload)


def click_xy(pid: int, window_id: int, x: float, y: float, foreground: bool) -> tuple[int, object, str]:
    payload = {"pid": pid, "window_id": window_id, "x": x, "y": y}
    if foreground:
        payload["delivery_mode"] = "foreground"
    return call("click", payload)


def snapshot(pid: int, window_id: int, png: Path | None, query: str | None = None) -> dict:
    payload: dict = {"pid": pid, "window_id": window_id}
    if png:
        payload["screenshot_out_file"] = str(png)
    if query:
        payload["query"] = query
    rc, data, raw = call("get_window_state", payload)
    if rc != 0 or not isinstance(data, dict):
        raise SystemExit(f"get_window_state failed ({rc}): {raw[:800]}")
    return data


def ocr(png: Path) -> str:
    if not shutil.which("tesseract") or not png.is_file():
        return ""
    p = subprocess.run(
        ["tesseract", str(png), "stdout", "--psm", "6"],
        capture_output=True,
        text=True,
    )
    return p.stdout or ""


def classify(title: str, app_name: str, els: list[dict], degraded: object) -> str:
    app = (app_name or "").lower()
    title_l = title.lower()
    labels = [str(e.get("label") or "") for e in els]
    roles = {str(e.get("role") or "") for e in els}
    if degraded:
        return "degraded-no-ax"
    if "electron" in app:
        if len(els) <= 2 and "frame" in roles:
            return "electron-px"
        return "electron"
    if app in {"cua-lab", "cua-lab-webkit.py"} or "webkit" in app:
        return "tauri-linux" if "Probe Increment" in labels else "webview"
    if "qt" in app or title_l.endswith("qt"):
        return "qt"
    if "gtk" in app or title_l.endswith("gtk"):
        return "gtk"
    if "Probe Increment" in labels:
        return "native-ax"
    return "unknown"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--title", required=True)
    ap.add_argument("--app-name", default="")
    ap.add_argument("--out", default="/tmp/cua-lab-drive")
    ap.add_argument("--do-calc", action="store_true")
    ap.add_argument("--try-cdp", action="store_true")
    ap.add_argument("--foreground", action="store_true")
    ap.add_argument("--timeout", type=float, default=20.0)
    args = ap.parse_args()

    out = Path(args.out)
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    record: dict = {"title": args.title, "app_name": args.app_name, "steps": []}

    win = find_window(args.title, args.app_name or None, args.timeout)
    pid, wid = int(win["pid"]), int(win["window_id"])
    record["window"] = win
    (out / "window.json").write_text(json.dumps(win, indent=2))

    before = snapshot(pid, wid, out / "before.png")
    (out / "before-meta.json").write_text(
        json.dumps({k: before.get(k) for k in before if k != "screenshot"}, indent=2)[:200_000]
    )
    els = elements_of(before)
    toolkit = classify(args.title, str(win.get("app_name") or ""), els, before.get("degraded"))
    record["classified"] = toolkit
    record["degraded"] = before.get("degraded")
    record["degraded_reason"] = before.get("degraded_reason")
    record["labels"] = [e.get("label") for e in els if e.get("label")]
    record["element_count"] = len(els)
    (out / "classify.txt").write_text(f"{toolkit}\napp={win.get('app_name')}\n")

    if args.try_cdp:
        rc, data, raw = call("browser_prepare", {"pid": pid})
        record["browser_prepare"] = {"rc": rc, "data": data, "raw": raw[:2000]}
        (out / "browser_prepare.json").write_text(json.dumps(record["browser_prepare"], indent=2)[:20_000])

    inc = find_el(els, "Probe Increment")
    fg = args.foreground or toolkit == "electron-px"
    if inc and inc.get("element_token"):
        rc, data, raw = click_el(pid, inc, foreground=fg)
        record["click_increment"] = {"rc": rc, "channel": "ax", "data": data, "raw": raw[:1500]}
    else:
        rc, data, raw = click_xy(pid, wid, 170, 131, foreground=True)
        record["click_increment"] = {"rc": rc, "channel": "px", "data": data, "raw": raw[:1500]}
        # Electron: background is refused — the helper already used foreground.
        if isinstance(data, dict) and data.get("code") == "background_unavailable":
            rc, data, raw = click_xy(pid, wid, 170, 131, foreground=True)
            record["click_increment"] = {"rc": rc, "channel": "px-fg", "data": data, "raw": raw[:1500]}

    time.sleep(0.35)
    after = snapshot(pid, wid, out / "after-increment.png")
    text = ocr(out / "after-increment.png")
    record["ocr_increment"] = text[:500]
    record["ok_increment"] = (
        record["click_increment"]["rc"] == 0
        and "background_unavailable" not in json.dumps(record["click_increment"].get("data"))
        and (out / "after-increment.png").stat().st_size > 0
    )

    if args.do_calc and toolkit != "electron-px" and toolkit != "degraded-no-ax":
        # Paint tab hides the AX keypad; switch back if the control exists.
        st0 = snapshot(pid, wid, None)
        els0 = elements_of(st0)
        if find_el(els0, "Probe Canvas") and not find_el(els0, "Probe Key 6"):
            tab = find_el(els0, "Probe Surface Tauri")
            if tab and tab.get("element_token"):
                click_el(pid, tab, foreground=fg)
                time.sleep(0.3)
        calc = []
        for name in ("Probe Key 6", "Multiply", "Probe Key 7", "Equals"):
            st = snapshot(pid, wid, None)
            el = find_el(elements_of(st), name)
            if not el:
                calc.append({"name": name, "channel": "miss"})
                continue
            rc, data, raw = click_el(pid, el, foreground=fg)
            calc.append({"name": name, "rc": rc, "data": data})
            time.sleep(0.15)
        snapshot(pid, wid, out / "after-calc.png")
        record["calc"] = calc
        record["ocr_calc"] = ocr(out / "after-calc.png")[:500]
        record["ok_calc"] = "42" in (record["ocr_calc"] or "") or any(
            (s.get("rc") == 0) for s in calc
        )

    (out / "record.json").write_text(json.dumps(record, indent=2)[:120_000])
    print(json.dumps(record, indent=2)[:6000])
    return 0 if record.get("ok_increment") else 1


if __name__ == "__main__":
    raise SystemExit(main())
