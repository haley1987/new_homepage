/* Haywood — Sidebar native scrollbar: idle → tease → hot with smooth fade-out */
(function () {
  const MIN_W     = 990;  // desktop breakpoint
  const HOT_ZONE  = 12;   // px from right edge to enter "hot"
  const LINGER_MS = 2200; // how long it stays visible after leaving
  const FADE_MS   = 800;  // actual fade-out duration (matches CSS)

  let hideTimer;

  function setState(sidebar, state) {
    sidebar.classList.remove('sb-tease', 'sb-hot', 'sb-fading');
    if (state) sidebar.classList.add(state);
  }

  // snapshot native thumb and cross-fade out (overlay only handles fade)
  function startFade(sidebar) {
    // mark fading state (CSS hides native during fade)
    sidebar.classList.add('sb-fading');
    const fader = ensureFader(sidebar);
    // set starting opacity 1 → CSS transition takes it to 0
    // position/size follow previous state; overlay just fades
    fader.style.opacity = '1';
    requestAnimationFrame(() => { fader.style.opacity = '0'; });

    setTimeout(() => {
      // finish: return to idle
      sidebar.classList.remove('sb-tease', 'sb-hot', 'sb-fading');
    }, FADE_MS + 50);
  }

  function ensureFader(sidebar) {
    let fader = sidebar.querySelector('.sb-fade-thumb');
    if (!fader) {
      fader = document.createElement('div');
      fader.className = 'sb-fade-thumb';
      sidebar.appendChild(fader);
    }
    // size/position of the overlay is not critical (cosmetic); we only fade it
    return fader;
  }

  function bind() {
    const sidebar = document.querySelector('.sidebar-drawer');
    if (!sidebar || window.innerWidth < MIN_W) return;
    if (sidebar.dataset.sbBound === '1') return;
    sidebar.dataset.sbBound = '1';

    const resetHideTimer = () => { clearTimeout(hideTimer); };
    const scheduleHide = () => {
      resetHideTimer();
      hideTimer = setTimeout(() => startFade(sidebar), LINGER_MS);
    };

    // pointer inside sidebar → show tease; near right edge → hot
    sidebar.addEventListener('mouseenter', () => { resetHideTimer(); setState(sidebar, 'sb-tease'); });
    sidebar.addEventListener('mousemove', (e) => {
      resetHideTimer();
      const r = sidebar.getBoundingClientRect();
      const fromRight = r.right - e.clientX;
      setState(sidebar, fromRight <= HOT_ZONE ? 'sb-hot' : 'sb-tease');
    });

    // scrolling also keeps it visible and restarts linger
    sidebar.addEventListener('wheel', () => { resetHideTimer(); setState(sidebar, 'sb-tease'); scheduleHide(); }, { passive: true });

    // leaving sidebar → do NOT hide immediately; wait, then fade
    sidebar.addEventListener('mouseleave', scheduleHide);

    // Theme editor reloads / resizing
    document.addEventListener('shopify:section:load', bind);
    window.addEventListener('resize', () => {
      if (window.innerWidth < MIN_W) setState(sidebar, null);
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', bind);
  } else {
    bind();
  }
})();
