/* 星空 + 流星 + 鼠标轨迹：单块 Canvas，仅暗色主题显示，尊重系统减动效设置 */
(function () {
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

  const c = document.createElement('canvas');
  const ctx = c.getContext('2d');
  function size() { c.width = innerWidth; c.height = innerHeight; }
  size();
  addEventListener('resize', size);
  Object.assign(c.style, { position: 'fixed', inset: '0', zIndex: '-1', pointerEvents: 'none' });
  document.body.prepend(c);

  // 背景星星：缓慢闪烁
  const stars = Array.from({ length: 140 }, () => ({
    x: Math.random(),
    y: Math.random(),
    r: Math.random() * 1.2 + 0.3,
    tw: Math.random() * Math.PI * 2,
    sp: Math.random() * 0.02 + 0.005
  }));

  let meteors = [];
  let trail = [];
  let nextMeteor = 2000 + Math.random() * 3000;
  let last = 0;

  // 鼠标轨迹：淡出的紫色小光点
  addEventListener('mousemove', (e) => {
    trail.push({ x: e.clientX, y: e.clientY, life: 1 });
    if (trail.length > 50) trail.shift();
  });

  function frame(now) {
    const dt = Math.min(now - last || 16, 50);
    last = now;
    const light = document.documentElement.getAttribute('data-theme') === 'light';
    c.style.opacity = light ? '0' : '1';   // 浅色主题下隐藏星空
    ctx.clearRect(0, 0, c.width, c.height);

    if (!light) {
      for (const s of stars) {
        s.tw += s.sp;
        const a = 0.22 + Math.abs(Math.sin(s.tw)) * 0.5;
        ctx.beginPath();
        ctx.arc(s.x * c.width, s.y * c.height, s.r, 0, 7);
        ctx.fillStyle = `rgba(224, 226, 240, ${a})`;
        ctx.fill();
      }

      // 流星：随机间隔从上方划过
      nextMeteor -= dt;
      if (nextMeteor <= 0) {
        nextMeteor = 3000 + Math.random() * 5000;
        meteors.push({
          x: Math.random() * c.width * 0.85,
          y: -20,
          vx: 4 + Math.random() * 3,
          vy: 2.5 + Math.random() * 2,
          life: 1
        });
      }
      meteors = meteors.filter((m) => m.life > 0 && m.y < c.height + 40);
      for (const m of meteors) {
        m.x += m.vx;
        m.y += m.vy;
        m.life -= 0.006;
        const tail = 16;
        const g = ctx.createLinearGradient(m.x, m.y, m.x - m.vx * tail, m.y - m.vy * tail);
        g.addColorStop(0, `rgba(205, 210, 255, ${0.9 * m.life})`);
        g.addColorStop(1, 'rgba(205, 210, 255, 0)');
        ctx.strokeStyle = g;
        ctx.lineWidth = 1.6;
        ctx.beginPath();
        ctx.moveTo(m.x, m.y);
        ctx.lineTo(m.x - m.vx * tail, m.y - m.vy * tail);
        ctx.stroke();
      }

      // 鼠标轨迹
      trail = trail.filter((p) => p.life > 0);
      for (const p of trail) {
        p.life -= 0.03;
        p.y -= 0.3;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.life * 2.2, 0, 7);
        ctx.fillStyle = `rgba(139, 110, 200, ${p.life * 0.45})`;
        ctx.fill();
      }
    }
    requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);
})();
