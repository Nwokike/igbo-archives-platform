/**
 * API & MCP Dashboard Functionality
 * Handles tab switching, language switching for code examples, and clipboard operations.
 */

document.addEventListener('DOMContentLoaded', function () {
    // Tab switching logic to match main dashboard
    const tabs = document.querySelectorAll('.tab');
    const panels = document.querySelectorAll('.tab-panel');

    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const targetId = tab.getAttribute('data-tab');

            // Remove active classes
            tabs.forEach(t => t.classList.remove('active'));
            panels.forEach(p => p.classList.add('hidden'));
            panels.forEach(p => p.classList.remove('block'));

            // Add active classes
            tab.classList.add('active');
            const targetPanel = document.getElementById(targetId);
            if (targetPanel) {
                targetPanel.classList.remove('hidden');
                targetPanel.classList.add('block');
            }
        });
    });

    // Language switcher for code examples
    const langTabs = document.querySelectorAll('.lang-tab');
    const langPanels = document.querySelectorAll('.lang-panel');

    langTabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const lang = tab.getAttribute('data-lang');

            // Active tab state
            langTabs.forEach(t => t.classList.remove('active', 'bg-accent', 'text-white'));
            tab.classList.add('active', 'bg-accent', 'text-white');

            // Panel visibility
            langPanels.forEach(p => p.classList.add('hidden'));
            langPanels.forEach(p => p.classList.remove('block'));

            const target = document.getElementById(`lang-${lang}`);
            if (target) {
                target.classList.remove('hidden');
                target.classList.add('block');
            }
        });
    });

    // Initialize first lang tab
    const firstLang = document.querySelector('.lang-tab');
    if (firstLang) firstLang.click();

    // MCP Config Switcher
    const mcpConfigTabs = document.querySelectorAll('.mcp-config-tab');
    const mcpConfigPanels = document.querySelectorAll('.mcp-config-panel');

    mcpConfigTabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const client = tab.getAttribute('data-mcp-client');

            mcpConfigTabs.forEach(t => t.classList.remove('active', 'bg-white', 'shadow-sm'));
            tab.classList.add('active', 'bg-white', 'shadow-sm');

            mcpConfigPanels.forEach(p => p.classList.add('hidden'));
            mcpConfigPanels.forEach(p => p.classList.remove('block'));

            const target = document.getElementById(`mcp-${client}`);
            if (target) {
                target.classList.remove('hidden');
                target.classList.add('block');
            }
        });
    });

    // Initialize first mcp tab
    const firstMcpTab = document.querySelector('.mcp-config-tab');
    if (firstMcpTab) firstMcpTab.click();
});

/**
 * Copy text to clipboard and show a success toast
 * @param {string} text - The text to copy
 */
function copyToClipboard(text) {
    if (!text) return;
    navigator.clipboard.writeText(text).then(() => {
        showToast('Copied to clipboard!');
    }).catch(err => {
        console.error('Failed to copy: ', err);
    });
}

/**
 * Copy the currently visible code block in the API switcher
 * @param {HTMLElement} btn - The button clicked
 */
function copyActiveCode(btn) {
    const container = btn.closest('.relative');
    const activePanel = container.querySelector('.lang-panel.block');
    if (activePanel) {
        const code = activePanel.querySelector('code').textContent;
        copyToClipboard(code.trim());
    }
}

/**
 * Copy the currently visible MCP configuration
 * @param {HTMLElement} btn - The button clicked
 */
function copyActiveMcpCode(btn) {
    const container = btn.closest('.relative');
    const activePanel = container.querySelector('.mcp-config-panel.block');
    if (activePanel) {
        const codeEl = activePanel.querySelector('code');
        if (codeEl) {
            copyToClipboard(codeEl.textContent.trim());
        } else {
            // Fallback for card-based layouts
            copyToClipboard(activePanel.textContent.replace(/\s+/g, ' ').trim());
        }
    }
}

/**
 * Specialized copy for the main MCP endpoint
 */
function copyMcpEndpoint() {
    const el = document.getElementById('mcpEndpoint');
    if (el) {
        copyToClipboard(el.textContent.trim());
    }
}

/**
 * Show a modern toast notification
 * @param {string} msg - The message to display
 */
function showToast(msg) {
    const toast = document.createElement('div');
    toast.className = 'toast-notification bg-dark-brown text-white p-3 rounded-lg shadow-xl fixed bottom-8 right-8 z-50 transform translate-y-20 opacity-0 transition-all duration-300';
    toast.innerHTML = `<i class="fas fa-check-circle mr-2 text-accent"></i> ${msg}`;
    document.body.appendChild(toast);

    // Trigger animation
    setTimeout(() => {
        toast.classList.remove('translate-y-20', 'opacity-0');
    }, 10);

    // Hide and remove
    setTimeout(() => {
        toast.classList.add('translate-y-20', 'opacity-0');
        setTimeout(() => {
            toast.remove();
        }, 300);
    }, 3000);
}
