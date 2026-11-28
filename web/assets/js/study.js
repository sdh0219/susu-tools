/* 自习室主页：课程卡片墙。
   课程注册表 = courses.json（name 与本地 1_learning/rivew-应大/ 的目录名一致），
   资料计数 = study.json 按 course 前缀匹配。每门课进入 study/course.html?c=<slug>。 */
(function () {
  const wall = document.getElementById('courseWall');
  const countEl = document.getElementById('studyCount');
  if (!wall) return;

  Promise.all([
    fetch('/assets/data/courses.json').then((r) => r.json()),
    fetch('/assets/data/study.json').then((r) => r.json())
  ]).then(([cdata, sdata]) => {
    const courses = cdata.courses || [];
    const items = sdata.items || [];

    const tiles = courses.map((c) => {
      const mine = c.match
        ? items.filter((it) => String(it.course || '').indexOf(c.match) === 0)
        : [];
      const types = {};
      mine.forEach((it) => { types[it.type] = (types[it.type] || 0) + 1; });
      const latest = mine.length
        ? mine.map((it) => String(it.date || '')).sort().reverse()[0]
        : '';
      return { c, count: mine.length, types, latest };
    });

    const total = tiles.reduce((s, t) => s + t.count, 0);
    if (countEl) countEl.textContent = `共 ${courses.length} 门课 · ${total} 份资料`;

    wall.innerHTML = tiles.map((t) => {
      const empty = !t.count;
      const meta = empty
        ? '<span class="tile-empty-note">笔记整理中</span>'
        : `<span class="tile-count">${t.count} 份资料</span>` +
          (t.latest ? `<span class="tile-latest">最近更新 ${t.latest}</span>` : '');
      return `
      <a class="course-tile${empty ? ' course-tile--empty' : ''}" href="study/course.html?c=${encodeURIComponent(t.c.slug)}">
        <div class="tile-icon">${t.c.icon}</div>
        <h2 class="tile-name">${esc(t.c.name)}</h2>
        <div class="tile-meta">${meta}</div>
        <span class="tile-arrow">进入课程 →</span>
      </a>`;
    }).join('');
  }).catch(() => {
    wall.innerHTML = '<p class="contributors-loading">资料加载失败，刷新试试。</p>';
  });

  function esc(s) {
    return String(s).replace(/[&<>"']/g, (c) => ({
      '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    }[c]));
  }
})();
