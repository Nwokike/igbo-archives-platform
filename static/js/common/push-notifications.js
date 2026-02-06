(function () {
    'use strict';

    const scriptTag = document.getElementById('push-notifications-script');
    const subscribeUrl = scriptTag?.dataset.subscribeUrl;
    const unsubscribeUrl = scriptTag?.dataset.unsubscribeUrl;
    const vapidPublicKey = document.querySelector('meta[name="vapid-public-key"]')?.content;

    const PUSH_PROMPT_ID = 'push-notification-prompt';
    const PUSH_PROMPT_DISMISS_KEY = 'pushPromptDismissedAt';
    const DISMISS_PERIOD_MS = 30 * 24 * 60 * 60 * 1000;

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
            return false;
        }
        try {
            const response = await fetch(subscribeUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify(subscription.toJSON())
            });
            if (!response.ok) {
                console.error('Failed to send subscription to server:', await response.text());
                return false;
            }
            console.log('Push subscription sent to server successfully.');
            return true;
        } catch (error) {
            console.error('Error sending subscription to server:', error);
            return false;
        }
    }

    async function removeSubscriptionFromServer(subscription) {
        if (!unsubscribeUrl) {
            console.error('Unsubscribe URL is not defined. Cannot remove subscription.');
            return false;
        }
        try {
            const response = await fetch(unsubscribeUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify(subscription.toJSON())
            });
            if (!response.ok) {
                console.error('Failed to remove subscription from server:', await response.text());
                return false;
            }
            console.log('Push subscription removed from server successfully.');
            return true;
        } catch (error) {
            console.error('Error removing subscription from server:', error);
            return false;
        }
    }

    async function syncSubscription() {
        try {
            const registration = await navigator.serviceWorker.ready;
            let subscription = await registration.pushManager.getSubscription();

            if (!subscription) {
                subscription = await registration.pushManager.subscribe({
                    userVisibleOnly: true,
                    applicationServerKey: urlBase64ToUint8Array(vapidPublicKey)
                });
                await sendSubscriptionToServer(subscription);
            } else {
                await sendSubscriptionToServer(subscription);
            }
        } catch (error) {
            console.error('Error syncing push notification subscription:', error);
            try {
                localStorage.setItem(PUSH_PROMPT_DISMISS_KEY, Date.now());
            } catch (storageError) {
                console.warn('Could not save to localStorage (tracking prevention):', storageError);
            }
        }
    }

    async function unsubscribeFromPush() {
        try {
            const registration = await navigator.serviceWorker.ready;
            const subscription = await registration.pushManager.getSubscription();

            if (subscription) {
                await removeSubscriptionFromServer(subscription);
                await subscription.unsubscribe();
                console.log('Unsubscribed from push notifications.');
            }
        } catch (error) {
            console.error('Error unsubscribing from push notifications:', error);
        }
    }

    function showSoftPrompt() {
        const prompt = document.getElementById(PUSH_PROMPT_ID);
        if (prompt) {
            prompt.classList.remove('hidden');
            prompt.classList.add('flex');
            let timeoutId = setTimeout(() => {
                if (!prompt.matches(':hover')) {
                    hideSoftPrompt();
                }
            }, 10000);

            prompt.addEventListener('mouseenter', () => clearTimeout(timeoutId));
            prompt.addEventListener('mouseleave', () => {
                timeoutId = setTimeout(() => {
                    hideSoftPrompt();
                }, 3000);
            });
        }
    }

    function hideSoftPrompt() {
        const prompt = document.getElementById(PUSH_PROMPT_ID);
        if (prompt) {
            prompt.classList.add('hidden');
            prompt.classList.remove('flex');
        }
    }

    async function handleAcceptPush() {
        hideSoftPrompt();
        const permission = await Notification.requestPermission();
        if (permission === 'granted') {
            await syncSubscription();
        } else if (permission === 'denied') {
            console.warn('User explicitly denied notifications via browser prompt.');
            try {
                localStorage.setItem(PUSH_PROMPT_DISMISS_KEY, Infinity);
            } catch (storageError) {
                console.warn('Could not save to localStorage (tracking prevention):', storageError);
            }
        }
    }

    function handleDismissPush() {
        hideSoftPrompt();
        try {
            localStorage.setItem(PUSH_PROMPT_DISMISS_KEY, Date.now());
        } catch (storageError) {
            console.warn('Could not save to localStorage (tracking prevention):', storageError);
        }
    }

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

    navigator.serviceWorker.ready.then(() => {
        if (Notification.permission === 'granted') {
            syncSubscription();
        } else if (Notification.permission === 'default') {
            let dismissedAt = null;
            try {
                dismissedAt = localStorage.getItem(PUSH_PROMPT_DISMISS_KEY);
            } catch (storageError) {
                console.warn('Could not read from localStorage (tracking prevention):', storageError);
            }
            const now = Date.now();
            if (!dismissedAt || (now - dismissedAt > DISMISS_PERIOD_MS)) {
                showSoftPrompt();
            } else {
                console.log('Push notification soft prompt dismissed recently. Will not show yet.');
            }
        }
    }).catch(error => {
        console.error('Service Worker ready failed:', error);
    });

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

    window.pushNotifications = {
        subscribe: syncSubscription,
        unsubscribe: unsubscribeFromPush
    };

})();
