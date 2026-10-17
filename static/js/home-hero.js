(() => {
  const root = document.querySelector('[data-hero-slider]');
  if (!root) return;
  const slides = [...root.querySelectorAll('[data-hero-slide]')];
  const dots = [...root.querySelectorAll('[data-hero-dot]')];
  const count = root.querySelector('[data-hero-count]');
  if (slides.length < 2) return;
  let current = Math.max(0, slides.findIndex((slide) => !slide.hidden));
  let timer;
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  const show = (index) => {
    current = (index + slides.length) % slides.length;
    slides.forEach((slide, i) => {
      slide.hidden = i !== current;
      const video = slide.querySelector('video');
      if (video) {
        if (i === current && !reducedMotion && !document.hidden) video.play().catch(() => {});
        else video.pause();
      }
    });
    dots.forEach((dot, i) => dot.setAttribute('aria-current', String(i === current)));
    if (count) count.textContent = `${String(current + 1).padStart(2, '0')} / ${String(slides.length).padStart(2, '0')}`;
  };
  const stop = () => window.clearInterval(timer);
  const start = () => {
    stop();
    if (!reducedMotion && !document.hidden) timer = window.setInterval(() => show(current + 1), 7000);
  };
  root.querySelector('[data-hero-prev]')?.addEventListener('click', () => { show(current - 1); start(); });
  root.querySelector('[data-hero-next]')?.addEventListener('click', () => { show(current + 1); start(); });
  dots.forEach((dot) => dot.addEventListener('click', () => { show(Number(dot.dataset.heroDot)); start(); }));
  root.addEventListener('mouseenter', stop);
  root.addEventListener('mouseleave', start);
  root.addEventListener('focusin', stop);
  root.addEventListener('focusout', (event) => { if (!root.contains(event.relatedTarget)) start(); });
  document.addEventListener('visibilitychange', () => document.hidden ? stop() : start());
  show(current);
  start();
})();
