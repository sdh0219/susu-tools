/* 课程子页：?c=<slug> → courses.json 定位课程 → study.json 按前缀过滤渲染该课全部资料。
   卡片样式与旧自习室一致（tool-card study-card）。 */
(function () {
  const nameEl = document.getElementById('courseName');
  const metaEl = document.getElementById('courseMeta');
  const termEl = document.getElementById('courseTerm');
  const cardsEl = document.getElementById('courseCards');
  const emptyEl = document.getElementById('courseEmpty');
  const mmCta = document.getElementById('mindmapCta');
  if (!cardsEl) return;

  const slug = new URLSearchParams(location.search).get('c') || '';

  const TYPES = {
    material: { label: '复习资料', icon: '📄', cls: 'study-material', arrow: '↓' },
    notes: { label: '课程笔记', icon: '📝', cls: 'study-notes', arrow: '↓' },
    homework: { label: '开源作业', icon: '💻', cls: 'study-homework', arrow: '↗' }
  };

  function esc(s) {
    return String(s).replace(/[&<>"']/g, (c) => ({
      '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    }[c]));
  }

  Promise.all([
    fetch('/assets/data/courses.json').then((r) => r.json()),
    fetch('/assets/data/study.json').then((r) => r.json())
  ]).then(([cdata, sdata]) => {
    const course = (cdata.courses || []).find((c) => c.slug === slug);
    if (!course) {
      nameEl.textContent = '课程不存在';
      metaEl.textContent = '检查一下链接里的课程代号，或从自习室重新进入。';
      emptyEl.classList.add('show');
      return;
    }

    document.title = course.name + ' - 自习室 - Susu';
    nameEl.textContent = course.name;
    termEl.textContent = course.term || '课程';

    /* 该课有交互思维导图时，展示专属入口 */
    if (mmCta) {
      mmCta.innerHTML = course.mindmap
        ? `<a class="btn btn-secondary" href="${esc(course.mindmap)}">🧠 本课交互思维导图 →</a>`
        : '';
    }

    const mine = (sdata.items || [])
      .filter((it) => course.match && String(it.course || '').indexOf(course.match) === 0)
      .sort((a, b) => String(b.date || '').localeCompare(String(a.date || '')));

    const typeCounts = {};
    mine.forEach((it) => { typeCounts[it.type] = (typeCounts[it.type] || 0) + 1; });
    metaEl.textContent = mine.length
      ? `${mine.length} 份资料：` +
        Object.keys(typeCounts).map((k) => `${typeCounts[k]} 份${(TYPES[k] || {}).label || k}`).join('、')
      : '暂无已上架资料';

    if (!mine.length) {
      emptyEl.classList.add('show');
      return;
    }

    cardsEl.innerHTML = mine.map(card).join('');
  }).catch(() => {
    metaEl.textContent = '资料加载失败，刷新试试。';
  });

  function card(it, i) {
    const meta = TYPES[it.type] || TYPES.material;
    const href = it.file || it.repo || '';
    const tag = href ? 'a' : 'article';
    const attrs = href
      ? (href.indexOf('http') === 0 ? ` href="${esc(href)}" target="_blank" rel="noopener"` : ` href="${esc(href)}"`)
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
})();
