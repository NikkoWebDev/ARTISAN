/**
 * Artisan - App UI Scripts
 * Micro-interacciones de lujo, buscador reactivo, galería interactiva y animaciones a 60fps
 */
document.addEventListener('DOMContentLoaded', function() {
    // 1. Mobile Menu Toggle
    const menuBtn = document.querySelector('.menu-toggle');
    const menuNav = document.getElementById('main-menu');
    if (menuBtn && menuNav) {
        menuBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            const isOpen = menuNav.classList.toggle('active');
            menuBtn.setAttribute('aria-expanded', isOpen);
            menuBtn.classList.toggle('is-active', isOpen);
        });

        document.addEventListener('click', function(e) {
            if (!menuNav.contains(e.target) && !menuBtn.contains(e.target)) {
                menuNav.classList.remove('active');
                menuBtn.setAttribute('aria-expanded', 'false');
                menuBtn.classList.remove('is-active');
            }
        });
    }

    // 2. Intersection Observer para reveals a 60fps
    const reveals = document.querySelectorAll('.reveal');
    if (reveals.length > 0 && 'IntersectionObserver' in window) {
        const observer = new IntersectionObserver((entries, obs) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('active');
                    obs.unobserve(entry.target);
                }
            });
        }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });
        reveals.forEach(el => observer.observe(el));
    } else {
        reveals.forEach(el => el.classList.add('active'));
    }

    // 3. Galería interactiva en ficha de producto (producto.html)
    const mainImg = document.querySelector('.principal-img');
    const thumbs = document.querySelectorAll('.thumb-img');
    if (mainImg && thumbs.length > 0) {
        thumbs.forEach(thumb => {
            thumb.addEventListener('click', function() {
                thumbs.forEach(t => t.classList.remove('is-active'));
                this.classList.add('is-active');
                
                // Transición suave de imagen
                mainImg.style.opacity = '0.4';
                mainImg.style.transform = 'scale(0.98)';
                setTimeout(() => {
                    mainImg.src = this.getAttribute('data-full') || this.src;
                    mainImg.alt = this.alt;
                    mainImg.style.opacity = '1';
                    mainImg.style.transform = 'scale(1)';
                }, 150);
            });
        });
    }

    // 4. Buscador reactivo en catálogo (lineaproductos.html)
    const searchInput = document.getElementById('catalogo-search');
    const productGrid = document.getElementById('catalogo-grid');
    const emptySearchMsg = document.getElementById('catalogo-empty-search');
    const countDisplay = document.getElementById('catalogo-count');

    if (searchInput && productGrid) {
        const cards = Array.from(productGrid.querySelectorAll('.producto-card'));

        searchInput.addEventListener('input', function(e) {
            const query = e.target.value.toLowerCase().trim();
            let visibleCount = 0;

            cards.forEach(card => {
                const title = (card.getAttribute('data-nombre') || card.querySelector('h3')?.textContent || '').toLowerCase();
                const cat = (card.getAttribute('data-categoria') || '').toLowerCase();
                const matches = !query || title.includes(query) || cat.includes(query);

                if (matches) {
                    card.style.display = '';
                    card.style.opacity = '1';
                    card.style.transform = 'scale(1)';
                    visibleCount++;
                } else {
                    card.style.display = 'none';
                    card.style.opacity = '0';
                    card.style.transform = 'scale(0.96)';
                }
            });

            if (countDisplay) {
                countDisplay.textContent = visibleCount;
            }

            if (emptySearchMsg) {
                emptySearchMsg.style.display = visibleCount === 0 ? 'block' : 'none';
            }
        });
    }

    // 5. Toast auto-dismiss
    const toasts = document.querySelectorAll('.toast');
    toasts.forEach(toast => {
        setTimeout(() => {
            toast.style.opacity = '0';
            setTimeout(() => toast.remove(), 400);
        }, 4000);
    });
});
