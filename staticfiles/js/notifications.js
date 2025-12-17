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

function markNotificationRead(notificationId) {
    var csrfToken = getCSRFToken();
    
    fetch('/profile/notifications/' + notificationId + '/mark-read/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrfToken,
            'Content-Type': 'application/json'
        }
    })
    .then(function(response) { return response.json(); })
    .then(function(data) {
        if (data.status === 'success') {
            updateNotificationCount();
        }
    })
    .catch(function(error) {
        console.error('Failed to mark notification as read:', error);
    });
}

function markAsRead(notificationId) {
    var csrfToken = getCSRFToken();
    
    fetch('/profile/notifications/' + notificationId + '/mark-read/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrfToken,
            'Content-Type': 'application/json'
        }
    })
    .then(function(response) { return response.json(); })
    .then(function(data) {
        if (data.status === 'success') {
            var item = document.getElementById('notification-' + notificationId);
            if (item) {
                item.classList.remove('border-l-4', 'border-l-vintage-gold', 'bg-heritage-cream/50');
                var button = item.querySelector('button');
                if (button) button.remove();
            }
        }
    })
    .catch(function(error) {
        console.error('Failed to mark notification as read:', error);
    });
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
    .then(function(response) { return response.json(); })
    .then(function(data) {
        if (data.status === 'success') {
            location.reload();
        }
    })
    .catch(function(error) {
        console.error('Failed to mark all notifications as read:', error);
    });
}

function updateNotificationCount() {
    location.reload();
}
