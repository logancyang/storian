// Offline support for the hosted storyboard. The page and the project data come from the
// network when it answers within a few seconds, otherwise from the cache; frames and contact
// sheets are cached as they're viewed. Video and audio stream from the network.
const BUILD = "dev";  // `storian publish` stamps each deploy so the new worker replaces the old
const SHELL = `storian-shell-${BUILD}`, MEDIA = "storian-media-v1";

self.addEventListener("install", e => {
  e.waitUntil(caches.open(SHELL).then(c => c.addAll(["/", "/api/project"])).then(() => self.skipWaiting()));
});
self.addEventListener("activate", e => {
  e.waitUntil(caches.keys()
    .then(ks => Promise.all(ks.filter(k => k.startsWith("storian-shell-") && k !== SHELL).map(k => caches.delete(k))))
    .then(() => self.clients.claim()));
});
self.addEventListener("fetch", e => {
  const r = e.request, u = new URL(r.url);
  if (r.method !== "GET") return;
  if (u.origin === location.origin) {
    if (r.mode === "navigate") return e.respondWith(networkFirst(r, "/"));
    if (u.pathname === "/api/project") return e.respondWith(networkFirst(r, "/api/project"));
    if (/^\/media\/(frames|sheets)\//.test(u.pathname)) return e.respondWith(cacheFirst(r));
    return;
  }
  if (/^fonts\.(googleapis|gstatic)\.com$/.test(u.hostname)) e.respondWith(cacheFirst(r));
});

async function networkFirst(r, key) {
  const c = await caches.open(SHELL);
  const net = fetch(r).then(res => { if (res.ok && !res.redirected) c.put(key, res.clone()); return res; });
  const slow = new Promise(ok => setTimeout(ok, 4000)).then(() => c.match(key));
  try {
    return (await Promise.race([net, slow])) || await net;
  } catch (err) {
    return (await c.match(key)) || Response.error();
  }
}
async function cacheFirst(r) {
  const c = await caches.open(MEDIA);
  const hit = await c.match(r);
  if (hit) return hit;
  const res = await fetch(r);
  if (res.ok || res.type === "opaque") c.put(r, res.clone());
  return res;
}
