/* Live2D 看板娘：库与模型全部自托管（同源 + Cloudflare CDN），页面加载完后再启动，不抢首屏带宽 */
(function () {
  function boot() {
    if (!window.OML2D || typeof window.OML2D.loadOml2d !== 'function') return;
    window.OML2D.loadOml2d({
      dockedPosition: 'right',
      models: [
        {
          path: '/assets/models/Hiyori/Hiyori.model3.json',
          scale: 0.08,
          position: [0, 60]
        },
        {
          path: '/assets/models/chino/model.json',
          scale: 0.15,
          position: [0, 60]
        },
        {
          path: '/assets/models/Senko_Normals/senko.model3.json',
          scale: 0.1,
          position: [0, 60]
        },
        {
          path: '/assets/models/koharu/model.json',
          scale: 0.15,
          position: [0, 60]
        }
      ]
    });
  }

  function start() {
    const s = document.createElement('script');
    s.src = '/assets/js/oml2d.min.js';
    s.onload = boot;
    s.onerror = function () { /* 加载失败：看板娘缺席，主站不受影响 */ };
    document.head.appendChild(s);
  }

  // 首屏渲染完成后再启动，延迟 600ms 完全错开关键资源
  if (document.readyState === 'complete') {
    setTimeout(start, 600);
  } else {
    window.addEventListener('load', () => setTimeout(start, 600));
  }
})();
