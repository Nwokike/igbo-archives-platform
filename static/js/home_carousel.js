/**
 * Homepage Carousel Logic
 * Uses Swiper.js for a modern, split-screen hero slider.
 */
document.addEventListener('DOMContentLoaded', function () {
    const swiperContainer = document.querySelector('.swiper-container');
    
    if (swiperContainer && typeof Swiper !== 'undefined') {
        const heroSwiper = new Swiper(swiperContainer, {
            // "Grand" fade effect
            effect: 'fade',
            fadeEffect: {
                crossFade: true
            },
            
            // Loop and Autoplay
            loop: true,
            speed: 1200, // Slightly slower for more "grand" feel
            autoplay: {
                delay: 6000,
                disableOnInteraction: false,
                pauseOnMouseEnter: true,
            },

            // Navigation arrows
            navigation: {
                nextEl: '.swiper-button-next-custom',
                prevEl: '.swiper-button-prev-custom',
            },

            // Pagination dots
            pagination: {
                el: '.swiper-pagination-custom',
                clickable: true,
                renderBullet: function (index, className) {
                    return '<span class="' + className + '"></span>';
                },
            },
            
            // Accessibility
            a11y: {
                prevSlideMessage: 'Previous slide',
                nextSlideMessage: 'Next slide',
            },

            // On initialization and slide change
            on: {
                init: function () {
                    // Force a re-calculation of layout if needed
                    this.update();
                },
            }
        });

        // Pause on focus for accessibility
        swiperContainer.addEventListener('focusin', () => heroSwiper.autoplay.stop());
        swiperContainer.addEventListener('focusout', () => heroSwiper.autoplay.start());
    } else if (swiperContainer) {
        console.warn('Swiper is not defined. Ensure swiper-bundle.min.js is loaded.');
    }
});
