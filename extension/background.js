// Keeps a connection to the native host (which watches the Omarchy theme)
// and stores the latest theme in chrome.storage.local. Content scripts react
// to storage changes, so this file knows nothing about Monkeytype itself.

const HOST = "com.github.omarchy_monkeytype";
let port = null;
let retryMs = 1000;

function connect() {
  if (port) return;
  try {
    port = chrome.runtime.connectNative(HOST);
  } catch (e) {
    console.warn("connectNative failed", e);
    scheduleReconnect();
    return;
  }
  port.onMessage.addListener((msg) => {
    retryMs = 1000;
    if (msg && msg.type === "theme") {
      chrome.storage.local.set({ theme: { ...msg, at: Date.now() } });
    }
  });
  port.onDisconnect.addListener(() => {
    console.warn("native host disconnected", chrome.runtime.lastError?.message);
    port = null;
    scheduleReconnect();
  });
}

function scheduleReconnect() {
  setTimeout(connect, retryMs);
  retryMs = Math.min(retryMs * 2, 60000);
}

chrome.runtime.onStartup.addListener(connect);
chrome.runtime.onInstalled.addListener(connect);
// A Monkeytype tab pings on load, which also wakes this worker if needed.
chrome.runtime.onMessage.addListener((msg, _sender, reply) => {
  if (msg === "ping") {
    connect();
    reply("pong");
  }
});
connect();
