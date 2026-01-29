document.addEventListener('DOMContentLoaded', function () {
    var tabButtons = document.querySelectorAll('.tab[data-tab], .tab-button[data-tab]');

    tabButtons.forEach(function (button) {
        button.addEventListener('click', function () {
            var targetId = this.getAttribute('data-tab');
            var container = this.closest('.tab-container') || document.body;

            // Find the nearest parent that contains both tabs and panels
            var parentContainer = container.closest('[class*="tab"]') || container.parentElement || document.body;

            // Find tab-content sibling or search in document
            var tabContent = container.nextElementSibling;
            if (!tabContent || !tabContent.classList.contains('tab-content')) {
                // Try to find tab-content anywhere in the same parent
                tabContent = parentContainer.querySelector('.tab-content') || document;
            }

            // Remove active from all tab buttons in the container
            container.querySelectorAll('.tab[data-tab], .tab-button[data-tab]').forEach(function (btn) {
                btn.classList.remove('active');
            });
            this.classList.add('active');

            // Hide all tab panels - search in both tab-content and document
            var panels = tabContent.querySelectorAll ? tabContent.querySelectorAll('.tab-panel') : document.querySelectorAll('.tab-panel');
            panels.forEach(function (panel) {
                panel.classList.add('hidden');
                panel.classList.remove('active', 'block');
            });

            // Show target panel
            var targetPanel = document.getElementById(targetId);
            if (targetPanel) {
                targetPanel.classList.remove('hidden');
                targetPanel.classList.add('active', 'block');
            }

            // Update URL
            var url = new URL(window.location);
            url.searchParams.set('tab', targetId);
            history.replaceState(null, '', url);
        });
    });

    // Handle URL param on load
    var urlParams = new URLSearchParams(window.location.search);
    var tabParam = urlParams.get('tab');
    if (tabParam) {
        var targetButton = document.querySelector('.tab[data-tab="' + tabParam + '"], .tab-button[data-tab="' + tabParam + '"]');
        if (targetButton) {
            targetButton.click();
        }
    }
});
