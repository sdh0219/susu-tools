/* Tool directory renderer.
 * Data source: window.SUSU_CATALOG (from assets/js/catalog-data.js,
 * generated from collections/tools.json via scripts/sync-catalog.ps1).
 */

function getCatalogTools() {
  if (window.SUSU_CATALOG && Array.isArray(window.SUSU_CATALOG.tools)) {
    return window.SUSU_CATALOG.tools;
  }
  return [];
}

function renderTools(filteredTools) {
  const grid = document.getElementById('toolGrid');
  const noResults = document.getElementById('noResults');
  if (!grid) return;

  if (filteredTools.length === 0) {
    grid.innerHTML = '';
    if (noResults) noResults.classList.add('show');
    return;
  }

  if (noResults) noResults.classList.remove('show');

  grid.innerHTML = filteredTools.map((tool, index) => `
    <a href="${tool.url}" target="_blank" rel="noopener noreferrer" class="tool-card cat-${tool.category} fade-in" style="transition-delay: ${index * 0.03}s">
      <div class="tool-card-header">
        <div class="tool-icon">${tool.icon}</div>
        <div class="tool-card-info">
          <h3>${tool.name} <span class="free-badge">${(tool.pricing === 'free') ? 'FREE' : 'TOOL'}</span></h3>
          <div class="tool-url">${String(tool.url).replace('https://', '')}</div>
        </div>
      </div>
      <p>${tool.desc}</p>
      <div class="tool-card-footer">
        <div class="tool-tags">
          ${(tool.tags || []).map(tag => `<span class="tool-tag">${tag}</span>`).join('')}
        </div>
        <div class="tool-arrow">→</div>
      </div>
    </a>
  `).join('');

  requestAnimationFrame(() => {
    grid.querySelectorAll('.fade-in').forEach(el => {
      el.classList.add('visible');
    });
  });
}

function filterTools(category, keyword) {
  let filtered = getCatalogTools().filter(t => (t.status || 'active') === 'active');

  if (category && category !== 'all') {
    filtered = filtered.filter(t => t.category === category);
  }

  if (keyword) {
    const kw = keyword.toLowerCase();
    filtered = filtered.filter(t =>
      t.name.toLowerCase().includes(kw) ||
      t.desc.toLowerCase().includes(kw) ||
      (t.tags || []).some(tag => tag.toLowerCase().includes(kw))
    );
  }

  renderTools(filtered);
}

document.addEventListener('DOMContentLoaded', () => {
  const tools = getCatalogTools();
  if (!tools.length) {
    const grid = document.getElementById('toolGrid');
    if (grid) {
      grid.innerHTML = '<p style="opacity:.7">目录数据未加载：请运行 <code>scripts/sync-catalog.ps1</code> 后刷新。</p>';
    }
    return;
  }

  renderTools(tools.filter(t => (t.status || 'active') === 'active'));

  let currentCategory = 'all';
  let currentKeyword = '';

  const filterBtns = document.querySelectorAll('.filter-btn');
  filterBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      filterBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      currentCategory = btn.dataset.filter;
      filterTools(currentCategory, currentKeyword);
    });
  });

  const searchInput = document.getElementById('toolSearch');
  if (!searchInput) return;
  let debounceTimer;
  searchInput.addEventListener('input', () => {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => {
      currentKeyword = searchInput.value.trim();
      filterTools(currentCategory, currentKeyword);
    }, 200);
  });
});
