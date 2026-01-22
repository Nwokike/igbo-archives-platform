(function () {
    'use strict';

    /**
     * Helper function to get CSRF token from cookies.
     * @param {string} name - The name of the cookie (usually 'csrftoken').
     * @returns {string|null} The value of the cookie or null if not found.
     */
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    document.addEventListener('DOMContentLoaded', function () {

        // --- Dark Mode Handler ---
        const darkModeToggles = document.querySelectorAll('#darkModeToggle, #darkModeToggleMobile');
        if (darkModeToggles.length > 0) {
            const body = document.body;

            const applyTheme = (isDark) => {
                if (isDark) {
                    document.documentElement.classList.add('dark');
                    body.classList.add('dark-mode'); // Keep for legacy CSS compatibility if needed
                } else {
                    document.documentElement.classList.remove('dark');
                    body.classList.remove('dark-mode');
                }
                localStorage.setItem('darkMode', isDark ? 'enabled' : 'disabled');
                darkModeToggles.forEach(btn => {
                    const icon = btn.querySelector('i');
                    if (icon) {
                        icon.classList.toggle('fa-moon', !isDark);
                        icon.classList.toggle('fa-sun', isDark);
                    }
                });
            };

            // Apply saved theme on page load
            if (localStorage.getItem('darkMode') === 'enabled') {
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
                document.body.style.overflow = 'hidden'; // Prevent scroll
                const input = mobileSearchOverlay.querySelector('input');
                if (input) setTimeout(() => input.focus(), 100);
            });

            if (closeMobileSearch) {
                closeMobileSearch.addEventListener('click', () => {
                    mobileSearchOverlay.classList.add('hidden');
                    mobileSearchOverlay.classList.remove('flex');
                    document.body.style.overflow = ''; // Restore scroll
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

        // Close dropdowns when clicking outside
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
                form.action = this.href; // Use the URL from the link

                const csrfInput = document.createElement('input');
                csrfInput.type = 'hidden';
                csrfInput.name = 'csrfmiddlewaretoken';
                csrfInput.value = getCookie('csrftoken');
                form.appendChild(csrfInput);

                document.body.appendChild(form);
                form.submit();
            });
        }

        // --- PWA Installation Prompt ---
        let deferredPrompt;
        const installButton = document.getElementById('pwaInstallBtn');

        window.addEventListener('beforeinstallprompt', (e) => {
            e.preventDefault();
            deferredPrompt = e;
            if (installButton) {
                installButton.style.display = 'flex';
            }
        });

        if (installButton) {
            installButton.addEventListener('click', async () => {
                if (deferredPrompt) {
                    deferredPrompt.prompt();
                    deferredPrompt = null;
                    installButton.style.display = 'none';
                }
            });
        }

        window.addEventListener('appinstalled', () => {
            if (installButton) {
                installButton.style.display = 'none';
            }
        });

        // --- Comment Success Toast Notification ---
        if (window.location.hash.includes('comment-')) {
            const toast = document.createElement('div');
            toast.className = 'custom-toast success';
            toast.innerHTML = '<i class="fas fa-check-circle"></i> Comment posted successfully!';
            document.body.appendChild(toast);

            setTimeout(() => toast.remove(), 3500);

            // Clean the URL hash
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
                localStorage.setItem(pageType + 'View', view);
            };

            gridViewBtn.addEventListener('click', () => toggleView('grid'));
            listViewBtn.addEventListener('click', () => toggleView('list'));

            // Apply saved view on page load
            const savedView = localStorage.getItem(pageType + 'View') || 'grid';
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

        // --- Recommended Carousel ---
        const recommendedCarousel = document.querySelector('.recommended-carousel');
        if (recommendedCarousel) {
            const track = recommendedCarousel.querySelector('.carousel-track');
            const prevButton = recommendedCarousel.querySelector('.prev-btn');
            const nextButton = recommendedCarousel.querySelector('.next-btn');

            const scrollCarousel = (direction) => {
                if (!track) return;
                const card = track.querySelector('.recommended-card');
                if (!card) return;

                const cardWidth = card.offsetWidth;
                const gap = 20;
                const scrollAmount = (cardWidth + gap) * 2; // Scroll 2 cards

                track.scrollBy({
                    left: direction * scrollAmount,
                    behavior: 'smooth'
                });
            };

            if (prevButton) {
                prevButton.addEventListener('click', () => scrollCarousel(-1));
            }

            if (nextButton) {
                nextButton.addEventListener('click', () => scrollCarousel(1));
            }
        }
    });

})();

/**
 * A function to copy text to the clipboard.
 * Note: This remains in the global scope intentionally to be callable from rare `onclick` attributes if needed for specific simple cases.
 * For new development, prefer using event listeners.
 * @param {string} text - The text to copy.
 */
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showToast('Link copied to clipboard!', 'success');
    }).catch(err => {
        console.error('Could not copy text: ', err);
        showToast('Failed to copy link', 'error');
    });
}

/**
 * Display a custom toast notification.
 * @param {string} message - The message to display.
 * @param {string} type - 'success', 'error', 'info', 'warning'.
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

    // Trigger reflow to enable transition
    toast.offsetHeight;
    toast.classList.add('show');

    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 3500);
}

// Export for global usage
window.showToast = showToast;
