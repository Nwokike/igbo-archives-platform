const CACHE_VERSION = 'v1.1.0'; // Increment this version number for any cache changes
const STATIC_CACHE_NAME = 'static-cache-' + CACHE_VERSION;
const DYNAMIC_CACHE_NAME = 'dynamic-cache-' + CACHE_VERSION;

// A list of static assets we want to cache on install
// This should be kept minimal and typically managed by a build process
const staticAssets = [
    '/',
    '/static/css/style.css',
    '/static/js/main.js',
    '/static/images/logos/logo-dark.png',
    '/static/images/logos/logo-light.png',
    // Add other critical static assets here
];

self.addEventListener('install', event => {
    console.log('[Service Worker] Installing Service Worker ...', CACHE_VERSION);
    event.waitUntil(
        caches.open(STATIC_CACHE_NAME)
            .then(cache => {
                console.log('[Service Worker] Precaching static assets');
                return cache.addAll(staticAssets.map(url => new Request(url, {credentials: 'omit'})));
            })
            .catch(error => {
                console.error('[Service Worker] Static precaching failed:', error);
            })
    );
    self.skipWaiting(); // Forces the waiting service worker to become the active service worker
});

self.addEventListener('activate', event => {
    console.log('[Service Worker] Activating Service Worker ....', CACHE_VERSION);
    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames.map(cacheName => {
                    if (cacheName.startsWith('static-cache-') && cacheName !== STATIC_CACHE_NAME) {
                        console.log('[Service Worker] Deleting old static cache:', cacheName);
                        return caches.delete(cacheName);
                    }
                    if (cacheName.startsWith('dynamic-cache-') && cacheName !== DYNAMIC_CACHE_NAME) {
                        console.log('[Service Worker] Deleting old dynamic cache:', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        })
    );
    return self.clients.claim(); // Immediately takes control of all pages under its scope
});

self.addEventListener('fetch', event => {
    // Only handle GET requests for caching strategy
    if (event.request.method !== 'GET') {
        return;
    }

    event.respondWith(
        caches.match(event.request).then(response => {
            // Cache hit - return response
            if (response) {
                return response;
            }

            // Not in cache - fetch from network, then add to dynamic cache
            return fetch(event.request.clone())
                .then(res => {
                    return caches.open(DYNAMIC_CACHE_NAME).then(cache => {
                        // Cache only successful responses (status 200)
                        if (res.status === 200) {
                            cache.put(event.request, res.clone());
                        }
                        return res;
                    });
                })
                .catch(err => {
                    // This catch handles network errors, not HTTP errors
                    console.error('[Service Worker] Fetch failed:', err);
                    // You might want to serve an offline page here
                    // For example: caches.match('/offline.html');
                    return new Response('<h1>Offline</h1>', {
                        headers: {'Content-Type': 'text/html'}
                    });
                });
        })
    );
});


// ===============================================
// PUSH NOTIFICATION HANDLING
// ===============================================

self.addEventListener('push', event => {
    const data = event.data ? event.data.json() : {};
    const title = data.head || 'Igbo Archives Notification';
    const options = {
        body: data.body || 'You have a new update from Igbo Archives.',
        icon: data.icon || '/static/images/icons/icon-72x72.png', // Default icon
        badge: '/static/images/icons/badge-72x72.png', // Badge icon (Android)
        vibrate: [200, 100, 200],
        data: {
            url: data.url || '/' // URL to open when notification is clicked
        },
        actions: [
            // Example action buttons
            // {action: 'explore', title: 'Explore', icon: '/static/images/icons/icon-72x72.png'},
            // {action: 'close', title: 'Close', icon: '/static/images/icons/icon-72x72.png'},
        
    };

    event.waitUntil(
        self.registration.showNotification(title, options)
    );
});

self.addEventListener('notificationclick', event => {
    console.log('[Service Worker] Notification click received.', event.notification.data);
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
            // If no window is open, or no matching window found, open a new one
            if (clients.openWindow) {
                return clients.openWindow(targetUrl);
            }
            return null;
        })
    );
});