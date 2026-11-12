// Everything that depends on how monkeytype.com works lives in this file.
// If the site changes, this is the only place to fix.
//
// How Monkeytype themes work (checked November 2026):
//   - <style id="theme"> sets CSS variables on :root (--bg-color, --main-color, ...)
//   - themes with extra styling also load <link id="currentTheme" href="/themes/<name>.css">
// We override the variables with our own !important rules and swap the extra
// CSS. Nothing is saved to Monkeytype's config or your account.

const STYLE_ID = "omarchy-monkeytype-vars";
const CSS_LINK_ID = "omarchy-monkeytype-css";
const MT_CSS_LINK_ID = "currentTheme";

const VARS = {
  bg: "--bg-color",
  main: "--main-color",
  caret: "--caret-color",
  sub: "--sub-color",
  subAlt: "--sub-alt-color",
  text: "--text-color",
  error: "--error-color",
  errorExtra: "--error-extra-color",
  colorfulError: "--colorful-error-color",
  colorfulErrorExtra: "--colorful-error-extra-color",
};

let current = null; // last theme message from the host

function isActive() {
  return current && current.mode !== "off" && current.colors;
}

function ensureStyle() {
  let style = document.getElementById(STYLE_ID);
  if (!style) {
    style = document.createElement("style");
    style.id = STYLE_ID;
    // Appended to <html> so it works before <head> exists and comes last.
    document.documentElement.appendChild(style);
  }
  return style;
}

function apply() {
  const style = document.getElementById(STYLE_ID);
  if (!isActive()) {
    style?.remove();
    document.getElementById(CSS_LINK_ID)?.remove();
    const mtLink = document.getElementById(MT_CSS_LINK_ID);
    if (mtLink) mtLink.disabled = false;
    return;
  }

  const rules = Object.entries(VARS)
    .filter(([key]) => current.colors[key])
    .map(([key, cssVar]) => `${cssVar}: ${current.colors[key]} !important;`)
    .join(" ");
  const css = `:root { ${rules} }`;
  const s = ensureStyle();
  if (s.textContent !== css) s.textContent = css;

  syncExtraCss();
}

// Called on load and whenever Monkeytype touches its own theme <link>.
function syncExtraCss() {
  if (!isActive()) return;
  const mtLink = document.getElementById(MT_CSS_LINK_ID);
  if (mtLink && !mtLink.disabled) mtLink.disabled = true;

  const wanted = current.hasCss ? `/themes/${current.name}.css` : null;
  let link = document.getElementById(CSS_LINK_ID);
  if (!wanted) {
    link?.remove();
    return;
  }
  if (!link) {
    link = document.createElement("link");
    link.id = CSS_LINK_ID;
    link.rel = "stylesheet";
    document.documentElement.appendChild(link);
  }
  if (link.getAttribute("href") !== wanted) link.setAttribute("href", wanted);
}

function watchMonkeytype() {
  // Monkeytype replaces or edits its theme <link> when its own theme changes.
  new MutationObserver(syncExtraCss).observe(document.head, {
    childList: true,
    subtree: true,
    attributes: true,
    attributeFilter: ["href"],
  });
  syncExtraCss();
}

chrome.storage.local.get("theme").then(({ theme }) => {
  current = theme || null;
  apply();
});

chrome.storage.onChanged.addListener((changes, area) => {
  if (area === "local" && changes.theme) {
    current = changes.theme.newValue || null;
    apply();
  }
});

if (document.head) watchMonkeytype();
else document.addEventListener("DOMContentLoaded", watchMonkeytype, { once: true });

chrome.runtime.sendMessage("ping").catch(() => {});
