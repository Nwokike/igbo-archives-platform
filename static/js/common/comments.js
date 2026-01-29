document.addEventListener('DOMContentLoaded', function () {
    const commentForm = document.querySelector('.modern-comment-form');
    const commentReplyBtns = document.querySelectorAll('.comment-reply-btn');
    const parentInput = document.querySelector('input[name="parent"]');
    const commentTextarea = document.querySelector('textarea[name="comment"]');

    if (commentReplyBtns.length > 0 && parentInput) {
        commentReplyBtns.forEach(btn => {
            btn.addEventListener('click', function (e) {
                e.preventDefault();
                const commentId = this.dataset.commentId;
                const authorName = this.closest('.comment-item').querySelector('.author-link').textContent.trim();

                // Set parent ID
                parentInput.value = commentId;

                // Scroll to form
                const formSection = document.getElementById('comment-form-section');
                if (formSection) {
                    formSection.scrollIntoView({ behavior: 'smooth' });
                }

                // Focus textarea and add mention or placeholder
                if (commentTextarea) {
                    commentTextarea.focus();
                    commentTextarea.placeholder = `Replying to ${authorName}...`;

                    // Optional: Add some visual cue that we are replying
                    let replyIndicator = document.getElementById('reply-indicator');
                    if (!replyIndicator) {
                        replyIndicator = document.createElement('div');
                        replyIndicator.id = 'reply-indicator';
                        replyIndicator.className = 'reply-mode-tag mb-4 p-2 bg-heritage-cream/50 rounded-lg flex justify-between items-center text-sm font-medium text-dark-brown';
                        commentForm.prepend(replyIndicator);
                    }
                    replyIndicator.innerHTML = `
                        <span><i class="fas fa-reply mr-2"></i>Replying to <strong>${authorName}</strong></span>
                        <button type="button" class="text-vintage-beaver hover:text-red-500" id="cancel-reply">
                            <i class="fas fa-times"></i>
                        </button>
                    `;

                    document.getElementById('cancel-reply').addEventListener('click', function () {
                        parentInput.value = '';
                        replyIndicator.remove();
                        commentTextarea.placeholder = "Share your thoughts...";
                    });
                }
            });
        });
    }

    // Floating label logic (if not handled by CSS alone)
    // Actually our CSS handles it via :not(:placeholder-shown), but for textarea 
    // it's sometimes better to have a bit of JS to ensure it stays up if there's content 
    // (though :not(:placeholder-shown) should work if placeholder is a space or empty)
});
