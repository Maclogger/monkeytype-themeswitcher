#!/usr/bin/env python3
"""Chrome native messaging host: tells the extension which Monkeytype theme to show.

Chrome starts this script when the extension connects. It watches the current
Omarchy theme and, whenever it changes (and once at startup), sends one message
with the colors to apply. The mapping is resolved here, and config.json is
re-read on every change, so editing config.json needs no extension reload.

Only the Python standard library is used.
"""

import json
import os
import struct
import sys
import threading
import time
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "config.json"
MT_THEMES_PATH = ROOT / "host" / "monkeytype-themes.json"

STATE = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local/state")) / "omarchy/current"
THEME_NAME_PATH = STATE / "theme.name"
THEME_GENERATION_PATH = STATE / "theme.generation"
COLORS_PATH = STATE / "theme" / "colors.toml"

POLL_SECONDS = 0.4
# omarchy-theme-set writes theme.name before all theme files are staged.
SETTLE_SECONDS = 0.3

COLOR_KEYS = ("bg", "main", "caret", "sub", "subAlt", "text",
              "error", "errorExtra", "colorfulError", "colorfulErrorExtra")


def send(message):
    data = json.dumps(message).encode()
    sys.stdout.buffer.write(struct.pack("=I", len(data)) + data)
    sys.stdout.buffer.flush()


def log(*args):
    # stderr ends up in Chrome's log, never in the message stream.
    print("[omarchy-monkeytype]", *args, file=sys.stderr, flush=True)


def watch_stdin_and_exit():
    """Chrome closes stdin when the extension disconnects; exit then."""
    try:
        while True:
            header = sys.stdin.buffer.read(4)
            if len(header) < 4:
                break
            (length,) = struct.unpack("=I", header)
            sys.stdin.buffer.read(length)  # extension messages are ignored
    finally:
        os._exit(0)


def read_json(path):
    with open(path) as f:
        return json.load(f)


def auto_colors():
    """Build a Monkeytype palette from the active Omarchy colors.toml."""
    with open(COLORS_PATH, "rb") as f:
        c = tomllib.load(f)
    get = lambda *keys: next((c[k] for k in keys if k in c), None)
    red = get("red", "bright_red") or "#ca4754"
    return {
        "bg": get("background"),
        "main": get("accent", "blue"),
        "caret": get("accent", "blue"),
        "sub": get("dark_foreground", "muted", "foreground"),
        "subAlt": get("lighter_background", "selection", "dark_background", "background"),
        "text": get("foreground"),
        "error": red,
        "errorExtra": get("bright_red", "red") or red,
        "colorfulError": red,
        "colorfulErrorExtra": get("bright_red", "red") or red,
    }


def resolve(omarchy_theme):
    try:
        config = read_json(CONFIG_PATH)
    except (OSError, ValueError) as e:
        log("cannot read config.json:", e)
        config = {}
    choice = config.get("themes", {}).get(omarchy_theme, config.get("default", "auto"))

    if choice == "off":
        return {"type": "theme", "omarchy": omarchy_theme, "mode": "off"}

    if choice != "auto":
        mt = read_json(MT_THEMES_PATH).get(choice)
        if mt:
            return {
                "type": "theme", "omarchy": omarchy_theme, "mode": "monkeytype",
                "name": choice, "hasCss": bool(mt.get("hasCss")),
                "colors": {k: mt[k] for k in COLOR_KEYS},
            }
        log(f"unknown Monkeytype theme {choice!r} for {omarchy_theme!r}, using auto")

    try:
        colors = auto_colors()
    except (OSError, ValueError) as e:
        log("cannot read Omarchy colors:", e)
        return {"type": "theme", "omarchy": omarchy_theme, "mode": "off"}
    return {"type": "theme", "omarchy": omarchy_theme, "mode": "auto", "colors": colors}


def fingerprint():
    """Changes whenever the theme or config.json changes."""
    parts = []
    for p in (THEME_NAME_PATH, THEME_GENERATION_PATH, CONFIG_PATH, MT_THEMES_PATH):
        try:
            parts.append(p.stat().st_mtime_ns)
        except OSError:
            parts.append(None)
    return tuple(parts)


def main():
    threading.Thread(target=watch_stdin_and_exit, daemon=True).start()
    last = None
    while True:
        current = fingerprint()
        if current != last:
            if last is not None:
                time.sleep(SETTLE_SECONDS)
                current = fingerprint()
            last = current
            try:
                name = THEME_NAME_PATH.read_text().strip()
                message = resolve(name)
                send(message)
                log("sent", message.get("omarchy"), message.get("mode"), message.get("name", ""))
            except OSError as e:
                log("cannot read current Omarchy theme:", e)
        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    main()
