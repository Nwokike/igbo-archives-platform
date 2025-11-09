(function() {
    'use strict';

    // This script will be loaded with 'defer', so it runs after the DOM is parsed.
    const scriptTag = document.getElementById('push-notifications-script');
    const subscribeUrl = scriptTag?.dataset.subscribeUrl;
    const unsubscribeUrl = scriptTag?.dataset.unsubscribeUrl;
    const vapidPublicKey = document.querySelector('meta[name="vapid-public-key"]')?.content;

    const PUSH_PROMPT_ID = 'push-notification-prompt';
    const PUSH_PROMPT_DISMISS_KEY = 'pushPromptDismissedAt';
    const DISMISS_PERIOD_MS = 30 * 24 * 60 * 60 * 1000; // 30 days in milliseconds

    if (!('serviceWorker' in navigator) || !('PushManager' in window) || !vapidPublicKey) {
        console.warn('Push notifications not fully supported or configured (missing SW, PushManager, or VAPID key).');
        return;
    }
    
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    
    function urlBase64ToUint8Array(base64String) {
        const padding = '='.repeat((4 - base64String.length % 4) % 4);
        const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
        const rawData = window.atob(base64);
        const outputArray = new Uint8Array(rawData.length);
        for (let i = 0; i < rawData.length; ++i) {
            outputArray[i] = rawData.charCodeAt(i);
        }
        return outputArray;
    }

    async function sendSubscriptionToServer(subscription) {
        if (!subscribeUrl) {
            console.error('Subscribe URL is not defined. Cannot send subscription.');
            return;
        }
        try {
            const response = await fetch(subscribeUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify(subscription)
            });
            if (!response.ok) {
                console.error('Failed to send subscription to server:', await response.text());
            } else {
                console.log('Push subscription sent to server successfully.');
            }
        } catch (error) {
            console.error('Error sending subscription to server:', error);
        }
    }

    async function syncSubscription() {
        try {
            const registration = await navigator.serviceWorker.ready;
            let subscription = await registration.pushManager.getSubscription();

            if (!subscription) {
                // If no subscription exists, try to create one.
                subscription = await registration.pushManager.subscribe({
                    userVisibleOnly: true,
                    applicationServerKey: urlBase64ToUint8Array(vapidPublicKey)
                });
                await sendSubscriptionToServer(subscription);
            } else {
                // If a subscription exists, ensure it's synced (e.g., if user switched browsers)
                await sendSubscriptionToServer(subscription);
            }
        } catch (error) {
            console.error('Error syncing push notification subscription:', error);
            // If subscription fails (e.g., user denied in browser settings),
            // ensure our soft prompt isn't shown again for a while.
            localStorage.setItem(PUSH_PROMPT_DISMISS_KEY, Date.now());
        }
    }
    
    function showSoftPrompt() {
        const prompt = document.getElementById(PUSH_PROMPT_ID);
        if (prompt) {
            prompt.classList.add('show');
            // Hide after a few seconds if no interaction, but keep it visible if user hovers
            let timeoutId = setTimeout(() => {
                if (!prompt.matches(':hover')) {
                    hideSoftPrompt();
                }
            }, 10000); // Hide after 10 seconds

            prompt.addEventListener('mouseenter', () => clearTimeout(timeoutId));
            prompt.addEventListener('mouseleave', () => {
                timeoutId = setTimeout(() => {
                    hideSoftPrompt();
                }, 3000); // Hide 3 seconds after mouse leaves
            });
        }
    }

    function hideSoftPrompt() {
        const prompt = document.getElementById(PUSH_PROMPT_ID);
        if (prompt) {
            prompt.classList.remove('show');
            // Remove from DOM after transition for accessibility/performance
            setTimeout(() => {
                prompt.style.display = 'none';
            }, 500); // Match CSS transition duration
        }
    }

    // Handle user accepting notifications from soft prompt
    async function handleAcceptPush() {
        hideSoftPrompt();
        const permission = await Notification.requestPermission();
        if (permission === 'granted') {
            await syncSubscription();
        } else if (permission === 'denied') {
            console.warn('User explicitly denied notifications via browser prompt.');
            // User denied the hard prompt, respect this permanently by browser
            // Our soft prompt should not reappear for a long time or ever again
            localStorage.setItem(PUSH_PROMPT_DISMISS_KEY, Infinity); 
        }
    }

    // Handle user dismissing soft prompt
    function handleDismissPush() {
        hideSoftPrompt();
        localStorage.setItem(PUSH_PROMPT_DISMISS_KEY, Date.now());
    }

    // Add event listeners to soft prompt buttons
    document.addEventListener('DOMContentLoaded', () => {
        const acceptBtn = document.getElementById('push-prompt-accept');
        const dismissBtn = document.getElementById('push-prompt-dismiss');
        if (acceptBtn) {
            acceptBtn.addEventListener('click', handleAcceptPush);
        }
        if (dismissBtn) {
            dismissBtn.addEventListener('click', handleDismissPush);
        }
    });

    // Main logic: Service Worker Registration and Push Permission Check
    navigator.serviceWorker.ready.then(() => {
        if (Notification.permission === 'granted') {
            // If already granted, ensure subscription is synced
            syncSubscription();
        } else if (Notification.permission === 'default') {
            // Permission hasn't been requested or was dismissed (not blocked)
            const dismissedAt = localStorage.getItem(PUSH_PROMPT_DISMISS_KEY);
            const now = Date.now();
            if (!dismissedAt || (now - dismissedAt > DISMISS_PERIOD_MS)) {
                // Show soft prompt if never dismissed or dismiss period has passed
                showSoftPrompt();
            } else {
                console.log('Push notification soft prompt dismissed recently. Will not show yet.');
            }
        }
        // If 'denied', we do nothing, respecting the user's explicit block.
    }).catch(error => {
        console.error('Service Worker ready failed:', error);
    });

    // Service Worker Registration (should happen early)
    if ('serviceWorker' in navigator) {
        window.addEventListener('load', () => {
            navigator.serviceWorker.register('/serviceworker.js')
                .then(registration => {
                    console.log('ServiceWorker registered successfully.');
                })
                .catch(err => {
                    console.error('ServiceWorker registration failed:', err);
                });
        });
    }

})();