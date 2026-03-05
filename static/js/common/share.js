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



document.addEventListener('DOMContentLoaded', function() {
    var shareBtn = document.getElementById('share-btn');
    if (shareBtn) {
        shareBtn.addEventListener('click', shareProfile);
    }
});