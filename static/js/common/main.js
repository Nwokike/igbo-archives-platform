(function () {
    'use strict';

    /**
     * Helper: getCookie is provided by utils.js (loaded before this file).
     * Use the global getCookie() function.
     */

    // --- PWA LOGIC (Moved to pwa-install.js) ---
    // Redundant listeners removed to prevent conflicts and ensure reliable visibility.

    document.addEventListener('DOMContentLoaded', function () {

        // --- Dark Mode Handler ---
        const darkModeToggles = document.querySelectorAll('#darkModeToggle, #darkModeToggleMobile');
        if (darkModeToggles.length > 0) {
            const body = document.body;

            const applyTheme = (isDark) => {
                if (isDark) {
                    document.documentElement.classList.add('dark');
                    body.classList.add('dark-mode');
                } else {
                    document.documentElement.classList.remove('dark');
                    body.classList.remove('dark-mode');
                }
                try {
                    localStorage.setItem('darkMode', isDark ? 'enabled' : 'disabled');
                } catch (storageError) {
                    // Silently fail if localStorage is blocked by tracking prevention
                }
                darkModeToggles.forEach(btn => {
                    const icon = btn.querySelector('i');
                    if (icon) {
                        icon.classList.toggle('fa-moon', !isDark);
                        icon.classList.toggle('fa-sun', isDark);
                    }
                });
            };

            let isDarkModeEnabled = false;
            try {
                isDarkModeEnabled = localStorage.getItem('darkMode') === 'enabled';
            } catch (storageError) {
                // Silently fail if localStorage is blocked by tracking prevention
            }
            if (isDarkModeEnabled) {
                applyTheme(true);
            }

            darkModeToggles.forEach(toggle => {
                toggle.addEventListener('click', () => {
                    const isDark = !body.classList.contains('dark-mode');
                    applyTheme(isDark);
                });
            });
        }

        // --- Mobile Search Overlay Handler ---
        const mobileSearchBtn = document.getElementById('mobileSearchBtn');
        const mobileSearchOverlay = document.getElementById('mobileSearchOverlay');
        const closeMobileSearch = document.getElementById('closeMobileSearch');

        if (mobileSearchBtn && mobileSearchOverlay) {
            mobileSearchBtn.addEventListener('click', () => {
                mobileSearchOverlay.classList.remove('hidden');
                mobileSearchOverlay.classList.add('flex');
                document.body.style.overflow = 'hidden';
                const input = mobileSearchOverlay.querySelector('input');
                if (input) setTimeout(() => input.focus(), 100);
            });

            if (closeMobileSearch) {
                closeMobileSearch.addEventListener('click', () => {
                    mobileSearchOverlay.classList.add('hidden');
                    mobileSearchOverlay.classList.remove('flex');
                    document.body.style.overflow = '';
                });
            }
        }

        // --- Alert Close Handler ---
        document.querySelectorAll('.alert-close').forEach(btn => {
            btn.addEventListener('click', function () {
                const alert = this.closest('.alert, .alert-success, .alert-error, .alert-warning, .alert-info');
                if (alert) alert.remove();
            });
        });

        // --- Dropdown Menus (Profile & Notifications) ---
        const profileButton = document.getElementById('profileButton');
        const profileDropdown = document.getElementById('profileDropdown');
        const notificationBell = document.getElementById('notificationBell');
        const notificationDropdown = document.getElementById('notificationDropdown');

        const showDropdown = (dropdown) => {
            dropdown.classList.remove('opacity-0', 'invisible', 'translate-y-2');
            dropdown.classList.add('opacity-100', 'visible', 'translate-y-0');
        };

        const hideDropdown = (dropdown) => {
            dropdown.classList.add('opacity-0', 'invisible', 'translate-y-2');
            dropdown.classList.remove('opacity-100', 'visible', 'translate-y-0');
        };

        const isDropdownVisible = (dropdown) => {
            return dropdown.classList.contains('opacity-100');
        };

        if (profileButton && profileDropdown) {
            profileButton.addEventListener('click', (e) => {
                e.stopPropagation();
                if (isDropdownVisible(profileDropdown)) {
                    hideDropdown(profileDropdown);
                } else {
                    showDropdown(profileDropdown);
                    if (notificationDropdown) hideDropdown(notificationDropdown);
                }
            });
        }

        if (notificationBell && notificationDropdown) {
            notificationBell.addEventListener('click', async (e) => {
                e.stopPropagation();
                const bell = e.currentTarget;

                if (profileDropdown) hideDropdown(profileDropdown);

                if (!isDropdownVisible(notificationDropdown)) {
                    notificationDropdown.innerHTML = '<div class="p-4 text-center text-vintage-beaver"><i class="fas fa-spinner fa-spin"></i> Loading...</div>';
                    showDropdown(notificationDropdown);
                    try {
                        const response = await fetch(bell.dataset.url);
                        if (response.ok) {
                            notificationDropdown.innerHTML = await response.text();
                        } else {
                            notificationDropdown.innerHTML = '<div class="p-4 text-center text-vintage-beaver"><i class="fas fa-bell-slash"></i><p>Failed to load</p></div>';
                        }
                    } catch (error) {
                        console.error('Error loading notifications:', error);
                        notificationDropdown.innerHTML = '<div class="p-4 text-center text-vintage-beaver"><i class="fas fa-exclamation-triangle"></i><p>Error</p></div>';
                    }
                } else {
                    hideDropdown(notificationDropdown);
                }
            });
        }

        document.addEventListener('click', (e) => {
            if (profileDropdown && isDropdownVisible(profileDropdown) && !profileButton.contains(e.target)) {
                hideDropdown(profileDropdown);
            }
            if (notificationDropdown && isDropdownVisible(notificationDropdown) && !notificationBell.contains(e.target)) {
                hideDropdown(notificationDropdown);
            }
        });

        // --- Instant Logout Handler ---
        const logoutLink = document.getElementById('logoutLink');
        if (logoutLink) {
            logoutLink.addEventListener('click', function (e) {
                e.preventDefault();
                const form = document.createElement('form');
                form.method = 'POST';
                form.action = this.href;

                const csrfInput = document.createElement('input');
                csrfInput.type = 'hidden';
                csrfInput.name = 'csrfmiddlewaretoken';
                csrfInput.value = getCookie('csrftoken');
                form.appendChild(csrfInput);

                document.body.appendChild(form);
                form.submit();
            });
        }

        // --- Comment Success Toast Notification ---
        if (window.location.hash.includes('comment-')) {
            const toast = document.createElement('div');
            toast.className = 'custom-toast success';
            toast.innerHTML = '<i class="fas fa-check-circle"></i> Comment posted successfully!';
            document.body.appendChild(toast);

            setTimeout(() => toast.remove(), 3500);

            setTimeout(() => {
                history.replaceState(null, null, window.location.pathname + window.location.search);
            }, 100);
        }

        // --- Grid/List View Toggle ---
        const gridViewBtn = document.getElementById('gridViewBtn');
        const listViewBtn = document.getElementById('listViewBtn');
        const contentContainer = document.getElementById('archiveGrid') ||
            document.getElementById('insightsGrid') ||
            document.getElementById('reviewsGrid');

        if (contentContainer && gridViewBtn && listViewBtn) {
            const pageType = contentContainer.id.replace('Grid', '');

            const toggleView = (view) => {
                const isGrid = view === 'grid';
                contentContainer.className = isGrid ? 'archive-view-grid' : 'archive-view-list';
                gridViewBtn.classList.toggle('active', isGrid);
                listViewBtn.classList.toggle('active', !isGrid);
                try {
                    localStorage.setItem(pageType + 'View', view);
                } catch (storageError) {
                    // Silently fail if localStorage is blocked by tracking prevention
                }
            };

            gridViewBtn.addEventListener('click', () => toggleView('grid'));
            listViewBtn.addEventListener('click', () => toggleView('list'));

            let savedView = 'grid';
            try {
                savedView = localStorage.getItem(pageType + 'View') || 'grid';
            } catch (storageError) {
                // Silently fail if localStorage is blocked by tracking prevention
            }
            toggleView(savedView);
        }

        // --- Carousel Logic ---
        const carousel = document.getElementById('featuredCarousel');
        if (carousel) {
            let currentSlide = 0;
            let autoPlayInterval;
            const slides = carousel.querySelectorAll('.carousel-slide');
            const dots = carousel.querySelectorAll('.carousel-dot');
            const nextButton = carousel.querySelector('.carousel-next');
            const prevButton = carousel.querySelector('.carousel-prev');

            const goToSlide = (index) => {
                slides[currentSlide].classList.remove('active');
                dots[currentSlide].classList.remove('active');
                currentSlide = (index + slides.length) % slides.length;
                slides[currentSlide].classList.add('active');
                dots[currentSlide].classList.add('active');
            };

            const resetAutoPlay = () => {
                clearInterval(autoPlayInterval);
                autoPlayInterval = setInterval(() => {
                    goToSlide(currentSlide + 1);
                }, 5000);
            };

            if (nextButton) {
                nextButton.addEventListener('click', () => {
                    goToSlide(currentSlide + 1);
                    resetAutoPlay();
                });
            }

            if (prevButton) {
                prevButton.addEventListener('click', () => {
                    goToSlide(currentSlide - 1);
                    resetAutoPlay();
                });
            }

            dots.forEach((dot, index) => {
                dot.addEventListener('click', () => {
                    goToSlide(index);
                    resetAutoPlay();
                });
            });

            if (slides.length > 1) {
                resetAutoPlay();
            }
        }

        // --- Share Dropdowns (Replaces inline script in share_buttons.html) ---
        // Handles multiple dropdowns on a single page by using classes
        const setupShareDropdowns = () => {
            const dropdowns = document.querySelectorAll('.share-dropdown-container');

            dropdowns.forEach(container => {
                const toggleBtn = container.querySelector('.share-toggle-button');
                const shareMenu = container.querySelector('.share-menu');

                if (!toggleBtn || !shareMenu) return;

                toggleBtn.addEventListener('click', function (e) {
                    e.stopPropagation();
                    const isExpanded = toggleBtn.getAttribute('aria-expanded') === 'true';

                    // Close all other open dropdowns first
                    document.querySelectorAll('.share-toggle-button').forEach(btn => {
                        if (btn !== toggleBtn) {
                            btn.setAttribute('aria-expanded', 'false');
                            const parent = btn.closest('.share-dropdown-container');
                            const menu = parent ? parent.querySelector('.share-menu') : null;
                            if (menu) {
                                menu.classList.add('opacity-0', 'scale-95', 'pointer-events-none');
                                menu.classList.remove('opacity-100', 'scale-100');
                            }
                        }
                    });

                    if (isExpanded) {
                        closeShareMenu(toggleBtn, shareMenu);
                    } else {
                        openShareMenu(toggleBtn, shareMenu);
                    }
                });
            });

            document.addEventListener('click', function (e) {
                dropdowns.forEach(container => {
                    const toggleBtn = container.querySelector('.share-toggle-button');
                    const shareMenu = container.querySelector('.share-menu');
                    if (toggleBtn && shareMenu && !container.contains(e.target)) {
                        closeShareMenu(toggleBtn, shareMenu);
                    }
                });
            });

            function openShareMenu(btn, menu) {
                btn.setAttribute('aria-expanded', 'true');
                menu.classList.remove('opacity-0', 'scale-95', 'pointer-events-none');
                menu.classList.add('opacity-100', 'scale-100');
            }

            function closeShareMenu(btn, menu) {
                btn.setAttribute('aria-expanded', 'false');
                menu.classList.add('opacity-0', 'scale-95', 'pointer-events-none');
                menu.classList.remove('opacity-100', 'scale-100');
            }
        };
        setupShareDropdowns();
    });

})();

