/* Service worker do Cora — shell offline + cache de estáticos. */
const CACHE = "cora-v1";
const ASSETS = [
  "/static/app.css",
  "/static/icon-192.png",
  "/static/icon-512.png",
  "/static/offline.html",
  "/static/manifest.webmanifest",
];

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(ASSETS)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (e) => {
  const req = e.request;
  if (req.method !== "GET") return;

  // Navegações: rede primeiro, com a página offline como reserva.
  if (req.mode === "navigate") {
    e.respondWith(fetch(req).catch(() => caches.match("/static/offline.html")));
    return;
  }

  // Estáticos: cache primeiro; popula o cache ao buscar novos de /static/.
  e.respondWith(
    caches.match(req).then((hit) =>
      hit ||
      fetch(req).then((res) => {
        if (res.ok && new URL(req.url).pathname.startsWith("/static/")) {
          const copy = res.clone();
          caches.open(CACHE).then((c) => c.put(req, copy));
        }
        return res;
      }).catch(() => hit)
    )
  );
});
