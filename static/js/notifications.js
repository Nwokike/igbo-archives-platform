function getCSRFToken() {
    var csrfInput = document.querySelector('[name=csrfmiddlewaretoken]');
    if (csrfInput) return csrfInput.value;

    var csrfMeta = document.querySelector('meta[name="csrf-token"]');
    if (csrfMeta) return csrfMeta.getAttribute('content');

    var cookies = document.cookie.split(';');
    for (var i = 0; i < cookies.length; i++) {
        var cookie = cookies[i].trim();
        if (cookie.startsWith('csrftoken=')) {
            return cookie.substring('csrftoken='.length);
        }
    }
    return '';
}

function updateNotificationCount() {
    const badge = document.getElementById('notificationBadge');
    if (badge) {
        let count = parseInt(badge.textContent) || 0;
        if (count > 0) {
            count--;
            badge.textContent = count;
            if (count === 0) {
                badge.style.display = 'none';
            }
        }
    }
}

function markNotificationRead(notificationId) {
    var csrfToken = getCSRFToken();

    fetch('/profile/notifications/' + notificationId + '/mark-read/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrfToken,
            'Content-Type': 'application/json'
        }
    })
        .then(function (response) { return response.json(); })
        .then(function (data) {
            if (data.status === 'success') {
                // Remove the visual indicator of unread state
                var item = document.getElementById('notification-' + notificationId);
                if (item) {
                    item.classList.remove('unread', 'bg-heritage-cream/50', 'border-l-4', 'border-l-vintage-gold'); // Adjust based on actual classes
                    // Also remove the mark-read button if it exists
                    var button = item.querySelector('.mark-read-btn');
                    if (button) button.remove();
                }
                updateNotificationCount();
            }
        })
        .catch(function (error) {
            console.error('Failed to mark notification as read:', error);
        });
}

function markAsRead(notificationId) {
    // Alias for compatibility if used elsewhere
    markNotificationRead(notificationId);
}

function markAllRead() {
    var csrfToken = getCSRFToken();

    fetch('/profile/notifications/mark-all-read/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrfToken,
            'Content-Type': 'application/json'
        }
    })
        .then(function (response) { return response.json(); })
        .then(function (data) {
            if (data.status === 'success') {
                // Update UI for all items
                document.querySelectorAll('.notification-item.unread').forEach(item => {
                    item.classList.remove('unread', 'bg-heritage-cream/50', 'border-l-4', 'border-l-vintage-gold');
                });
                document.querySelectorAll('.mark-read-btn').forEach(btn => btn.remove());

                const badge = document.getElementById('notificationBadge');
                if (badge) badge.style.display = 'none';

                if (window.showToast) window.showToast('All notifications marked as read');
            }
        })
        .catch(function (error) {
            console.error('Failed to mark all notifications as read:', error);
        });
}
