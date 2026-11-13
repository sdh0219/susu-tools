/* 思维导图页逻辑：
   fetch mindmaps.json → 渲染课程 tab → fetch 对应 md → markmap 渲染
   依赖 assets/js/markmap-bundle.js 暴露的 window.markmap（Transformer/Markmap/d3） */
(function () {
  const svg = document.getElementById('mm');
  const stage = document.getElementById('mmStage');
  const tabsEl = document.getElementById('mapTabs');
  const statusEl = document.getElementById('mmStatus');
  if (!svg || !tabsEl) return;

  // 默认展开到第 2 层（章节级）：导图全文有数百节点，展开太深会被 fit() 缩成看不清的地缝；
  // 章节级首屏干净，逐层点开阅读。「展开全部」后不自动 fit，保持当前可读缩放
  const DEFAULT_EXPAND_LEVEL = 2;
  const BASE_OPTS = { spacingVertical: 8, duration: 300, maxWidth: 320 }; // 长句节点自动换行，避免导图被拉得过宽

  let maps = [];
  let currentId = null;
  let mm = null;           // Markmap 实例（复用，setData 换数据）
  let rootTemplate = null; // 当前导图 markmap root，每次渲染前深拷贝（setData 会改写节点状态）
  let expandLevel = DEFAULT_EXPAND_LEVEL;
  let busy = false;        // 渲染互斥：渲染中忽略切换/工具条点击
  let renderTimer = null;

  const setStatus = (text) => { if (statusEl) statusEl.textContent = text; };

  function cloneRoot() {
    return JSON.parse(JSON.stringify(rootTemplate));
  }

  function countNodes(node) {
    let n = 1;
    (node.children || []).forEach((c) => { n += countNodes(c); });
    return n;
  }

  // ---------- 主题适配：svg 上挂 markmap-dark，代码块/圆点底色跟随站点深浅主题 ----------
  function applyThemeClass() {
    const dark = document.documentElement.getAttribute('data-theme') !== 'light';
    svg.classList.toggle('markmap-dark', dark);
  }

  // ---------- 渲染 ----------
  function renderMap(autoFit = true) {
    if (!rootTemplate || typeof window.markmap === 'undefined') return;
    const root = cloneRoot();
    const opts = { ...BASE_OPTS, initialExpandLevel: expandLevel };
    if (!mm) {
      // Markmap.create 内部 setData 后会自动 fit
      mm = window.markmap.Markmap.create(svg, opts, root);
    } else {
      mm.setData(root, opts);
      if (autoFit) mm.fit(); // 展开全部后不 fit：保持当前可读缩放，避免几百节点缩成一屏
    }
    applyThemeClass();
  }

  // 防抖：120ms 内的连续操作合并成一次渲染
  function scheduleRender(fn) {
    clearTimeout(renderTimer);
    renderTimer = setTimeout(() => {
      try { fn(); } finally { busy = false; }
    }, 120);
  }

  // ---------- tab ----------
  function renderTabs() {
    tabsEl.innerHTML = '';
    maps.forEach((m) => {
      const b = document.createElement('button');
      b.type = 'button';
      b.className = 'filter-btn';
      b.dataset.id = m.id;
      b.textContent = m.course;
      b.title = m.desc || '';
      b.setAttribute('aria-pressed', 'false');
      b.addEventListener('click', () => loadMap(m.id));
      tabsEl.appendChild(b);
    });
  }

  function setTabActive(id) {
    tabsEl.querySelectorAll('.filter-btn').forEach((b) => {
      const on = b.dataset.id === id;
      b.classList.toggle('active', on);
      b.setAttribute('aria-pressed', String(on));
    });
  }

  function updateUrl(id) {
    const url = new URL(location.href);
    url.searchParams.set('m', id);
    history.replaceState(null, '', url);
  }

  // ---------- 加载 & 切换 ----------
  async function loadMap(id) {
    if (busy || !maps.length) return; // 渲染中防抖，避免连点
    const meta = maps.find((m) => m.id === id) || maps[0];
    if (!meta) return;
    if (currentId === meta.id && mm) return; // 已在展示
    busy = true;
    setTabActive(meta.id);
    setStatus(`正在加载《${meta.title}》…`);
    if (stage) stage.classList.add('mm-loading');
    try {
      const res = await fetch(meta.file);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const md = await res.text();
      const { root } = new window.markmap.Transformer().transform(md);
      rootTemplate = root;
      currentId = meta.id;
      expandLevel = DEFAULT_EXPAND_LEVEL; // 切课程回到默认展开层级
      updateUrl(meta.id);
      renderMap();
      setStatus(`《${meta.title}》· ${countNodes(root)} 个节点 · 点击节点折叠/展开`);
    } catch (err) {
      setStatus(`导图加载失败：${err.message}`);
    } finally {
      busy = false;
      if (stage) stage.classList.remove('mm-loading');
    }
  }

  // ---------- 工具条 ----------
  function guard(fn) {
    return () => {
      if (busy || !rootTemplate) return;
      busy = true;
      scheduleRender(fn);
    };
  }

  function bindToolbar() {
    const actions = {
      mmFit: () => { if (mm) mm.fit(); },
      mmZoomIn: () => { if (mm) mm.rescale(1.25); },
      mmZoomOut: () => { if (mm) mm.rescale(0.8); },
      // -1 = 全展开；不 fit 保持可读缩放（几百节点 fit 会缩成一屏），用户拖拽平移看细节
      mmExpandAll: () => { expandLevel = -1; renderMap(false); setStatus('已全部展开：拖拽平移查看细节，点「适应屏幕」可看全貌'); },
      mmCollapseAll: () => { expandLevel = 1; renderMap(); }, // 1 = 只留一级
    };
    Object.keys(actions).forEach((id) => {
      const btn = document.getElementById(id);
      if (btn) btn.addEventListener('click', guard(actions[id]));
    });
  }

  // ---------- init ----------
  async function init() {
    if (typeof window.markmap === 'undefined') {
      setStatus('markmap 资源加载失败，请刷新重试');
      return;
    }
    try {
      const res = await fetch('assets/data/mindmaps.json');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      maps = data.maps || [];
    } catch (err) {
      setStatus(`mindmaps.json 加载失败：${err.message}`);
      return;
    }
    renderTabs();
    bindToolbar();

    // 主题切换时同步 markmap-dark（暗色为站点默认）
    new MutationObserver(applyThemeClass).observe(
      document.documentElement, { attributes: true, attributeFilter: ['data-theme'] }
    );

    const want = new URLSearchParams(location.search).get('m');
    const valid = want && maps.some((m) => m.id === want) ? want : (maps[0] && maps[0].id);
    await loadMap(valid);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
