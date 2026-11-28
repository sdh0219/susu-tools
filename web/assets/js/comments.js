/* 评论区：giscus（GitHub Discussions 驱动）。
   - 页面只需放一个 <div id="comments"></div>
   - giscus App 未安装/网络不通时，区块内保留「去仓库讨论」的兜底说明（HTML 里已写）
   - 跟随站点主题按钮实时切换评论区配色 */
(function () {
  /* ⚠️ 开关：giscus GitHub App 已安装（2026-11-28），评论区启用 */
  var ENABLED = true;

  var CFG = {
    repo: 'sdh0219/susu-tools',
    repoId: 'R_kgDOSu58MQ',
    category: 'Announcements',
    categoryId: 'DIC_kwDOSu58Mc4DL8ba',
    mapping: 'pathname',
    strict: '0',
    reactionsEnabled: '1',
    inputPosition: 'top',
    lang: 'zh-CN'
  };

  function siteTheme() {
    var t = document.documentElement.getAttribute('data-theme');
    if (t === 'light') return 'light';
    if (t === 'dark') return 'dark';
    return 'preferred_color_scheme';
  }

  function mount() {
    var host = document.getElementById('comments');
    if (!host || host.dataset.mounted) return;
    host.dataset.mounted = '1';

    /* App 未装时不要挂 giscus（否则访客会看到它的报错框），改给一个显眼的讨论入口 */
    if (!ENABLED) {
      host.innerHTML = '<a class="btn btn-secondary" href="https://github.com/sdh0219/susu-tools/discussions" target="_blank" rel="noopener">去 GitHub 讨论区发起讨论 →</a>';
      return;
    }

    var s = document.createElement('script');
    s.src = 'https://giscus.app/client.js';
    s.async = true;
    s.crossOrigin = 'anonymous';
    var attrs = {
      'data-repo': CFG.repo,
      'data-repo-id': CFG.repoId,
      'data-category': CFG.category,
      'data-category-id': CFG.categoryId,
      'data-mapping': CFG.mapping,
      'data-strict': CFG.strict,
      'data-reactions-enabled': CFG.reactionsEnabled,
      'data-emit-metadata': '0',
      'data-input-position': CFG.inputPosition,
      'data-theme': siteTheme(),
      'data-lang': CFG.lang,
      'data-loading': 'lazy'
    };
    Object.keys(attrs).forEach(function (k) { s.setAttribute(k, attrs[k]); });
    host.appendChild(s);
  }

  /* 主题切换 → 通知所有 giscus iframe 换色 */
  function syncTheme() {
    var theme = siteTheme();
    var frames = document.querySelectorAll('iframe.giscus-frame');
    frames.forEach(function (f) {
      f.contentWindow.postMessage({ giscus: { setConfig: { theme: theme } } }, 'https://giscus.app');
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', mount);
  } else {
    mount();
  }

  new MutationObserver(syncTheme).observe(document.documentElement, {
    attributes: true,
    attributeFilter: ['data-theme']
  });
})();
