/* Live2D 看板娘：自托管库与模型；点击模型会说话（气泡 + Web Speech 中文语音播报） */
(function () {
  const PHRASES = [
    '今天也要元气满满哦！',
    '代码写累了，就休息一下嘛～',
    '偷偷告诉你，右上角的小太阳可以切换浅色主题！',
    '浅色主题里会下樱花雨，快去看看呀！',
    '发现页面坏掉了？邮件告诉主人哦！',
    '工具用得顺手的话，给项目点颗小星星嘛～',
    '博客里有新的随笔，去读读嘛～',
    '主人主人，今天也要开心哦！'
  ];
  const GREETING = '你好呀，我是这里的看板娘，点点我会有惊喜哦！';

  function boot() {
    if (!window.OML2D || typeof window.OML2D.loadOml2d !== 'function') return;
    const oml2d = window.OML2D.loadOml2d({
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
      ],
      tips: {
        idleTips: {
          wordTheDay: false,
          message: PHRASES.slice(0, 5),
          duration: 3500,
          interval: 9000,
          priority: 2
        }
      }
    });

    // ---- 语音播报：优先播放预录甜美音色 mp3（assets/voice/p1..p8.mp3）----
    // 文件缺失时只显示气泡、不出声——绝不回退到机械的系统 TTS
    const audioCache = {};
    function playVoiceFile(index) {
      return new Promise((resolve) => {
        const file = '/assets/voice/p' + index + '.mp3';
        if (audioCache[index] !== undefined) {
          const a = audioCache[index].cloneNode();
          a.onended = () => resolve(true);
          a.onerror = () => resolve(false);
          a.play().catch(() => resolve(false));
          return;
        }
        const a = new Audio(file);
        audioCache[index] = a;
        a.onended = () => resolve(true);
        a.onerror = () => { delete audioCache[index]; resolve(false); };
        a.play().then(() => { /* 播放中 */ }).catch(() => resolve(false));
      });
    }

    // ---- 点击模型：随机说话（气泡 + 语音）----
    let lastPick = -1;
    function interact() {
      let i = Math.floor(Math.random() * PHRASES.length);
      if (i === lastPick) i = (i + 1) % PHRASES.length;
      lastPick = i;
      const text = PHRASES[i];
      if (oml2d && typeof oml2d.tipsMessage === 'function') oml2d.tipsMessage(text, 4000, 3);
      playVoiceFile(i + 1);   // 对应 assets/voice/p1..p8.mp3
    }
    document.addEventListener('click', (e) => {
      // 只响应点击模型画布本体；星空画布、按钮、菜单不触发
      if (e.target.tagName !== 'CANVAS' || e.target.id === 'starfield') return;
      if (e.target.closest('button') || e.target.closest('[class*="status"]')) return;
      interact();
    });

    // ---- 开场问候（只出气泡不发声，避免打扰）----
    setTimeout(() => {
      if (oml2d && typeof oml2d.tipsMessage === 'function') oml2d.tipsMessage(GREETING, 5000, 3);
      playVoiceFile(0);   // 对应 assets/voice/p0.mp3（可选）
    }, 2600);
  }

  function start() {
    const s = document.createElement('script');
    s.src = '/assets/js/oml2d.min.js';
    s.onload = boot;
    s.onerror = function () { /* 加载失败：看板娘缺席，主站不受影响 */ };
    document.head.appendChild(s);
  }

  if (document.readyState === 'complete') {
    setTimeout(start, 600);
  } else {
    window.addEventListener('load', () => setTimeout(start, 600));
  }
})();
