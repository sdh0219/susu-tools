/* 思维导图页逻辑：
   fetch mindmaps.json → 渲染课程 tab → fetch 对应 md → markmap 渲染
   依赖 assets/js/markmap-bundle.js 暴露的 window.markmap（Transformer/Markmap/d3） */
(function () {
  const svg = document.getElementById('mm');
  const stage = document.getElementById('mmStage');
  const tabsEl = document.getElementById('mapTabs');
  const statusEl = document.getElementById('mmStatus');
  if (!svg || !tabsEl) return;

  // 点击节点文字也触发折叠/展开（markmap 默认只认圆点）。
  // 做法：文字点击 → 取该节点的数据 → 调 markmap 的公开方法 toggleNode；
  // 节点内的链接（<a>）不劫持，保留跳转。
  svg.addEventListener('click', (e) => {
    if (e.target.closest('a')) return;
    const fo = e.target.closest('foreignObject');
    if (!fo) return;
    const g = fo.closest('g.markmap-node');
    if (g && g.__data__ && mm) {
      mm.toggleNode(g.__data__);
      e.preventDefault();
    }
  });

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
      window.__mm = mm; // 调试/自动化测试用：暴露实例以便检查内部状态
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
  // fetch 白名单（字面量查表）：fetch 的地址只能从这张写死的表里取，
  // 任何 id 查不到就返回 null 直接拒绝——id 本身不参与 URL 拼接
  const MAP_FILES = {
    'numerical-computing': '/assets/mindmaps/numerical-computing.md',
    'academic-writing': '/assets/mindmaps/academic-writing.md',
    'socialism-theory': '/assets/mindmaps/socialism-theory.md',
    'innovation-entrepreneurship': '/assets/mindmaps/innovation-entrepreneurship.md',
    'comprehensive-english': '/assets/mindmaps/comprehensive-english.md',
    'rock-mineral-identification': '/assets/mindmaps/rock-mineral-identification.md',
  };
  function resolveMapFile(id) {
    return Object.prototype.hasOwnProperty.call(MAP_FILES, id) ? MAP_FILES[id] : null;
  }

  async function loadMap(id) {
    if (busy || !maps.length) return; // 渲染中防抖，避免连点
    const meta = maps.find((m) => m.id === id) || maps[0];
    if (!meta) return;
    const file = resolveMapFile(meta.id);
    if (!file) {
      setStatus('导图文件路径不合法');
      return;
    }
    if (currentId === meta.id && mm) return; // 已在展示
    busy = true;
    setTabActive(meta.id);
    setStatus(`正在加载《${meta.title}》…`);
    if (stage) stage.classList.add('mm-loading');
    try {
      const res = await fetch(file);
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

  // ---------- 全屏 ----------
  // 原生全屏在某些环境（预览 webview / 无 fullscreen 权限的 iframe）会被拒绝且静默失败，
  // 因此统一兜底成「页面内全屏」：stage 固定铺满视口，Esc 退出。
  let fauxFull = false;

  function syncFullLabel() {
    const btn = document.getElementById('mmFull');
    if (!btn) return;
    const on = fauxFull || document.fullscreenElement === stage;
    btn.textContent = on ? '✕ 退出全屏' : '⛶ 全屏';
    btn.setAttribute('aria-pressed', String(on));
  }

  function setFauxFull(on) {
    if (!stage) return;
    fauxFull = on;
    stage.classList.toggle('mm-faux-full', on);
    document.documentElement.classList.toggle('mm-faux-lock', on);
    syncFullLabel();
    // 页面内全屏遮住了工具条，给一个悬浮退出按钮
    let exitBtn = document.getElementById('mmFauxExit');
    if (on && !exitBtn) {
      exitBtn = document.createElement('button');
      exitBtn.id = 'mmFauxExit';
      exitBtn.type = 'button';
      exitBtn.className = 'mm-faux-exit';
      exitBtn.textContent = '✕ 退出全屏';
      exitBtn.addEventListener('click', () => setFauxFull(false));
      document.body.appendChild(exitBtn);
    } else if (!on && exitBtn) {
      exitBtn.remove();
    }
    setTimeout(() => { if (mm) mm.fit(); }, 150); // 画布尺寸变了，重新适应
  }

  function toggleFullscreen() {
    if (!stage) return;
    if (fauxFull) { setFauxFull(false); return; }
    if (document.fullscreenElement) { document.exitFullscreen(); return; }

    const req = stage.requestFullscreen || stage.webkitRequestFullscreen || stage.msRequestFullscreen;
    if (!req) { setFauxFull(true); return; }

    // 部分环境里 requestFullscreen 既不 resolve 也不 reject（权限策略直接吞掉），
    // 所以不只靠 promise，再加一个 350ms 看门狗：没真正进全屏就切页面内全屏。
    const fallback = () => {
      if (document.fullscreenElement !== stage && !fauxFull) {
        setFauxFull(true);
        setStatus('浏览器不允许原生全屏，已切换为页面内全屏（Esc 退出）');
      }
    };
    setTimeout(fallback, 350);
    try {
      const p = req.call(stage);
      if (p && typeof p.catch === 'function') p.catch(fallback);
    } catch (err) {
      fallback();
    }
  }

  // ---------- 导出 PDF ----------
  // 克隆画布里的 SVG（保留当前展开状态），清掉平移/缩放，按内容原始尺寸生成打印视图：
  // 在系统打印对话框里选「另存为 PDF」即可。不引额外依赖，文字仍是矢量，放大不糊。
  // 用隐藏 iframe 而不是新窗口，绕开弹窗拦截。
  function exportPdf() {
    if (!svg || !mm) return;
    const meta = maps.find((m) => m.id === currentId);
    const title = (meta ? meta.title : '思维导图').replace(/[<>]/g, '');

    const clone = svg.cloneNode(true);
    clone.removeAttribute('id');
    clone.removeAttribute('style');
    clone.classList.remove('markmap-dark'); // 导出统一浅色，打印和分享都更清楚
    clone.setAttribute('xmlns', 'http://www.w3.org/2000/svg');

    // 内容包围盒取自当前节点布局（getBBox 不受平移缩放影响）
    let box = { x: 0, y: 0, width: 1200, height: 800 };
    const srcG = Array.from(svg.children).find((el) => el.tagName.toLowerCase() === 'g');
    if (srcG && typeof srcG.getBBox === 'function') {
      const b = srcG.getBBox();
      if (b.width > 0 && b.height > 0) box = b;
    }
    const pad = 48;
    const x = box.x - pad;
    const y = box.y - pad;
    const w = box.width + pad * 2;
    const h = box.height + pad * 2;

    Array.from(clone.children).forEach((el) => {
      if (el.tagName.toLowerCase() === 'g') el.removeAttribute('transform');
    });
    clone.setAttribute('viewBox', `${x} ${y} ${w} ${h}`);

    // 1 CSS px = 0.75pt：PDF 里的字号与屏幕 100% 时一致
    const wPt = Math.round(w * 0.75);
    const hPt = Math.round(h * 0.75);

    const html = `<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8">
<title>${title}</title>
<style>
  @page { size: ${wPt}pt ${hPt}pt; margin: 0; }
  html, body { margin: 0; padding: 0; background: #fff; }
  svg { display: block; width: ${wPt}pt; height: ${hPt}pt; background: #fff; }
  .markmap-node text, .markmap-foreign { fill: #1b1b1b; color: #1b1b1b; }
  .markmap-foreign * { color: inherit; }
</style></head><body>${clone.outerHTML}</body></html>`;

    const old = document.getElementById('mmPrintFrame');
    if (old) old.remove();
    const frame = document.createElement('iframe');
    frame.id = 'mmPrintFrame';
    frame.setAttribute('aria-hidden', 'true');
    frame.style.cssText = 'position:fixed;left:-10000px;top:0;width:1200px;height:900px;border:0;';
    document.body.appendChild(frame);

    let printed = false;
    frame.addEventListener('load', () => {
      if (printed) return;
      printed = true;
      setTimeout(() => {
        try {
          frame.contentWindow.focus();
          frame.contentWindow.print();
          setStatus('打印对话框已打开：选「另存为 PDF」即可保存');
        } catch (err) {
          setStatus(`导出失败：${err.message}`);
        }
      }, 300);
    });

    const doc = frame.contentWindow.document;
    doc.open();
    doc.write(html);
    doc.close();
  }

  function bindToolbar() {
    const actions = {
      mmFit: () => { if (mm) mm.fit(); },
      mmZoomIn: () => { if (mm) mm.rescale(1.25); },
      mmZoomOut: () => { if (mm) mm.rescale(0.8); },
      // -1 = 全展开；不 fit 保持可读缩放（几百节点 fit 会缩成一屏），用户拖拽平移看细节
      mmExpandAll: () => { expandLevel = -1; renderMap(false); setStatus('已全部展开：用上方按钮缩放或收起，点「适应屏幕」看全貌'); },
      mmCollapseAll: () => { expandLevel = 1; renderMap(); }, // 1 = 只留一级
    };
    Object.keys(actions).forEach((id) => {
      const btn = document.getElementById(id);
      if (btn) btn.addEventListener('click', guard(actions[id]));
    });
    // 全屏 / 导出不走渲染互斥，必须同步响应点击（弹窗需要用户手势）
    const fullBtn = document.getElementById('mmFull');
    if (fullBtn) fullBtn.addEventListener('click', toggleFullscreen);
    const pdfBtn = document.getElementById('mmPdf');
    if (pdfBtn) pdfBtn.addEventListener('click', exportPdf);
    document.addEventListener('fullscreenchange', () => {
      if (document.fullscreenElement === stage && fauxFull) setFauxFull(false); // 原生全屏生效，撤掉兜底样式
      syncFullLabel();
      setTimeout(() => { if (mm) mm.fit(); }, 150); // 画布尺寸变了，重新适应
    });
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && fauxFull) setFauxFull(false);
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

    const want = new URL(location.href).searchParams.get('m');
    // 深链 ?m= 只做一件事：模拟点击对应的 tab 按钮——
    // 加载统一走 tab 点击的既有链路（与手动点击完全相同），URL 参数不直接进入加载函数
    const wantedTab = want
      ? [...tabsEl.querySelectorAll('.filter-btn')].find((b) => b.dataset.id === want)
      : null;
    if (wantedTab) wantedTab.click();
    else await loadMap(maps[0]?.id);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
