(() => {
  document.querySelectorAll('[data-hwfaq]').forEach((root) => {
    const search = root.querySelector('[data-hwfaq-search]');
    const items = [...root.querySelectorAll('[data-hwfaq-item]')];
    const groups = [...root.querySelectorAll('[data-hwfaq-group]')];
    const empty = root.querySelector('[data-hwfaq-empty]');
    if (!search || items.length === 0) return;

    search.addEventListener('input', () => {
      const query = search.value.trim().toLowerCase();
      let visibleCount = 0;

      items.forEach((item) => {
        const matches = query === '' || item.dataset.searchText.includes(query);
        item.hidden = !matches;
        if (matches) visibleCount += 1;
        if (query !== '' && matches) item.open = true;
        if (query === '') item.open = item.hasAttribute('data-open-by-default');
      });

      groups.forEach((group) => {
        const groupItems = [...group.querySelectorAll('[data-hwfaq-item]')];
        group.hidden = !groupItems.some((item) => !item.hidden);
      });

      if (empty) empty.hidden = visibleCount !== 0;
    });
  });
})();
