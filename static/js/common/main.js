(function () {
    'use strict';

    /**
     * Helper function to get CSRF token from cookies.
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

    // --- PWA LOGIC (Global Scope) ---
    // Defined outside DOMContentLoaded to catch early events
    let deferredPrompt;

    function showInstallButton() {
        const installButton = document.getElementById('pwaInstallBtn');
        if (installButton) {
            installButton.style.display = 'flex';
            installButton.classList.remove('hidden');
        }
    }

    window.addEventListener('beforeinstallprompt', (e) => {
        // Prevent Chrome 67 and earlier from automatically showing the prompt
        e.preventDefault();
        // Stash the event so it can be triggered later
        deferredPrompt = e;
        // Update UI logic
        showInstallButton();
    });

    window.addEventListener('appinstalled', () => {
        const installButton = document.getElementById('pwaInstallBtn');
        if (installButton) {
            installButton.style.display = 'none';
        }
        deferredPrompt = null;
    });

    document.addEventListener('DOMContentLoaded', function () {

        // --- PWA Button Click Handler ---
        const installButton = document.getElementById('pwaInstallBtn');
        if (installButton) {
            // Check if the event fired *before* the DOM was ready
            if (deferredPrompt) {
                showInstallButton();
            }

            installButton.addEventListener('click', async () => {
                if (deferredPrompt) {
                    deferredPrompt.prompt();
                    const { outcome } = await deferredPrompt.userChoice;
                    console.log(`User response to the install prompt: ${outcome}`);
                    deferredPrompt = null;
                    installButton.style.display = 'none';
                }
            });
        }

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
                localStorage.setItem('darkMode', isDark ? 'enabled' : 'disabled');
                darkModeToggles.forEach(btn => {
                    const icon = btn.querySelector('i');
                    if (icon) {
                        icon.classList.toggle('fa-moon', !isDark);
                        icon.classList.toggle('fa-sun', isDark);
                    }
                });
            };

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
                localStorage.setItem(pageType + 'View', view);
            };

            gridViewBtn.addEventListener('click', () => toggleView('grid'));
            listViewBtn.addEventListener('click', () => toggleView('list'));

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
                const scrollAmount = (cardWidth + gap) * 2;

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