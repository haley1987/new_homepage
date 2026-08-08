(() => {
  const slugify = (value) => value
    .toLowerCase()
    .trim()
    .replace(/&/g, 'and')
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-|-$/g, '');

  document.querySelectorAll('[data-hwrp]').forEach((root) => {
    const policy = root.querySelector('[data-hwrp-policy]');
    const nav = root.querySelector('[data-hwrp-nav]');
    if (!policy || !nav) return;

    const headings = [...policy.querySelectorAll('h2')];
    const usedIds = new Set();

    headings.forEach((heading, index) => {
      const baseId = slugify(heading.textContent) || `policy-section-${index + 1}`;
      let id = baseId;
      let count = 2;
      while (usedIds.has(id)) {
        id = `${baseId}-${count}`;
        count += 1;
      }
      usedIds.add(id);
      heading.id = id;

      const link = document.createElement('a');
      link.href = `#${id}`;
      link.textContent = heading.textContent.trim();
      nav.appendChild(link);
    });

    if (!('IntersectionObserver' in window) || headings.length === 0) return;

    const links = [...nav.querySelectorAll('a')];
    const observer = new IntersectionObserver((entries) => {
      const visible = entries
        .filter((entry) => entry.isIntersecting)
        .sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top)[0];
      if (!visible) return;

      links.forEach((link) => {
        if (link.hash === `#${visible.target.id}`) link.setAttribute('aria-current', 'true');
        else link.removeAttribute('aria-current');
      });
    }, { rootMargin: '-18% 0px -68% 0px', threshold: 0 });

    headings.forEach((heading) => observer.observe(heading));
  });
})();
