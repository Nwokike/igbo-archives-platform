/**
 * Igbo Archives Service Worker
 * Handles caching, offline support, and push notifications
 */

const CACHE_VERSION = 'static';
const STATIC_CACHE_NAME = 'static-cache-' + CACHE_VERSION;
const DYNAMIC_CACHE_NAME = 'dynamic-cache-' + CACHE_VERSION;
const MAX_DYNAMIC_CACHE_ITEMS = 50;

// Only cache static assets - NO HTML pages
const staticAssets = [
    '/offline/',
    '/static/css/tailwind.output.css',
    '/static/css/style.css',
    '/static/js/common/main.js',
    '/static/images/logos/logo-dark.png',
    '/static/images/logos/logo-light.png',
];

const EXCLUDE_FROM_CACHE = [
    '/api/',
    '/admin/',
    '/accounts/',
    '/webpush/',
    'htmx',
    'csrftoken',
];

function shouldCache(url) {
    // Only cache static assets - never HTML pages
    const isStatic = url.includes('/static/') ||
        url.includes('.css') ||
        url.includes('.js') ||
        url.includes('.png') ||
        url.includes('.jpg') ||
        url.includes('.woff') ||
        url.includes('.woff2');
    if (!isStatic) return false;
    return !EXCLUDE_FROM_CACHE.some(pattern => url.includes(pattern));
}

async function limitCacheSize(cacheName, maxItems) {
    const cache = await caches.open(cacheName);
    let keys = await cache.keys();
    while (keys.length > maxItems) {
        await cache.delete(keys[0]);
        keys = await cache.keys();
    }
}

self.addEventListener('install', event => {
    console.log('[Service Worker] Installing...', CACHE_VERSION);
    event.waitUntil(
        caches.open(STATIC_CACHE_NAME)
            .then(cache => {
                console.log('[Service Worker] Precaching static assets');
                return cache.addAll(staticAssets.map(url => new Request(url, { credentials: 'omit' })));
            })
            .catch(error => {
                console.error('[Service Worker] Static precaching failed:', error);
            })
    );
    self.skipWaiting();
});

self.addEventListener('activate', event => {
    console.log('[Service Worker] Activating...', CACHE_VERSION);
    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames.map(cacheName => {
                    if (cacheName.startsWith('static-cache-') && cacheName !== STATIC_CACHE_NAME) {
                        console.log('[Service Worker] Deleting old cache:', cacheName);
                        return caches.delete(cacheName);
                    }
                    if (cacheName.startsWith('dynamic-cache-') && cacheName !== DYNAMIC_CACHE_NAME) {
                        console.log('[Service Worker] Deleting old cache:', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        })
    );
    return self.clients.claim();
});

self.addEventListener('fetch', event => {
    if (event.request.method !== 'GET') {
        return;
    }

    const url = event.request.url;
    const requestUrl = new URL(url);

    // Skip service worker for external resources - let browser handle them directly
    if (requestUrl.origin !== self.location.origin) {
        return;
    }

    event.respondWith(
        caches.match(event.request).then(response => {
            if (response) {
                return response;
            }

            return fetch(event.request)
                .then(res => {
                    // Only cache successful responses from same origin
                    if (res.status === 200 && shouldCache(url) && res.type === 'basic') {
                        const responseToCache = res.clone();
                        caches.open(DYNAMIC_CACHE_NAME).then(cache => {
                            cache.put(event.request, responseToCache);
                            limitCacheSize(DYNAMIC_CACHE_NAME, MAX_DYNAMIC_CACHE_ITEMS);
                        });
                    }
                    return res;
                })
                .catch(err => {
                    console.error('[Service Worker] Fetch failed:', err);
                    if (event.request.mode === 'navigate') {
                        return caches.match('/offline/');
                    }
                    return new Response('', { status: 408, statusText: 'Request Timeout' });
                });
        })
    );
});

self.addEventListener('push', event => {
    const data = event.data ? event.data.json() : {};
    const title = data.head || 'Igbo Archives';
    const options = {
        body: data.body || 'You have a new update from Igbo Archives.',
        icon: data.icon || '/static/images/logos/logo-light.png',
        badge: '/static/images/logos/logo-light.png',
        vibrate: [200, 100, 200],
        data: {
            url: data.url || '/'
        },
        actions: []
    };

    event.waitUntil(
        self.registration.showNotification(title, options)
    );
});

self.addEventListener('notificationclick', event => {
    console.log('[Service Worker] Notification clicked');
    event.notification.close();

    const targetUrl = event.notification.data.url;

    event.waitUntil(
        clients.matchAll({ type: 'window', includeUncontrolled: true }).then(clientList => {
            for (let i = 0; i < clientList.length; i++) {
                const client = clientList[i];
                if (client.url === targetUrl && 'focus' in client) {
                    return client.focus();
                }
            }
            if (clients.openWindow) {
                return clients.openWindow(targetUrl);
            }
            return null;
        })
    );
});