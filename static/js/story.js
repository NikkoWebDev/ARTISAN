/**
 * Scrollytelling "El camino de una pieza".
 * Cambia la escena según el paso visible y mueve el jaguar según el avance.
 * Solo usa transform/opacity. Sin JS, los pasos se leen como lista normal.
 */
(function () {
    const root = document.querySelector('[data-story]');
    if (!root) return;

    const steps = Array.from(root.querySelectorAll('.story-step'));
    const scenes = Array.from(root.querySelectorAll('.scene'));
    const jaguar = document.getElementById('story-jaguar');
    const bar = document.getElementById('story-progress-bar');
    const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    root.classList.add('is-enhanced');

    function setActive(i) {
        scenes.forEach(function (s, k) { s.classList.toggle('is-active', k === i); });
        steps.forEach(function (s, k) { s.classList.toggle('is-active', k === i); });
    }
    setActive(0);

    if ('IntersectionObserver' in window) {
        const io = new IntersectionObserver(function (entries) {
            entries.forEach(function (e) {
                if (e.isIntersecting) setActive(Number(e.target.dataset.step));
            });
        }, { rootMargin: '-45% 0px -45% 0px' });
        steps.forEach(function (s) { io.observe(s); });
    }

    let ticking = false;
    function update() {
        ticking = false;
        const r = root.getBoundingClientRect();
        const total = r.height - window.innerHeight * 0.6;
        const p = Math.max(0, Math.min(1, (-r.top + window.innerHeight * 0.2) / Math.max(total, 1)));
        if (bar) bar.style.transform = 'scaleX(' + p.toFixed(3) + ')';
        if (jaguar && !reduce) {
            // El jaguar cruza de -40 a 70 unidades del viewBox en x, y baja un poco al final
            jaguar.style.transform = 'translate(' + (-180 + p * 330).toFixed(1) + 'px,' + (300) + 'px) scale(.5)';
        }
    }
    function onScroll() {
        if (!ticking) { ticking = true; requestAnimationFrame(update); }
    }
    window.addEventListener('scroll', onScroll, { passive: true });
    window.addEventListener('resize', onScroll);
    update();
})();
