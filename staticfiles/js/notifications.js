function markNotificationRead(notificationId) {
    var csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
    if (!csrfToken) {
        console.warn('CSRF token not found');
        return;
    }
    
    fetch('/profile/notifications/' + notificationId + '/mark-read/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrfToken.value,
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

function updateNotificationCount() {
    location.reload();
}
