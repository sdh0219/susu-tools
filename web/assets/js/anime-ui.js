/* 二次元交互层：拟声词气泡 + 音效反馈 + 花瓣爆开
   自包含：样式由本文件注入，不依赖其他脚本；新增文件，接线由各页 <script> 引入。
   静音开关：localStorage 'susu-sfx' = 'off'；window.susuSfx.toggle() 可编程切换。 */
(function () {
  // 减弱动态效果：关掉气泡与花瓣，音效保留（声音不是动效）
  const reducedMotion = matchMedia('(prefers-reduced-motion: reduce)').matches;

  // ---------- 注入样式 ----------
  const style = document.createElement('style');
  style.textContent = `
    .sfx-bubble {
      position: fixed; z-index: 400; pointer-events: none;
      background: #fff; color: #d6336c;
      border: 2px solid #d6336c; border-radius: 10px;
      padding: 2px 10px; font-size: 0.9rem; font-weight: 800;
      box-shadow: 2px 2px 0 rgba(214, 51, 108, 0.35);
      transform: translate(-50%, -130%) rotate(-4deg);
      opacity: 0; transition: opacity 0.15s ease;
      white-space: nowrap;
    }
    .sfx-bubble.show { opacity: 1; }
    .sfx-bubble::after {
      content: ''; position: absolute; left: 50%; bottom: -6px;
      transform: translateX(-50%);
      border: 6px solid transparent; border-top-color: #d6336c; border-bottom: 0;
    }
    .sfx-petal {
      position: fixed; z-index: 399; pointer-events: none;
      width: 10px; height: 10px;
      background: radial-gradient(circle at 30% 30%, #ffd7e4, #ec6f9d);
      border-radius: 100% 0 100% 0;
      animation: sfx-petal-fall 0.9s ease-in forwards;
    }
    @keyframes sfx-petal-fall {
      to { transform: translate(var(--px), var(--py)) rotate(var(--pr)); opacity: 0; }
    }
    @media (prefers-reduced-motion: reduce) {
      .sfx-petal { display: none; }
    }
  `;
  document.head.appendChild(style);

  // ---------- 音效 ----------
  const SFX = {
    pop: '/assets/audio/sfx/pop.wav',
    chime: '/assets/audio/sfx/chime.wav',
    don: '/assets/audio/sfx/don.wav',
    yoshi: '/assets/audio/sfx/yoshi.wav',
  };
  const buffers = {};
  function muted() {
    try { return localStorage.getItem('susu-sfx') === 'off'; } catch (e) { return false; }
  }
  function play(name, volume) {
    if (muted() || !SFX[name]) return;
    let audio = buffers[name];
    if (!audio) {
      audio = new Audio(SFX[name]);
      audio.preload = 'auto';
      buffers[name] = audio;
    }
    const node = audio.cloneNode();
    node.volume = volume === undefined ? 0.25 : volume;
    node.play().catch(() => { /* 自动播放被拦截时静默 */ });
  }
  window.susuSfx = {
    toggle() {
      const off = muted();
      try { localStorage.setItem('susu-sfx', off ? 'on' : 'off'); } catch (e) { /* 隐私模式忽略 */ }
      return !off; // 返回切换后的状态：true = 开
    },
    muted,
    play,
  };

  // ---------- 拟声词气泡 ----------
  const WORDS = ['ドン！', 'ヨシ！', 'ナイス！', 'すごい！', '最高！', 'オッケー！', 'ウレシイ♪', 'ファイト〜'];
  const bubble = document.createElement('div');
  bubble.className = 'sfx-bubble';
  document.body.appendChild(bubble);
  let bubbleTimer = null;
  let lastBubbleAt = 0;

  function showBubble(x, y) {
    const now = Date.now();
    if (now - lastBubbleAt < 500) return; // 节流：连续扫过不刷屏
    lastBubbleAt = now;
    bubble.textContent = WORDS[Math.floor(Math.random() * WORDS.length)];
    bubble.style.left = x + 'px';
    bubble.style.top = y + 'px';
    bubble.classList.add('show');
    clearTimeout(bubbleTimer);
    bubbleTimer = setTimeout(() => bubble.classList.remove('show'), 700);
  }

  const HOVER_SEL = '.btn, .filter-btn, .project-card, .study-card, .tool-card, .fortune-btn';
  document.addEventListener('mouseover', (e) => {
    if (reducedMotion) return;
    const el = e.target.closest(HOVER_SEL);
    if (el) showBubble(e.clientX, e.clientY);
  });

  // ---------- 点击音效 ----------
  const CLICK_SEL = '.btn, .filter-btn, .project-card, .study-card, .tool-card, .fortune-btn, .theme-toggle';
  document.addEventListener('click', (e) => {
    const el = e.target.closest(CLICK_SEL);
    if (!el) return;
    const word = el.getAttribute('data-sfx');
    play(word || 'pop');
  });

  // ---------- 花瓣爆开（主按钮专属，庆祝感）----------
  function burst(x, y) {
    if (reducedMotion) return;
    for (let i = 0; i < 6; i++) {
      const p = document.createElement('span');
      p.className = 'sfx-petal';
      const angle = (Math.PI * 2 * i) / 6 + Math.random() * 0.6;
      const dist = 26 + Math.random() * 22;
      p.style.left = x + 'px';
      p.style.top = y + 'px';
      p.style.setProperty('--px', Math.cos(angle) * dist + 'px');
      p.style.setProperty('--py', (Math.sin(angle) * dist + 26) + 'px');
      p.style.setProperty('--pr', (Math.random() * 360) + 'deg');
      document.body.appendChild(p);
      p.addEventListener('animationend', () => p.remove());
    }
  }
  document.addEventListener('click', (e) => {
    const el = e.target.closest('.btn-primary, .project-card');
    if (el) burst(e.clientX, e.clientY);
  });

  // ---------- 页脚音效开关（有 #sfxToggle 时绑定） ----------
  const sfxToggle = document.getElementById('sfxToggle');
  if (sfxToggle) {
    const sync = () => {
      const on = !muted();
      sfxToggle.textContent = on ? '🔊 音效' : '🔇 静音';
      sfxToggle.setAttribute('aria-pressed', String(on));
    };
    sync();
    sfxToggle.addEventListener('click', () => { window.susuSfx.toggle(); sync(); });
  }
})();
