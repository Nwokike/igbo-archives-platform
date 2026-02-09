/**
 * PWA Install Button Handler
 * Shows a persistent install button when the app is installable
 */

(function () {
    'use strict';

    let deferredPrompt = null;
    const installBtn = document.getElementById('pwaInstallBtn');

    if (!installBtn) return;

    // Listen for the beforeinstallprompt event
    window.addEventListener('beforeinstallprompt', function (e) {
        console.log('beforeinstallprompt event fired');
        // Prevent Chrome 67+ from automatically showing the prompt
        e.preventDefault();
        // Stash the event so it can be triggered later
        deferredPrompt = e;
        // Show the install button
        if (installBtn) {
            console.log('Showing PWA install button');
            installBtn.style.display = 'flex';
            installBtn.classList.remove('hidden');
        }
    });

    // Handle install button click
    if (installBtn) {
        installBtn.addEventListener('click', async function () {
            if (!deferredPrompt) {
                console.log('Install prompt not available');
                return;
            }

            // Show the install prompt
            deferredPrompt.prompt();

            // Wait for the user to respond to the prompt
            const { outcome } = await deferredPrompt.userChoice;
            console.log('User choice:', outcome);

            // Clear the deferredPrompt variable
            deferredPrompt = null;

            // Hide the install button
            installBtn.style.display = 'none';
            installBtn.classList.add('hidden');
        });
    }

    // Hide button if app is already installed
    window.addEventListener('appinstalled', function () {
        console.log('PWA was installed');
        deferredPrompt = null;
        if (installBtn) {
            installBtn.style.display = 'none';
            installBtn.classList.add('hidden');
        }
    });

    // Initial check in case event fired before script load
    if (window.deferredPrompt && installBtn) {
        deferredPrompt = window.deferredPrompt;
        installBtn.style.display = 'flex';
        installBtn.classList.remove('hidden');
    }

    // For iOS - check if running as standalone
    if (window.matchMedia('(display-mode: standalone)').matches) {
        installBtn.classList.add('hidden');
    }

    // Also check for iOS Safari
    if (window.navigator.standalone === true) {
        installBtn.classList.add('hidden');
    }
})();
