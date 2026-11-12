#!/usr/bin/env python3
"""Refresh host/monkeytype-themes.json from the Monkeytype source on GitHub.

Run this when Monkeytype adds themes. It also prints the Monkeytype themes
closest in color to each installed Omarchy theme, to help with config.json.
"""

import glob
import json
import os
import re
import tomllib
import urllib.request
from pathlib import Path

SOURCE = "https://raw.githubusercontent.com/monkeytypegame/monkeytype/master/frontend/src/ts/constants/themes.ts"
OUT = Path(__file__).resolve().parent.parent / "host" / "monkeytype-themes.json"
KEYS = {"bg", "main", "caret", "sub", "subAlt", "text",
        "error", "errorExtra", "colorfulError", "colorfulErrorExtra"}


def fetch_themes():
    src = urllib.request.urlopen(SOURCE, timeout=30).read().decode()
    body = src[src.index("export const themes"):]
    themes = {}
    for m in re.finditer(r'\n  "?([a-z0-9_]+)"?: \{(.*?)\n  \}', body, re.S):
        fields = dict(re.findall(r'(\w+): "(#[0-9a-fA-F]+)"', m.group(2)))
        if not KEYS <= fields.keys():
            print(f"skipping {m.group(1)}: missing colors")
            continue
        theme = {k: fields[k] for k in KEYS}
        if re.search(r"hasCss: true", m.group(2)):
            theme["hasCss"] = True
        themes[m.group(1)] = theme
    if len(themes) < 100:
        raise SystemExit(f"only parsed {len(themes)} themes; the source format probably changed")
    return themes


def rgb(c):
    c = c.lstrip("#")
    if len(c) in (3, 4):
        c = "".join(x * 2 for x in c[:3])
    return [int(c[i:i + 2], 16) for i in (0, 2, 4)]


def dist(a, b):
    return sum((x - y) ** 2 for x, y in zip(rgb(a), rgb(b))) ** 0.5


def suggest(themes):
    for f in sorted(glob.glob(os.path.expanduser("~/.local/share/omarchy/themes/*/colors.toml"))
                    + glob.glob(os.path.expanduser("~/.config/omarchy/themes/*/colors.toml"))):
        with open(f, "rb") as fh:
            c = tomllib.load(fh)
        score = lambda k: (2 * dist(themes[k]["bg"], c["background"])
                           + dist(themes[k]["main"], c["accent"])
                           + dist(themes[k]["text"], c["foreground"]))
        best = sorted(themes, key=score)[:4]
        print(f"{Path(f).parent.name:18} {' '.join(best)}")


if __name__ == "__main__":
    themes = fetch_themes()
    OUT.write_text(json.dumps(themes, indent=2, sort_keys=True) + "\n")
    print(f"wrote {len(themes)} themes to {OUT}\n\nClosest matches per Omarchy theme:")
    suggest(themes)
