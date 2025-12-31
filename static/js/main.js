(function() {
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

    document.addEventListener('DOMContentLoaded', function() {
        
        // --- Dark Mode Handler ---
        const darkModeToggle = document.getElementById('darkModeToggle');
        if (darkModeToggle) {
            const body = document.body;
            const icon = darkModeToggle.querySelector('i');
            
            // Apply saved theme on page load
            if (localStorage.getItem('darkMode') === 'enabled') {
                body.classList.add('dark-mode');
                icon.classList.remove('fa-moon');
                icon.classList.add('fa-sun');
            }
            
            darkModeToggle.addEventListener('click', () => {
                body.classList.toggle('dark-mode');
                const isDarkMode = body.classList.contains('dark-mode');
                localStorage.setItem('darkMode', isDarkMode ? 'enabled' : 'disabled');
                icon.classList.toggle('fa-moon', !isDarkMode);
                icon.classList.toggle('fa-sun', isDarkMode);
            });
        }

        // --- Sticky Header Handler ---
        const stickyHeaderWrapper = document.querySelector('.sticky-header-wrapper');
        if (stickyHeaderWrapper) {
            const scrollThreshold = 100;
            window.addEventListener('scroll', () => {
                const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
                if (scrollTop > scrollThreshold) {
                    stickyHeaderWrapper.classList.add('shrink');
                } else {
                    stickyHeaderWrapper.classList.remove('shrink');
                }
            }, { passive: true });
        }

        // --- Dropdown Menus (Profile & Notifications) ---
        const profileButton = document.getElementById('profileButton');
        const profileDropdown = document.getElementById('profileDropdown');
        const notificationBell = document.getElementById('notificationBell');
        const notificationDropdown = document.getElementById('notificationDropdown');

        if (profileButton && profileDropdown) {
            profileButton.addEventListener('click', (e) => {
                e.stopPropagation();
                profileDropdown.classList.toggle('show');
                if (notificationDropdown) {
                    notificationDropdown.style.display = 'none'; // Close other dropdown
                }
            });
        }

        if (notificationBell && notificationDropdown) {
            notificationBell.addEventListener('click', async (e) => {
                e.stopPropagation();
                const bell = e.currentTarget;
                const isVisible = notificationDropdown.style.display === 'block';

                if (profileDropdown) {
                    profileDropdown.classList.remove('show'); // Close other dropdown
                }

                if (!isVisible) {
                    notificationDropdown.innerHTML = '<div class="notification-loading"><i class="fas fa-spinner fa-spin"></i> Loading...</div>';
                    notificationDropdown.style.display = 'block';
                    try {
                        const response = await fetch(bell.dataset.url);
                        if (response.ok) {
                            notificationDropdown.innerHTML = await response.text();
                        } else {
                            notificationDropdown.innerHTML = '<div class="notification-empty"><i class="fas fa-bell-slash"></i><p>Failed to load</p></div>';
                        }
                    } catch (error) {
                        console.error('Error loading notifications:', error);
                        notificationDropdown.innerHTML = '<div class="notification-empty"><i class="fas fa-exclamation-triangle"></i><p>Error</p></div>';
                    }
                } else {
                    notificationDropdown.style.display = 'none';
                }
            });
        }
        
        // Close dropdowns when clicking outside
        document.addEventListener('click', (e) => {
            if (profileDropdown && profileDropdown.classList.contains('show')) {
                profileDropdown.classList.remove('show');
            }
            if (notificationDropdown && notificationDropdown.style.display === 'block') {
                if (!notificationBell.contains(e.target)) {
                    notificationDropdown.style.display = 'none';
                }
            }
        });

        // --- Instant Logout Handler ---
        const logoutLink = document.getElementById('logoutLink');
        if (logoutLink) {
            logoutLink.addEventListener('click', function(e) {
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
        // You can implement a more elegant notification here if needed
        alert('Link copied to clipboard!');
    }).catch(err => {
        console.error('Could not copy text: ', err);
    });
}
