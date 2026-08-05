(() => {
  if (window.HaywoodHomepage) return;

  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');

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

  const init = (root = document) => {
    updateHeader();
    protectVideo(root);
  };

  window.HaywoodHomepage = { init };
  window.addEventListener('scroll', updateHeader, { passive: true });
  document.addEventListener('DOMContentLoaded', () => init());
  document.addEventListener('shopify:section:load', (event) => init(event.target));
})();
