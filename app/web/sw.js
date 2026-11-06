/* Haq service worker: makes the app installable and opens instantly on repeat visits.
   It caches ONLY the app shell (page, styles, script, icons). Legal answers, voice and every
   /api call always go to the network, so nobody is shown a stale or cached legal answer. */
const SHELL = "haq-shell-v4";
const FILES = ["/", "/static/app.css", "/static/app.js", "/static/i18n.js", "/manifest.webmanifest",
  "/static/icons/icon-192.png", "/static/icons/icon-512.png"];

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(SHELL).then((c) => c.addAll(FILES)).then(() => self.skipWaiting()));
});
self.addEventListener("activate", (e) => {
  e.waitUntil(caches.keys().then((keys) => Promise.all(keys.filter((k) => k !== SHELL).map((k) => caches.delete(k))))
    .then(() => self.clients.claim()));
});
self.addEventListener("fetch", (e) => {
  const url = new URL(e.request.url);
  if (e.request.method !== "GET" || url.origin !== location.origin || url.pathname.startsWith("/api/")) return;
  // network first (fresh code after a deploy), cache as the offline fallback
  e.respondWith(fetch(e.request).then((r) => {
    if (r.ok) { const copy = r.clone(); caches.open(SHELL).then((c) => c.put(e.request, copy)); }
    return r;
  }).catch(() => caches.match(e.request).then((m) => m || caches.match("/"))));
});
