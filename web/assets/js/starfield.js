/* 主题化氛围层：暗色=星空+流星雨+鼠标轨迹，浅色=樱花飘落。尊重系统减动效设置 */
(function () {
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

  const c = document.createElement('canvas');
  c.id = 'starfield';
  const ctx = c.getContext('2d');
  function size() { c.width = innerWidth; c.height = innerHeight; }
  size();
  addEventListener('resize', size);
  Object.assign(c.style, { position: 'fixed', inset: '0', zIndex: '-1', pointerEvents: 'none' });
  document.body.prepend(c);

  const isLight = () => document.documentElement.getAttribute('data-theme') === 'light';

  // 暗色：闪烁背景星
  const stars = Array.from({ length: 140 }, () => ({
    x: Math.random(),
    y: Math.random(),
    r: Math.random() * 1.2 + 0.3,
    tw: Math.random() * Math.PI * 2,
    sp: Math.random() * 0.02 + 0.005
  }));

  // 暗色：从上往下落的四芒小星星
  const fall = [];

  // 浅色：樱花花瓣
  const petals = Array.from({ length: 16 }, () => ({
    x: Math.random(),
    y: Math.random(),
    s: Math.random() * 3 + 4,
    rot: Math.random() * Math.PI * 2,
    rs: (Math.random() - 0.5) * 0.03,
    vy: Math.random() * 0.6 + 0.35,
    sway: Math.random() * 1.4 + 0.4,
    ph: Math.random() * Math.PI * 2
  }));

  // 暗色：偶发的大流星（带长尾巴）
  let meteors = [];
  let nextMeteor = 1500 + Math.random() * 3000;

  let trail = [];
  let last = 0;

  // 四芒星光
  function sparkle(x, y, r, a) {
    ctx.beginPath();
    ctx.moveTo(x, y - r);
    ctx.quadraticCurveTo(x, y, x + r, y);
    ctx.quadraticCurveTo(x, y, x, y + r);
    ctx.quadraticCurveTo(x, y, x - r, y);
    ctx.quadraticCurveTo(x, y, x, y - r);
    ctx.fillStyle = `rgba(228, 232, 252, ${a})`;
    ctx.fill();
  }

  addEventListener('mousemove', (e) => {
    trail.push({ x: e.clientX, y: e.clientY, life: 1 });
    if (trail.length > 50) trail.shift();
  });

  function frame(now) {
    const dt = Math.min(now - last || 16, 50);
    last = now;
    const light = isLight();
    ctx.clearRect(0, 0, c.width, c.height);

    if (light) {
      // 浅色：樱花花瓣
      for (const p of petals) {
        p.y += (p.vy * dt) / 16;
        p.x += Math.sin(now / 1000 * p.sway + p.ph) * 0.4;
        p.rot += p.rs;
        if (p.y * c.height > c.height + 10) { p.y = -0.02; p.x = Math.random(); }
        if (p.x * c.width > c.width + 10) p.x = -0.02;
        ctx.save();
        ctx.translate(p.x * c.width, p.y * c.height);
        ctx.rotate(p.rot);
        ctx.beginPath();
        ctx.ellipse(0, 0, p.s, p.s * 0.55, 0, 0, 7);
        ctx.fillStyle = 'rgba(233, 156, 180, 0.5)';
        ctx.fill();
        ctx.restore();
      }
      trail = trail.filter((p) => p.life > 0);
      for (const p of trail) {
        p.life -= 0.03;
        p.y -= 0.3;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.life * 2.2, 0, 7);
        ctx.fillStyle = `rgba(214, 130, 160, ${p.life * 0.4})`;
        ctx.fill();
      }
    } else {
      // 背景星星闪烁
      for (const s of stars) {
        s.tw += s.sp;
        const a = 0.22 + Math.abs(Math.sin(s.tw)) * 0.5;
        ctx.beginPath();
        ctx.arc(s.x * c.width, s.y * c.height, s.r, 0, 7);
        ctx.fillStyle = `rgba(224, 226, 240, ${a})`;
        ctx.fill();
      }

      // 星落：小星星持续从顶部掉下来
      if (fall.length < 22 && Math.random() < 0.1) {
        fall.push({
          x: Math.random() * c.width,
          y: -8,
          vy: (Math.random() * 1.1 + 0.6) * (dt / 16),
          ph: Math.random() * 6,
          sway: 6 + Math.random() * 14,
          r: Math.random() * 2.4 + 1.6
        });
      }
      for (let i = fall.length - 1; i >= 0; i--) {
        const f = fall[i];
        f.y += f.vy;
        f.ph += 0.03;
        if (f.y > c.height + 12) { fall.splice(i, 1); continue; }
        const x = f.x + Math.sin(f.ph) * f.sway;
        sparkle(x, f.y, f.r * 2, 0.5 + Math.abs(Math.sin(f.ph * 2)) * 0.4);
      }

      // 大流星：偶发划过
      nextMeteor -= dt;
      if (nextMeteor <= 0) {
        nextMeteor = 2500 + Math.random() * 4000;
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

      // 鼠标轨迹：紫色光点
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
