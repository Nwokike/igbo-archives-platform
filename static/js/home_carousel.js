/**
 * Homepage Carousel Logic
 * Handles the "Featured Archive" infinite scroll carousel.
 */
(function () {
    const track = document.getElementById('carouselTrack');
    const dots = document.querySelectorAll('.carousel-dot');
    const prevBtn = document.getElementById('carouselPrev');
    const nextBtn = document.getElementById('carouselNext');
    if (!track || !dots.length) return;

    let currentIndex = 0;
    const slideCount = dots.length;
    let autoplayInterval;

    function scrollToSlide(index) {
        const slides = track.querySelectorAll('.carousel-slide');
        if (slides[index]) {
            slides[index].scrollIntoView({ behavior: 'smooth', inline: 'center', block: 'nearest' });
            updateDots(index);
            currentIndex = index;
        }
    }

    function updateDots(activeIndex) {
        dots.forEach((dot, i) => {
            dot.classList.toggle('bg-vintage-gold', i === activeIndex);
            dot.classList.toggle('w-4', i === activeIndex);
            dot.classList.toggle('bg-white/30', i !== activeIndex);
            dot.classList.toggle('w-1.5', i !== activeIndex);
        });
    }

    function nextSlide() {
        currentIndex = (currentIndex + 1) % slideCount;
        scrollToSlide(currentIndex);
    }

    function prevSlide() {
        currentIndex = (currentIndex - 1 + slideCount) % slideCount;
        scrollToSlide(currentIndex);
    }

    function startAutoplay() {
        autoplayInterval = setInterval(nextSlide, 4000);
    }

    function stopAutoplay() {
        clearInterval(autoplayInterval);
    }

    // Event listeners
    prevBtn?.addEventListener('click', () => { stopAutoplay(); prevSlide(); startAutoplay(); });
    nextBtn?.addEventListener('click', () => { stopAutoplay(); nextSlide(); startAutoplay(); });
    dots.forEach((dot, i) => {
        dot.addEventListener('click', () => { stopAutoplay(); scrollToSlide(i); startAutoplay(); });
    });

    // Pause on hover
    track.addEventListener('mouseenter', stopAutoplay);
    track.addEventListener('mouseleave', startAutoplay);

    // Start autoplay
    startAutoplay();
})();
