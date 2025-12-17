function shareProfile() {
    var title = document.querySelector('[data-share-title]');
    var shareTitle = title ? title.getAttribute('data-share-title') : document.title;
    
    if (navigator.share) {
        navigator.share({
            title: shareTitle,
            url: window.location.href
        }).catch(function(err) {
            console.log('Share cancelled or failed:', err);
        });
    } else {
        navigator.clipboard.writeText(window.location.href).then(function() {
            showToast('Link copied to clipboard!');
        }).catch(function() {
            prompt('Copy this link:', window.location.href);
        });
    }
}

function showToast(message) {
    var toast = document.createElement('div');
    toast.className = 'fixed bottom-6 left-1/2 -translate-x-1/2 bg-dark-brown text-white px-4 py-2 rounded-lg shadow-lg z-50 animate-fade-in-up';
    toast.textContent = message;
    document.body.appendChild(toast);
    
    setTimeout(function() {
        toast.style.opacity = '0';
        toast.style.transition = 'opacity 0.3s';
        setTimeout(function() { toast.remove(); }, 300);
    }, 2000);
}
