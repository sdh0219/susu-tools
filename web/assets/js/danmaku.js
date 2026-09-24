/* 弹幕层：二次元站的灵魂。预设可爱弹幕循环飘过，纯展示不挡操作 */
(function () {
  const MSGS = [
    '欢迎来到我的二次元工具间！',
    '看板娘在右下角等你哦～',
    '今晚的星空也很美呢',
    '点看板娘有惊喜！',
    '樱花雨下起来啦！',
    '全部免费，白嫖党狂喜✧',
    '写代码也要元气满满！',
    '星星掉下来啦，接住！',
    '浅色主题的樱花超好看',
    '长按不时更新，常来玩呀',
    'ようこそ！欢迎来到二次元'
  ];

  const layer = document.createElement('div');
  layer.className = 'danmaku-layer';
  document.body.appendChild(layer);

  function spawn(text, gold) {
    if (layer.children.length >= 7) return;
    const el = document.createElement('span');
    el.className = 'danmaku';
    if (gold) el.classList.add('gold');
    el.textContent = text || MSGS[Math.floor(Math.random() * MSGS.length)];
    el.style.top = (8 + Math.random() * 55) + '%';
    el.style.fontSize = (13 + Math.random() * 7) + 'px';
    el.style.animationDuration = (9 + Math.random() * 8) + 's';
    el.addEventListener('animationend', () => el.remove());
    layer.appendChild(el);
  }
  // 弹幕发射台（随笔页输入框调用）
  window.susuDanmaku = { send: (text) => spawn(text, true) };
  // 弹幕输入条（随笔页）
  const dmInput = document.getElementById('dmInput');
  const dmSend = document.getElementById('dmSend');
  if (dmInput && dmSend) {
    const doSend = () => {
      const t = dmInput.value.trim();
      if (t) { window.susuDanmaku.send(t); dmInput.value = ''; }
    };
    dmSend.addEventListener('click', doSend);
    dmInput.addEventListener('keydown', (e) => { if (e.key === 'Enter') doSend(); });
  }
  // Konami 彩蛋：彩虹弹幕雨
  addEventListener('susu-rainbow', () => {
    const rainbowMsgs = ['秘技解锁！！', '你就是欧皇吧！', '✧ 彩虹弹幕雨 ✧', '隐藏要素 GET☆', '竟然真的有人会输这个'];
    let n = 0;
    const iv = setInterval(() => {
      spawn(rainbowMsgs[n % rainbowMsgs.length], true);
      if (++n >= 8) clearInterval(iv);
    }, 350);
  });

  spawn();
  setTimeout(spawn, 2000);
  setInterval(spawn, 3500 + Math.random() * 2000);
})();
