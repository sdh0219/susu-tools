/* Live2D 看板娘：动态注入 oh-my-live2d，CDN 不可达时静默降级，不影响主站 */
(function () {
  var LIB = 'https://fastly.jsdelivr.net/npm/oh-my-live2d@0.19.3/dist/index.min.js';

  function boot() {
    if (!window.OML2D || typeof window.OML2D.loadOml2d !== 'function') return;
    window.OML2D.loadOml2d({
      position: 'right',
      models: [
        {
          path: 'https://model.hacxy.cn/HK416-1-normal/model.json',
          scale: 0.12,
          position: [0, 60]
        },
        {
          path: 'https://cdn.jsdelivr.net/gh/guansss/pixi-live2d-display/test/assets/shizuku/shizuku.model.json',
          scale: 0.08,
          position: [0, 60]
        },
        {
          path: 'https://model.hacxy.cn/cat-black/model.json',
          scale: 0.1,
          position: [0, 60]
        }
      ]
    });
  }

  var s = document.createElement('script');
  s.src = LIB;
  s.onload = boot;
  s.onerror = function () { /* CDN 不可达：看板娘缺席，主站不受影响 */ };
  document.head.appendChild(s);
})();
