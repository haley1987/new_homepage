(() => {
  const initializeLocator = () => {
    const locator = document.querySelector('[data-hwl-locator]');
    const toggle = document.querySelector('[data-hwl-browse-toggle]');

    if (!locator || !toggle || locator.dataset.hwlReady === 'true') return;

    const label = toggle.querySelector('[data-hwl-browse-label]');
    let browseAll = false;
    let searchField;

    const updateResults = () => {
      const hasQuery = Boolean(searchField?.value.trim());
      const showResults = browseAll || hasQuery;

      locator.classList.toggle('hwl__locator-frame--show-results', showResults);
      toggle.setAttribute('aria-expanded', String(browseAll));
      if (label) label.textContent = browseAll ? 'Hide full directory' : 'Browse all locations';
    };

    const bindSearchField = () => {
      const field = locator.querySelector('.stockist-search-field');
      if (!field || field === searchField) return Boolean(field);

      searchField = field;
      searchField.addEventListener('input', updateResults);
      searchField.addEventListener('change', updateResults);
      searchField.addEventListener('search', updateResults);
      updateResults();
      return true;
    };

    toggle.addEventListener('click', () => {
      browseAll = !browseAll;
      updateResults();

      if (browseAll) {
        window.requestAnimationFrame(() => locator.scrollIntoView({ behavior: 'smooth', block: 'start' }));
      }
    });

    locator.dataset.hwlReady = 'true';

    if (!bindSearchField()) {
      const observer = new MutationObserver(() => {
        if (bindSearchField()) observer.disconnect();
      });
      observer.observe(locator, { childList: true, subtree: true });
    }
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeLocator, { once: true });
  } else {
    initializeLocator();
  }
})();
