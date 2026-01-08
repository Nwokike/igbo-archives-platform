/**
 * Donation Page Logic
 * Handles custom amount inputs and Paystack integration.
 */
document.addEventListener('DOMContentLoaded', () => {
    const customInput = document.getElementById('customAmount');
    const donateBtn = document.getElementById('donateBtn');

    if (!donateBtn || !customInput) return;

    // Get config from global context or data attributes (assuming templated values are available globally or we parse them)
    // For now, we'll try to get the key from the script tag data or a global variable if set.
    // Ideally, pass these via data-attributes on a container.
    const container = document.querySelector('.card-body');
    // Wait, the template uses {{ paystack_public_key }} inside the inline script.
    // We should look for a data attribute. I will add data attributes to the donate button in the next step.

    donateBtn.addEventListener('click', function () {
        const amount = parseInt(customInput.value) || 0;
        const publicKey = this.dataset.key;
        const userEmail = this.dataset.email;

        if (amount < 100) {
            if (window.showToast) {
                window.showToast('Minimum donation amount is ₦100', 'warning');
            } else {
                alert('Minimum donation amount is ₦100');
            }
            return;
        }

        if (typeof PaystackPop === 'undefined') {
            console.error('Paystack SDK not loaded');
            if (window.showToast) window.showToast('Payment system not loaded. Please refresh.', 'error');
            return;
        }

        const handler = PaystackPop.setup({
            key: publicKey,
            email: userEmail,
            amount: amount * 100, // Paystack uses kobo
            currency: 'NGN',
            ref: 'IA-' + Math.floor(Math.random() * 1000000000 + 1),
            metadata: {
                custom_fields: [
                    { display_name: "Donation Type", variable_name: "donation_type", value: "One-time" }
                ]
            },
            callback: function (response) {
                if (window.showToast) {
                    window.showToast('Thank you for your generous donation!', 'success');
                } else {
                    alert('Thank you for your generous donation! Reference: ' + response.reference);
                }
                setTimeout(() => window.location.reload(), 2000);
            },
            onClose: function () {
                if (window.showToast) window.showToast('Payment cancelled', 'info');
            }
        });
        handler.openIframe();
    });
});
