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

  function spawn() {
    if (layer.children.length >= 7) return;
    const el = document.createElement('span');
    el.className = 'danmaku';
    el.textContent = MSGS[Math.floor(Math.random() * MSGS.length)];
    el.style.top = (8 + Math.random() * 55) + '%';
    el.style.fontSize = (13 + Math.random() * 7) + 'px';
    el.style.animationDuration = (9 + Math.random() * 8) + 's';
    el.addEventListener('animationend', () => el.remove());
    layer.appendChild(el);
  }

  spawn();
  setTimeout(spawn, 2000);
  setInterval(spawn, 3500 + Math.random() * 2000);
})();
