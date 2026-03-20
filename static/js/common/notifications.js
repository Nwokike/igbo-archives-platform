/**
 * Notification handlers for Igbo Archives.
 *
 * Reads URL patterns from data-attributes on #notificationsList container
 * (set by Django template tags) so no URLs are hardcoded in JS.
 *
 * Depends on: utils.js (getCookie)
 */

(function () {
    'use strict';

    // ── Helpers ────────────────────────────────────────────────

    /**
     * Get the notifications list container and its URL configuration.
     * Returns null if the container isn't on the page.
     */
    function getConfig() {
        var container = document.getElementById('notificationsList');
        if (!container) return null;
        return {
            container: container,
            markReadUrl: container.dataset.markReadUrl || '',
            markAllReadUrl: container.dataset.markAllReadUrl || ''
        };
    }

    /**
     * Decrement the notification badge count.
     * Hides the badge when count reaches 0.
     */
    function updateBadgeCount() {
        var badge = document.getElementById('notificationBadge');
        if (!badge) return;

        var count = parseInt(badge.textContent, 10) || 0;
        if (count > 0) {
            count--;
            badge.textContent = count;
            if (count === 0) {
                badge.style.display = 'none';
            }
        }
    }

    /**
     * Remove unread visual styling from a notification element.
     */
    function clearUnreadStyle(el) {
        if (!el) return;
        el.classList.remove(
            'bg-accent/5',
            'border-l-4',
            'border-l-accent'
        );
    }

    // ── API Actions ────────────────────────────────────────────

    /**
     * Mark a single notification as read.
     * @param {string|number} notificationId
     */
    function markNotificationRead(notificationId) {
        var config = getConfig();
        if (!config || !config.markReadUrl) {
            console.warn('Notification: mark-read URL not configured');
            return;
        }

        // Replace the placeholder ID (0) in the URL with the actual ID
        var url = config.markReadUrl.replace('/0/', '/' + notificationId + '/');

        fetch(url, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'Content-Type': 'application/json'
            }
        })
            .then(function (response) { return response.json(); })
            .then(function (data) {
                if (data.status === 'success') {
                    var item = document.getElementById('notification-' + notificationId);
                    clearUnreadStyle(item);

                    // Remove the "Mark read" button
                    var btn = item ? item.querySelector('.mark-read-btn') : null;
                    if (btn) btn.remove();

                    updateBadgeCount();
                }
            })
            .catch(function (error) {
                console.error('Failed to mark notification as read:', error);
            });
    }

    /**
     * Mark all notifications as read.
     */
    function markAllRead() {
        var config = getConfig();
        if (!config || !config.markAllReadUrl) {
            console.warn('Notification: mark-all-read URL not configured');
            return;
        }

        fetch(config.markAllReadUrl, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
        })
            .then(function (response) { return response.json(); })
            .then(function (data) {
                if (data.status === 'success') {
                    // Clear unread styles from all items
                    config.container.querySelectorAll('[id^="notification-"]').forEach(function (item) {
                        clearUnreadStyle(item);
                    });

                    // Remove all "Mark read" buttons
                    config.container.querySelectorAll('.mark-read-btn').forEach(function (btn) {
                        btn.remove();
                    });

                    // Hide the badge entirely
                    var badge = document.getElementById('notificationBadge');
                    if (badge) badge.style.display = 'none';

                    if (window.showToast) {
                        window.showToast('All notifications marked as read');
                    }
                }
            })
            .catch(function (error) {
                console.error('Failed to mark all notifications as read:', error);
            });
    }

    // ── Event Delegation ──────────────────────────────────────

    /**
     * Single delegated listener on the notifications container.
     * Handles data-action="mark-read" and data-action="mark-all-read"
     * buttons rendered by the Django template.
     */
    function initEventDelegation() {
        var config = getConfig();

        // Container-level delegation (for #notificationsList)
        if (config) {
            config.container.addEventListener('click', function (e) {
                var markReadBtn = e.target.closest('[data-action="mark-read"]');
                if (markReadBtn) {
                    e.preventDefault();
                    e.stopPropagation();
                    var notificationId = markReadBtn.dataset.notificationId;
                    if (notificationId) {
                        markNotificationRead(notificationId);
                    }
                    return;
                }

                var markAllBtn = e.target.closest('[data-action="mark-all-read"]');
                if (markAllBtn) {
                    e.preventDefault();
                    markAllRead();
                    return;
                }
            });
        }

        // Document-level delegation for buttons outside the container
        document.addEventListener('click', function (e) {
            var markAllBtn = e.target.closest('[data-action="mark-all-read"]');
            if (markAllBtn) {
                e.preventDefault();
                markAllRead();
                return;
            }
        });
    }

    // ── Initialise ────────────────────────────────────────────

    // Wait for DOM before attaching listeners
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initEventDelegation);
    } else {
        initEventDelegation();
    }

    // Re-init when HTMX swaps dropdown content
    document.addEventListener('htmx:afterSwap', function (e) {
        if (e.detail.target && e.detail.target.id === 'notificationDropdown') {
            initEventDelegation();
        }
    });

    // Expose for any external callers that may need them
    window.markNotificationRead = markNotificationRead;
    window.markAllRead = markAllRead;
})();