/**
 * A function to copy text to the clipboard.
 * Includes fallback for environments without Navigator Clipboard API.
 */
function copyToClipboard(text) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(() => {
            showToast('Link copied to clipboard!', 'success');
        }).catch(err => {
            console.error('Could not copy text: ', err);
            fallbackCopyToClipboard(text);
        });
    } else {
        fallbackCopyToClipboard(text);
    }
}

function fallbackCopyToClipboard(text) {
    const textarea = document.createElement('textarea');
    textarea.value = text;
    textarea.style.position = 'fixed'; // Avoid scrolling to bottom
    textarea.style.opacity = '0';
    textarea.style.left = '-9999px';
    document.body.appendChild(textarea);
    textarea.focus();
    textarea.select();

    try {
        const successful = document.execCommand('copy');
        if (successful) {
            showToast('Link copied to clipboard!', 'success');
        } else {
            showToast('Failed to copy link', 'error');
        }
    } catch (err) {
        console.error('Fallback copy failed', err);
        showToast('Press Ctrl+C to copy', 'info');
    }
    document.body.removeChild(textarea);
}

/**
 * Display a custom toast notification.
 */
function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `custom-toast ${type}`;

    let icon = 'check-circle';
    if (type === 'error') icon = 'times-circle';
    if (type === 'warning') icon = 'exclamation-triangle';
    if (type === 'info') icon = 'info-circle';

    toast.innerHTML = `<i class="fas fa-${icon}"></i> ${message}`;
    document.body.appendChild(toast);

    toast.offsetHeight;
    toast.classList.add('show');

    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 3500);
}

window.showToast = showToast;