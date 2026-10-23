/* Alpha LPGas Driver Portal service worker.
   Cache-first for static/CDN assets, network-first for portal pages
   (falls back to cache when offline). POSTs always go to the network. */
const CACHE = 'lpgas-driver-v1';
const PRECACHE = [
    '/static/driver/icons/icon-192.png',
    '/static/driver/icons/icon-512.png',
];

self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE).then((cache) => cache.addAll(PRECACHE)).then(() => self.skipWaiting())
    );
});

self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys()
            .then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
            .then(() => self.clients.claim())
    );
});

self.addEventListener('fetch', (event) => {
    const req = event.request;
    if (req.method !== 'GET') return;

    const url = new URL(req.url);

    // Static assets and CDN libraries: cache-first
    if (url.pathname.startsWith('/static/') || url.hostname.includes('jsdelivr')) {
        event.respondWith(
            caches.match(req).then((hit) => hit || fetch(req).then((res) => {
                const copy = res.clone();
                caches.open(CACHE).then((cache) => cache.put(req, copy));
                return res;
            }))
        );
        return;
    }

    // Portal pages: network-first, fall back to cache when offline
    if (url.origin === location.origin) {
        event.respondWith(
            fetch(req).then((res) => {
                const copy = res.clone();
                caches.open(CACHE).then((cache) => cache.put(req, copy));
                return res;
            }).catch(() => caches.match(req))
        );
    }
});
