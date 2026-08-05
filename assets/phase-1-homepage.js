(() => {
  if (window.HaywoodHomepage) return;

  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  let revealObserver;

  const updateHeader = () => {
    document.body.classList.toggle('hw-header-scrolled', window.scrollY > 40);
  };

  const protectVideo = (root = document) => {
    const saveData = navigator.connection && navigator.connection.saveData;
    if (!saveData && !reducedMotion.matches) return;
    root.querySelectorAll('.hw-hero__video').forEach((video) => {
      video.pause();
      video.removeAttribute('autoplay');
      video.preload = 'none';
    });
  };

  const revealSections = (root = document) => {
    if (reducedMotion.matches || !('IntersectionObserver' in window)) return;

    document.body.classList.add('hw-motion-ready');
    if (!revealObserver) {
      revealObserver = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;
          entry.target.classList.add('hw-in-view');
          revealObserver.unobserve(entry.target);
        });
      }, { rootMargin: '0px 0px -8% 0px', threshold: 0.08 });
    }

    const sections = root.matches?.('.hw-section') ? [root] : root.querySelectorAll('.hw-section');
    sections.forEach((section) => {
      if (!section.classList.contains('hw-in-view')) revealObserver.observe(section);
    });
  };

  const setupScrollCues = (root = document) => {
    const railSelector = [
      '.hw-trust__list',
      '.hw-product-explorer__grid',
      '.hw-process__grid',
      '.hw-education__grid',
      '.hw-community__grid'
    ].join(',');
    const rails = root.matches?.(railSelector) ? [root] : root.querySelectorAll(railSelector);

    rails.forEach((rail) => {
      if (rail.dataset.hwScrollCue === 'true') return;
      rail.dataset.hwScrollCue = 'true';

      const cue = document.createElement('div');
      cue.className = 'hw-scroll-cue';
      cue.setAttribute('aria-hidden', 'true');
      cue.innerHTML = '<span>Swipe</span><span class="hw-scroll-cue__track"><i></i></span><span class="hw-scroll-cue__arrow">→</span>';
      rail.insertAdjacentElement('afterend', cue);

      const updateCue = () => {
        cue.hidden = rail.scrollWidth <= rail.clientWidth + 8;
        if (Math.abs(rail.scrollLeft) > 8) cue.classList.add('hw-scroll-cue--used');
      };

      rail.addEventListener('scroll', updateCue, { passive: true });
      if ('ResizeObserver' in window) new ResizeObserver(updateCue).observe(rail);
      requestAnimationFrame(updateCue);
    });
  };

  const init = (root = document) => {
    updateHeader();
    protectVideo(root);
    revealSections(root);
    setupScrollCues(root);
  };

  window.HaywoodHomepage = { init };
  window.addEventListener('scroll', updateHeader, { passive: true });
  document.addEventListener('DOMContentLoaded', () => init());
  document.addEventListener('shopify:section:load', (event) => init(event.target));
})();
