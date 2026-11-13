/* 自习室：读取 study.json，按课程分组渲染卡片 + 搜索/筛选 */
(function () {
  const groupsEl = document.getElementById('studyGroups');
  const empty = document.getElementById('studyEmpty');
  const countEl = document.getElementById('studyCount');
  const searchInput = document.getElementById('studySearch');
  const filterBar = document.getElementById('studyFilters');
  if (!groupsEl) return;

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

  // 按课程分组：items 已按日期倒序，Map 的插入顺序即「最近有更新的课程在前」
  function groupOf(list) {
    const map = new Map();
    list.forEach((it) => {
      const key = it.course || '未分类';
      if (!map.has(key)) map.set(key, []);
      map.get(key).push(it);
    });
    return Array.from(map.entries());
  }

  function groupMeta(list) {
    return Object.keys(TYPES)
      .map((k) => [TYPES[k].label, list.filter((it) => it.type === k).length])
      .filter(([, n]) => n > 0)
      .map(([label, n]) => `${n} 份${label}`)
      .join(' · ');
  }

  function render() {
    const list = items.filter(match);
    const groups = groupOf(list);

    if (countEl) {
      if (!items.length) countEl.textContent = '';
      else if (list.length === items.length) {
        countEl.textContent = `共 ${items.length} 份 · ${groups.length} 门课`;
      } else countEl.textContent = `${list.length} / ${items.length} 份`;
    }

    if (!list.length) {
      groupsEl.innerHTML = '';
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
    groupsEl.innerHTML = groups.map(([course, group]) => {
      const semester = group.find((it) => it.semester);
      return `
      <section class="course-group">
        <div class="course-head">
          <h2>${esc(course)}</h2>
          <div class="course-meta">
            ${semester ? `<span class="course-semester">${esc(semester.semester)}</span>` : ''}
            <span>${groupMeta(group)}</span>
          </div>
        </div>
        <div class="tool-grid">${group.map(card).join('')}</div>
      </section>`;
    }).join('');
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
