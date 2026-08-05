document.addEventListener('DOMContentLoaded', () => {
  // APO presence: Look for MW app container or attribute they inject
  const hasAPO = !!document.querySelector('.mw-product-options, [data-mwpo], [data-mwpo-app]');
  // Toggle any configure-only CTAs
  document.querySelectorAll('[data-apo-cta]').forEach(el => {
    el.style.display = hasAPO ? '' : 'none';
  });

  // Slide-over (expects .js-show-configs and .js-hide-configs + .configuration-overlay)
  const openers = document.querySelectorAll('.js-show-configs');
  const closers = document.querySelectorAll('.js-hide-configs');
  const overlay = document.querySelector('.configuration-overlay');
  function openOverlay(){ if(overlay){ overlay.classList.add('is-open'); document.documentElement.classList.add('no-scroll'); } }
  function closeOverlay(){ if(overlay){ overlay.classList.remove('is-open'); document.documentElement.classList.remove('no-scroll'); } }
  openers.forEach(b=>b.addEventListener('click', openOverlay));
  closers.forEach(b=>b.addEventListener('click', closeOverlay));

  // Sticky config bar (appears after CTAs leave viewport)
  const cta = document.querySelector('[data-sticky-anchor]') || document.querySelector('[data-apo-cta]');
  const bar = document.querySelector('.sticky-config-bar');
  if (cta && bar){
    const io = new IntersectionObserver(es => {
      es.forEach(e => { bar.style.display = e.isIntersecting ? 'none' : 'flex'; });
    }, { threshold: 0 });
    io.observe(cta);
    bar.querySelector('button')?.addEventListener('click', () => openers[0]?.click());
  }
});
