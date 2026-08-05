class ConfigDrawer extends HTMLElement {
  constructor() {
    super();
    this.overlay = this.querySelector('[data-config-close]');
    this.closeBtn = this.querySelector('.drawer__close');

    this.handleKey = this.handleKey.bind(this);
    this.onOpenClick = this.onOpenClick.bind(this);
    this.onCloseClick = this.onCloseClick.bind(this);
  }

  connectedCallback() {
    document.addEventListener('click', this.onOpenClick);
    this.overlay?.addEventListener('click', this.onCloseClick);
    this.closeBtn?.addEventListener('click', this.onCloseClick);
    document.addEventListener('keydown', this.handleKey);
  }

  disconnectedCallback() {
    document.removeEventListener('click', this.onOpenClick);
    document.removeEventListener('keydown', this.handleKey);
  }

onOpenClick(e) {
  const trigger = e.target.closest('[data-config-open],[data-config-overlay-open],.js-show-configs');
  if (!trigger) return;

  // Optional: guard for matching drawer id via aria-controls
  const targetId = trigger.getAttribute('aria-controls') || 'ConfigDrawer';
  if (this.id !== targetId) return;

  e.preventDefault();
  this.open();
}


  onCloseClick(e) {
    e?.preventDefault();
    this.close();
  }

  handleKey(e) {
    if (e.key === 'Escape' && this.isOpen()) this.close();
  }

  isOpen() { return this.hasAttribute('open'); }

  open() {
    this.setAttribute('open', '');
    document.documentElement.classList.add('overflow-hidden'); // lock scroll like Dawn does
    // If APO needs a refresh when the element becomes visible:
    window.requestAnimationFrame(() => {
      document.dispatchEvent(new CustomEvent('config-drawer:opened', { detail: { productId: this.dataset.productId }}));
      // If your options app exposes a re-init, do it here, e.g.:
       window.mwpo && window.mwpo.init && window.mwpo.init();
    });
  }

  close() {
    this.removeAttribute('open');
    document.documentElement.classList.remove('overflow-hidden');
    document.dispatchEvent(new CustomEvent('config-drawer:closed'));
  }
}
customElements.define('config-drawer', ConfigDrawer);

// Keep price in sync with selected variant (works with Dawn variant selectors or APO emitting a change event)
document.addEventListener('change', (e) => {
  const sel = e.target.closest('select[name="id"]');
  if (!sel) return;
  const priceEl = document.getElementById('ProductPrice');
  const opt = sel.selectedOptions?.[0];
  if (opt && priceEl) {
    // Assumes option text contains " - $X.XX"; adjust if you prefer Ajax to fetch money formats.
    const txt = opt.textContent.split(' - ').pop();
    if (txt) priceEl.textContent = txt;
  }
});
