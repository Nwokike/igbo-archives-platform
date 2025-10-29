document.addEventListener('DOMContentLoaded', function() {
    const darkModeToggle = document.querySelector('.night-mode-toggle');
    const body = document.body;
    
    const darkMode = localStorage.getItem('darkMode');
    if (darkMode === 'enabled') {
        body.classList.add('dark-mode');
        if (darkModeToggle) {
            darkModeToggle.textContent = '☀️';
        }
    }
    
    if (darkModeToggle) {
        darkModeToggle.addEventListener('click', function() {
            body.classList.toggle('dark-mode');
            if (body.classList.contains('dark-mode')) {
                localStorage.setItem('darkMode', 'enabled');
                darkModeToggle.textContent = '☀️';
            } else {
                localStorage.setItem('darkMode', 'disabled');
                darkModeToggle.textContent = '🌙';
            }
        });
    }
    
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
                const { outcome } = await deferredPrompt.userChoice;
                console.log(`User response to the install prompt: ${outcome}`);
                deferredPrompt = null;
                installButton.style.display = 'none';
            }
        });
    }
    
    window.addEventListener('appinstalled', () => {
        console.log('PWA was installed');
        if (installButton) {
            installButton.style.display = 'none';
        }
    });
});

function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(function() {
        alert('Link copied to clipboard!');
    }, function(err) {
        console.error('Could not copy text: ', err);
    });
}


let currentSlide = 0;
let autoPlayInterval;

function moveCarousel(direction) {
    const slides = document.querySelectorAll('.carousel-slide');
    const dots = document.querySelectorAll('.carousel-dot');
    
    if (slides.length === 0) return;
    
    slides[currentSlide].classList.remove('active');
    dots[currentSlide].classList.remove('active');
    
    currentSlide = (currentSlide + direction + slides.length) % slides.length;
    
    slides[currentSlide].classList.add('active');
    dots[currentSlide].classList.add('active');
    
    resetAutoPlay();
}

function goToSlide(index) {
    const slides = document.querySelectorAll('.carousel-slide');
    const dots = document.querySelectorAll('.carousel-dot');
    
    if (slides.length === 0) return;
    
    slides[currentSlide].classList.remove('active');
    dots[currentSlide].classList.remove('active');
    
    currentSlide = index;
    
    slides[currentSlide].classList.add('active');
    dots[currentSlide].classList.add('active');
    
    resetAutoPlay();
}

function autoPlayCarousel() {
    const slides = document.querySelectorAll('.carousel-slide');
    if (slides.length > 1) {
        autoPlayInterval = setInterval(() => {
            const randomSlide = Math.floor(Math.random() * slides.length);
            goToSlide(randomSlide);
        }, 5000);
    }
}

function resetAutoPlay() {
    if (autoPlayInterval) {
        clearInterval(autoPlayInterval);
    }
    autoPlayCarousel();
}

function toggleArchiveView(view) {
    console.log('toggleArchiveView called with view:', view);
    
    let container = document.getElementById('archiveGrid') || 
                    document.getElementById('insightsGrid') || 
                    document.getElementById('reviewsGrid');
    
    const gridBtn = document.getElementById('gridViewBtn');
    const listBtn = document.getElementById('listViewBtn');
    
    if (!container) {
        console.error('Container not found! Looking for: archiveGrid, insightsGrid, or reviewsGrid');
        return;
    }
    
    console.log('Container found:', container.id, 'Current class:', container.className);
    
    const pageType = container.id.replace('Grid', '');
    
    if (view === 'grid') {
        container.className = 'archive-view-grid';
        gridBtn?.classList.add('active');
        listBtn?.classList.remove('active');
        localStorage.setItem(pageType + 'View', 'grid');
        console.log('Switched to GRID view');
    } else {
        container.className = 'archive-view-list';
        gridBtn?.classList.remove('active');
        listBtn?.classList.add('active');
        localStorage.setItem(pageType + 'View', 'list');
        console.log('Switched to LIST view');
    }
}

document.addEventListener('DOMContentLoaded', function() {
    const carousel = document.getElementById('featuredCarousel');
    if (carousel) {
        autoPlayCarousel();
        
        carousel.addEventListener('mouseenter', () => {
            if (autoPlayInterval) {
                clearInterval(autoPlayInterval);
            }
        });
        
        carousel.addEventListener('mouseleave', () => {
            autoPlayCarousel();
        });
    }
    
    let container = document.getElementById('archiveGrid') || 
                    document.getElementById('insightsGrid') || 
                    document.getElementById('reviewsGrid');
    
    if (container) {
        const pageType = container.id.replace('Grid', '');
        const savedView = localStorage.getItem(pageType + 'View') || 'grid';
        toggleArchiveView(savedView);
    }
    
    let lastScrollTop = 0;
    const header = document.querySelector('.sticky-header-wrapper');
    
    window.addEventListener('scroll', () => {
        const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
        
        if (scrollTop > 100) {
            header?.classList.add('shrink');
        } else {
            header?.classList.remove('shrink');
        }
        
        lastScrollTop = scrollTop;
    }, { passive: true });
    
    // Notification Bell Dropdown
    const notificationBell = document.getElementById('notificationBell');
    const notificationDropdown = document.getElementById('notificationDropdown');
    const profileButton = document.getElementById('profileButton');
    const profileDropdown = document.getElementById('profileDropdown');
    
    if (notificationBell && notificationDropdown) {
        notificationBell.addEventListener('click', async (e) => {
            e.stopPropagation();
            
            // Close profile dropdown if open
            if (profileDropdown) {
                profileDropdown.classList.remove('show');
            }
            
            // Toggle notification dropdown
            const isVisible = notificationDropdown.style.display === 'block';
            
            if (!isVisible) {
                // Load notifications via AJAX
                try {
                    const response = await fetch('/profile/notifications/dropdown/');
                    const html = await response.text();
                    notificationDropdown.innerHTML = html;
                    notificationDropdown.style.display = 'block';
                } catch (error) {
                    console.error('Error loading notifications:', error);
                    notificationDropdown.innerHTML = '<div class="notification-loading">Error loading notifications</div>';
                    notificationDropdown.style.display = 'block';
                }
            } else {
                notificationDropdown.style.display = 'none';
            }
        });
    }
    
    if (profileButton && profileDropdown) {
        profileButton.addEventListener('click', (e) => {
            e.stopPropagation();
            
            // Close notification dropdown if open
            if (notificationDropdown) {
                notificationDropdown.style.display = 'none';
            }
            
            // Toggle profile dropdown
            const isVisible = profileDropdown.style.display === 'block';
            if (isVisible) {
                profileDropdown.style.display = 'none';
            } else {
                profileDropdown.style.display = 'block';
            }
        });
    }
    
    // Close dropdowns when clicking outside
    document.addEventListener('click', () => {
        if (profileDropdown) {
            profileDropdown.style.display = 'none';
        }
        if (notificationDropdown) {
            notificationDropdown.style.display = 'none';
        }
    });
});
