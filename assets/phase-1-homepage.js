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

  const init = (root = document) => {
    updateHeader();
    protectVideo(root);
    revealSections(root);
  };

  window.HaywoodHomepage = { init };
  window.addEventListener('scroll', updateHeader, { passive: true });
  document.addEventListener('DOMContentLoaded', () => init());
  document.addEventListener('shopify:section:load', (event) => init(event.target));
})();
