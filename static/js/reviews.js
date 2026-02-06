/**
 * Interactive Review Functions
 * Handles editing, toggling visibility, and Turnstile resetting.
 */

function showReviewForm() {
    // 1. Hide the Summary Card
    const summaryCard = document.getElementById('userReviewSummary');
    if (summaryCard) {
        summaryCard.classList.add('hidden');
    }

    // 2. Show the Form Card
    const formCard = document.getElementById('reviewFormContainer');
    if (formCard) {
        formCard.classList.remove('hidden');
    }
}

function cancelEdit() {
    // Reverse of showReviewForm (optional, if you want a cancel button)
    const summaryCard = document.getElementById('userReviewSummary');
    const formCard = document.getElementById('reviewFormContainer');
    
    if (summaryCard && formCard) {
        summaryCard.classList.remove('hidden');
        formCard.classList.add('hidden');
    }
}

function editReview(rating, text) {
    // 1. Ensure the form is visible (in case it's hidden behind the summary)
    showReviewForm();

    // 2. Scroll sidebar to the form
    const formContainer = document.getElementById('reviewFormContainer');
    if (formContainer) {
        formContainer.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }

    // 3. Populate the Text Area
    const textArea = document.querySelector('textarea[name="review_text"]');
    if (textArea) {
        textArea.value = text;
        textArea.focus();
    }

    // 4. Select the correct Star
    const starInput = document.getElementById(`star${rating}`);
    if (starInput) {
        starInput.checked = true;
    }

    // 5. Update Button Text
    const submitBtn = document.getElementById('reviewSubmitBtn');
    if (submitBtn) {
        submitBtn.textContent = 'Update Review';
    }
}

/**
 * Re-initialize Turnstile after HTMX swaps.
 */
document.body.addEventListener('htmx:afterSwap', function(event) {
    if (event.target.id === 'reviews-sidebar-container') {
        if (typeof turnstile !== 'undefined') {
            turnstile.render('.cf-turnstile');
        }
    }
});