/* JARVIS Service Worker — macht JARVIS auf dem Handy installierbar.
   Strategie: Netzwerk zuerst (Daten sind live), statische Dateien aus dem
   Cache als Fallback, damit die App-Hülle auch bei kurzem Aussetzer lädt.
   Bewusst KEIN Cachen von /api/* — die Dashboard-Daten müssen immer frisch sein. */
const CACHE = 'jarvis-v1';
const SHELL = ['/', '/static/style.css', '/static/icons/jarvis-192.png'];

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(SHELL)).catch(() => {}));
  self.skipWaiting();
});

self.addEventListener('activate', (e) => {
  e.waitUntil(caches.keys().then((keys) =>
    Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))));
  self.clients.claim();
});

self.addEventListener('fetch', (e) => {
  const url = new URL(e.request.url);
  if (e.request.method !== 'GET' || url.pathname.startsWith('/api/')) return; // live
  e.respondWith(
    fetch(e.request)
      .then((res) => {
        if (res && res.ok && url.origin === self.location.origin) {
          const copy = res.clone();
          caches.open(CACHE).then((c) => c.put(e.request, copy)).catch(() => {});
        }
        return res;
      })
      .catch(() => caches.match(e.request).then((m) => m || caches.match('/')))
  );
});
