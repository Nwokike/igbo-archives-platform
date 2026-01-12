document.addEventListener('DOMContentLoaded', function () {
    var tabButtons = document.querySelectorAll('.tab[data-tab], .tab-button[data-tab]');

    tabButtons.forEach(function (button) {
        button.addEventListener('click', function () {
            var targetId = this.getAttribute('data-tab');
            var container = this.closest('.tab-container') || document.body;

            container.querySelectorAll('.tab[data-tab], .tab-button[data-tab]').forEach(function (btn) {
                btn.classList.remove('active');
            });
            this.classList.add('active');

            container.querySelectorAll('.tab-panel').forEach(function (panel) {
                panel.classList.add('hidden');
                panel.classList.remove('active');
            });

            var targetPanel = document.getElementById(targetId);
            if (targetPanel) {
                targetPanel.classList.remove('hidden');
                targetPanel.classList.add('active');
            }

            var url = new URL(window.location);
            url.searchParams.set('tab', targetId);
            history.replaceState(null, '', url);
        });
    });

    var urlParams = new URLSearchParams(window.location.search);
    var tabParam = urlParams.get('tab');
    if (tabParam) {
        var targetButton = document.querySelector('.tab-button[data-tab="' + tabParam + '"]');
        if (targetButton) {
            targetButton.click();
        }
    }
});
