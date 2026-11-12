# Omarchy → Monkeytype theme sync

A small personal Chrome extension that keeps [Monkeytype](https://monkeytype.com)'s theme in sync with the current [Omarchy](https://omarchy.org) theme. When you switch themes in Omarchy, every open Monkeytype tab changes right away, without a reload.

## How it works

```
Omarchy theme switch
  → host/omarchy_monkeytype_host.py sees ~/.local/state/omarchy/current/theme.name change
  → looks up the Omarchy theme in config.json
  → sends the colors to the extension (Chrome native messaging)
  → extension/content.js overrides Monkeytype's theme CSS variables
```

- **Changes are local only.** The extension overrides colors in the page. It doesn't touch your Monkeytype settings or account, and turning the extension off brings back your own theme.
- **No background service.** Chrome starts the host script when the extension loads and stops it with Chrome. It uses only the Python standard library.

## Install

Requirements: Omarchy, Google Chrome, Python 3.11+ (all included in Omarchy except Chrome).

```bash
git clone https://github.com/Maclogger/monkeytype-themeswitcher ~/monkeytype-themeswitcher && ~/monkeytype-themeswitcher/install.sh
```

The script registers the helper with Chrome, copies the extension's path to your clipboard, and opens `chrome://extensions`. There:

1. Turn on **Developer mode** (top right).
2. Click **Load unpacked**, press `Ctrl+L`, paste the path, and confirm.

That's it. The mapping in `config.json` works out of the box.

Chrome only remembers the unpacked extension on this machine, so step 2 is needed once per machine. Google Chrome can't load extensions from the command line, so the script can't do it for you.

- `install.sh` is safe to re-run. Re-run it if you move the folder, because Chrome stores the helper's full path.
- `./install.sh --uninstall` removes the registration. Remove the extension itself in `chrome://extensions`.
- Updating: `git pull`, then click the reload icon on the extension card (this also restarts the helper). Changes to `config.json` alone apply on the next theme switch.

## Configure

Edit `config.json`. The file is re-read on every theme change, so no extension reload is needed.

```json
{
  "default": "auto",
  "themes": {
    "nord": "nord",
    "tokyo-night": "auto",
    "matte-black": "off"
  }
}
```

Keys are Omarchy theme names, as in `~/.local/state/omarchy/current/theme.name`. Values can be:

| Value | Effect |
|---|---|
| a Monkeytype theme name (e.g. `serika_dark`) | use that Monkeytype theme. The full list is in `host/monkeytype-themes.json` |
| `"auto"` | build a palette from the Omarchy theme's own `colors.toml` |
| `"off"` | leave Monkeytype alone and show your normal Monkeytype theme |

`default` applies to Omarchy themes that aren't listed, such as a new theme you've just installed.

### New Monkeytype themes

```bash
./scripts/update-monkeytype-themes.py
```

This refreshes `host/monkeytype-themes.json` from the Monkeytype source on GitHub. It also prints the closest color matches for each installed Omarchy theme.

## If Monkeytype changes

All site-specific code is in `extension/content.js`. Right now it relies on the CSS variables `--bg-color`, `--main-color` and so on, and on the optional `<link id="currentTheme">` that loads `/themes/<name>.css`.

## Debugging

- Extension: `chrome://extensions` → this extension → *service worker* → Console.
- Host: run `./host/omarchy_monkeytype_host.py` in a terminal. It prints one binary-framed message, and logs go to stderr.
