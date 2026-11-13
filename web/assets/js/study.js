/* 自习室：读取 study.json 渲染卡片 + 搜索/筛选 */
(function () {
  const grid = document.getElementById('studyGrid');
  const empty = document.getElementById('studyEmpty');
  const countEl = document.getElementById('studyCount');
  const searchInput = document.getElementById('studySearch');
  const filterBar = document.getElementById('studyFilters');
  if (!grid) return;

  const TYPES = {
    material: { label: '复习资料', icon: '📄', cls: 'study-material', arrow: '↓' },
    notes: { label: '课程笔记', icon: '📝', cls: 'study-notes', arrow: '↓' },
    homework: { label: '开源作业', icon: '💻', cls: 'study-homework', arrow: '↗' }
  };

  let items = [];
  let activeType = 'all';
  let keyword = '';

  fetch('/assets/data/study.json')
    .then((r) => r.json())
    .then((data) => {
      items = (data.items || []).slice().sort((a, b) =>
        String(b.date || '').localeCompare(String(a.date || ''))
      );
      // 完全没有数据时藏起搜索和筛选，避免"点了没反应"的假控件
      if (!items.length) {
        const toolbar = searchInput ? searchInput.closest('.tool-search') : null;
        if (toolbar) toolbar.style.display = 'none';
        if (filterBar) filterBar.style.display = 'none';
      }
      render();
    })
    .catch(() => {
      items = [];
      render();
    });

  if (filterBar) {
    filterBar.addEventListener('click', (e) => {
      const btn = e.target.closest('.filter-btn');
      if (!btn) return;
      activeType = btn.dataset.type || 'all';
      filterBar.querySelectorAll('.filter-btn').forEach((b) => {
        const on = b === btn;
        b.classList.toggle('active', on);
        b.setAttribute('aria-pressed', String(on));
      });
      render();
    });
  }

  if (searchInput) {
    searchInput.addEventListener('input', () => {
      keyword = searchInput.value.trim().toLowerCase();
      render();
    });
  }

  function match(it) {
    if (activeType !== 'all' && it.type !== activeType) return false;
    if (!keyword) return true;
    const hay = [it.title, it.course, it.desc, it.format, it.semester, (it.tags || []).join(' ')]
      .filter(Boolean).join(' ').toLowerCase();
    return hay.includes(keyword);
  }

  function render() {
    const list = items.filter(match);

    if (countEl) {
      if (!items.length) countEl.textContent = '';
      else if (list.length === items.length) countEl.textContent = `共 ${items.length} 份`;
      else countEl.textContent = `${list.length} / ${items.length} 份`;
    }

    if (!list.length) {
      grid.innerHTML = '';
      if (empty) {
        empty.classList.add('show');
        const h3 = empty.querySelector('h3');
        const p = empty.querySelector('p');
        if (items.length) {
          if (h3) h3.textContent = '没找到';
          if (p) p.textContent = '换个关键词或筛选试试～';
        } else {
          if (h3) h3.textContent = '自习室还在布置';
          if (p) p.textContent = '资料整理好就陆续放上来。';
        }
      }
      return;
    }

    if (empty) empty.classList.remove('show');
    grid.innerHTML = list.map(card).join('');
  }

  function card(it, i) {
    const meta = TYPES[it.type] || TYPES.material;
    const href = it.file || it.repo || '';
    const tag = href ? 'a' : 'article';
    // 内部页面（/notes/、/mindmap.html）当前页打开；外部链接新标签页
    const attrs = href
      ? (href.startsWith('http') ? ` href="${esc(href)}" target="_blank" rel="noopener"` : ` href="${esc(href)}"`)
      : '';
    const plain = href ? '' : ' study-card--plain';
    const subtitle = [it.course, it.semester].filter(Boolean).map(esc).join(' · ');
    const tags = [it.format, it.size].concat(it.tags || [], it.date ? [it.date] : [])
      .filter(Boolean)
      .map((t) => `<span class="tool-tag">${esc(t)}</span>`)
      .join('');

    return `
      <${tag} class="tool-card study-card ${meta.cls}${plain}"${attrs} style="animation-delay:${Math.min(i, 8) * 40}ms">
        <div class="tool-card-header">
          <div class="tool-icon">${meta.icon}</div>
          <div class="tool-card-info">
            <h3>${esc(it.title)} <span class="study-badge">${meta.label}</span></h3>
            ${subtitle ? `<div class="tool-url">${subtitle}</div>` : ''}
          </div>
        </div>
        <p>${esc(it.desc || '')}</p>
        <div class="tool-card-footer">
          <div class="tool-tags">${tags}</div>
          ${href ? `<span class="tool-arrow">${meta.arrow}</span>` : ''}
        </div>
      </${tag}>`;
  }

  function esc(s) {
    return String(s).replace(/[&<>"']/g, (c) => ({
      '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    }[c]));
  }
})();
