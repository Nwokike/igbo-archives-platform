/**
 * Google Analytics Configuration
 * Initializes the dataLayer and configures GA with the provided ID.
 */
(function () {
    window.dataLayer = window.dataLayer || [];
    function gtag() { dataLayer.push(arguments); }
    gtag('js', new Date());

    // Get the ID from the data attribute of the currently executing script
    const script = document.currentScript;
    const gaId = script ? script.getAttribute('data-ga-id') : null;

    if (gaId) {
        gtag('config', gaId);
    } else {
        console.warn('Google Analytics ID not found in data-ga-id attribute');
    }
})();
