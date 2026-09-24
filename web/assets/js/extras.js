/* 二次元要素：一言 hitokoto / 今日运势签 / 音乐盒 BGM 开关 */
(function () {
  // ---------- 一言（hitokoto 社区 API）----------
  const hitoEl = document.getElementById('hitokoto');
  if (hitoEl) {
    const fallback = '总有一天，我要撕碎这片虚伪的星空。——《黑之契约者》';
    fetch('https://v1.hitokoto.cn/?c=a&c=b&c=i&encode=json')
      .then((r) => r.json())
      .then((d) => {
        hitoEl.textContent = `「${d.hitokoto}」${d.from_who ? '—— ' + d.from_who : ''}${d.from ? '《' + d.from + '》' : ''}`;
      })
      .catch(() => { hitoEl.textContent = fallback; });
  }

  // ---------- 今日运势签（おみくじ）----------
  const FORTUNES = [
    { lvl: '大吉', msg: '今天做什么都超顺利，适合把收藏夹里那个工具打开试试！', item: '樱花色的鼠标垫' },
    { lvl: '大吉', msg: '灵感会自己撞上门来，记得把想法记下来。', item: '冰镇布丁' },
    { lvl: '中吉', msg: '平稳的一天，适合整理收藏夹、写写随笔。', item: '看板娘的小围裙' },
    { lvl: '中吉', msg: '会有小惊喜藏在不起眼的角落里。', item: '热可可' },
    { lvl: '小吉', msg: '慢慢来比较快，代码也一样。', item: '樱花书签' },
    { lvl: '吉', msg: '适合听听 BGM 发发呆，休息也是生产力。', item: '猫爪鼠标垫' },
    { lvl: '末吉', msg: '遇到烦心事就切浅色主题看看樱花吧。', item: '樱花味零食' },
  ];
  const ITEMS = ['樱花', '猫爪', '布丁', '看板娘的围裙', '四芒星', '旧键盘', '草莓牛奶'];

  let fortuneEl = null;
  function showFortune() {
    if (fortuneEl) { fortuneEl.remove(); fortuneEl = null; return; }
    const f = FORTUNES[Math.floor(Math.random() * FORTUNES.length)];
    const item = ITEMS[Math.floor(Math.random() * ITEMS.length)];
    fortuneEl = document.createElement('div');
    fortuneEl.className = 'fortune-card';
    fortuneEl.innerHTML = `
      <div class="fortune-close">×</div>
      <div class="fortune-title">今日运势 · ${f.lvl}</div>
      <p class="fortune-msg">${f.msg}</p>
      <p class="fortune-item">幸运物：${item}</p>
      <p class="fortune-tip">点击任意处关闭</p>`;
    document.body.appendChild(fortuneEl);
    fortuneEl.addEventListener('click', () => { fortuneEl.remove(); fortuneEl = null; });
  }
  const fortuneBtn = document.getElementById('fortuneBtn');
  if (fortuneBtn) fortuneBtn.addEventListener('click', showFortune);

  // ---------- 音乐盒（BGM 开关，状态记忆）----------
  const musicBtn = document.getElementById('musicBtn');
  if (musicBtn && !document.getElementById('bgm-audio')) {
    const TRACKS = [
      { file: '/assets/audio/bgm-loop.mp3', name: '治愈·星夜' },
      { file: '/assets/audio/bgm-battle.mp3', name: '战斗·像素' },
      { file: '/assets/audio/bgm-pixel.mp3', name: '跳跃·8bit' },
    ];
    let trackIdx = parseInt(localStorage.getItem('susu-track') || '0', 10) % TRACKS.length;
    const audio = new Audio(TRACKS[trackIdx].file);
    audio.loop = true;
    audio.volume = 0.35;
    const setIcon = (on) => { musicBtn.textContent = on ? '🔊' : '🔇'; };
    const saved = localStorage.getItem('susu-bgm') === 'on';
    setIcon(saved);
    if (saved) audio.play().catch(() => {});
    musicBtn.addEventListener('click', () => {
      const on = musicBtn.textContent.trim() === '🔊';
      if (on) audio.pause();
      else audio.play().catch(() => {});
      localStorage.setItem('susu-bgm', on ? 'off' : 'on');
      setIcon(!on);
    });
    // 点歌：长按/双击切下一首
    musicBtn.addEventListener('dblclick', () => {
      trackIdx = (trackIdx + 1) % TRACKS.length;
      localStorage.setItem('susu-track', String(trackIdx));
      audio.src = TRACKS[trackIdx].file;
      musicBtn.title = 'BGM：' + TRACKS[trackIdx].name;
      if (localStorage.getItem('susu-bgm') === 'on') audio.play().catch(() => {});
    });
    musicBtn.title = 'BGM：' + TRACKS[trackIdx].name + '（双击切歌）';
    // 连续打卡
    const today = new Date().toDateString();
    const yest = new Date(Date.now() - 864e5).toDateString();
    const last = localStorage.getItem('susu-lastday');
    let streak = parseInt(localStorage.getItem('susu-streak') || '0', 10);
    if (last !== today) {
      streak = (last === yest) ? streak + 1 : 1;
      localStorage.setItem('susu-streak', String(streak));
      localStorage.setItem('susu-lastday', today);
    }
    const chip = document.getElementById('streakChip');
    if (chip) chip.textContent = '📅 连续打卡 ' + Math.max(streak, 1) + ' 天';
  }
})();
