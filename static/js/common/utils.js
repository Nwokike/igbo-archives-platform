/**
 * Shared utility functions for Igbo Archives.
 * Consolidates common helpers used across multiple JS files.
 */

/**
 * Get a cookie value by name.
 * @param {string} name - Cookie name to retrieve
 * @returns {string|null} Cookie value or null
 */
function getCookie(name) {
    // 1. Hidden input (most reliable in Django templates)
    var csrfInput = document.querySelector('[name=csrfmiddlewaretoken]');
    if (name === 'csrftoken' && csrfInput) return csrfInput.value;

    // 2. Meta tag
    if (name === 'csrftoken') {
        var csrfMeta = document.querySelector('meta[name="csrf-token"]');
        if (csrfMeta) return csrfMeta.getAttribute('content');
    }

    // 3. Cookie
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

/**
 * Escape HTML entities to prevent XSS.
 * @param {string} str - Raw string to escape
 * @returns {string} Escaped string safe for HTML insertion
 */
function escapeHtml(str) {
    if (!str) return '';
    var div = document.createElement('div');
    div.appendChild(document.createTextNode(str));
    return div.innerHTML;
}

/**
 * Validate that a URL is safe (http/https or relative path).
 * Blocks javascript:, data:, vbscript: and other dangerous protocols.
 * @param {string} url - URL to validate
 * @returns {boolean} True if URL is safe
 */
function isSafeUrl(url) {
    if (!url || typeof url !== 'string') return false;
    var trimmed = url.trim().toLowerCase();
    if (trimmed.startsWith('http://') || trimmed.startsWith('https://') || trimmed.startsWith('/')) {
        return true;
    }
    return false;
}

// Make available globally
window.getCookie = getCookie;
window.escapeHtml = escapeHtml;
window.isSafeUrl = isSafeUrl;
