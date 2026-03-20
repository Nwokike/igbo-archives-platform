/**
 * Donation Page Logic
 * Handles custom amount inputs, currency toggle, and Paystack integration.
 */
document.addEventListener('DOMContentLoaded', () => {
    const customInput = document.getElementById('customAmount');
    const donateBtn = document.getElementById('donateBtn');
    const amountLabel = document.getElementById('amountLabel');
    const currencyHint = document.getElementById('currencyHint');

    if (!donateBtn || !customInput) return;

    // Currency state
    let selectedCurrency = 'NGN';
    const currencyConfig = {
        NGN: { symbol: '₦', min: 100, label: 'Enter custom amount (₦)', multiplier: 100 },
        USD: { symbol: '$', min: 1, label: 'Enter custom amount ($)', multiplier: 100 }
    };

    // Currency toggle
    const toggleBtns = document.querySelectorAll('.currency-btn');
    toggleBtns.forEach(btn => {
        btn.addEventListener('click', function () {
            selectedCurrency = this.dataset.currency;
            const config = currencyConfig[selectedCurrency];

            // Update UI
            customInput.min = config.min;
            customInput.value = '';
            customInput.placeholder = 'Enter amount';
            if (amountLabel) amountLabel.textContent = config.label;

            // Toggle active styling
            toggleBtns.forEach(b => {
                b.classList.remove('bg-accent', 'text-white');
                b.classList.add('bg-surface-alt', 'text-text-muted');
            });
            this.classList.remove('bg-surface-alt', 'text-text-muted');
            this.classList.add('bg-accent', 'text-white');

            // Show/hide USD hint
            if (currencyHint) {
                currencyHint.style.display = selectedCurrency === 'USD' ? 'block' : 'none';
            }
        });
    });

    donateBtn.addEventListener('click', function () {
        const config = currencyConfig[selectedCurrency];
        const amount = parseInt(customInput.value) || 0;
        const publicKey = this.dataset.key;
        const userEmail = this.dataset.email;

        if (amount < config.min) {
            const msg = `Minimum donation amount is ${config.symbol}${config.min}`;
            if (window.showToast) {
                window.showToast(msg, 'warning');
            } else {
                alert(msg);
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
            amount: amount * config.multiplier,
            currency: selectedCurrency,
            ref: 'IA-' + Math.floor(Math.random() * 1000000000 + 1),
            metadata: {
                custom_fields: [
                    { display_name: "Donation Type", variable_name: "donation_type", value: "One-time" },
                    { display_name: "Currency", variable_name: "currency", value: selectedCurrency }
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
