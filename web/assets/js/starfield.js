/* 主题化氛围层：暗色=星空+星落+流星+鼠标轨迹，浅色=樱花飘落+粉色轨迹 */
(function () {
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
  const stars = Array.from({ length: 150 }, () => ({
    x: Math.random(),
    y: Math.random(),
    r: Math.random() * 1.3 + 0.4,
    tw: Math.random() * Math.PI * 2,
    sp: Math.random() * 0.02 + 0.005
  }));

  // 暗色：从上往下掉的四芒小星星
  const fall = [];

  // 浅色：樱花花瓣（大而慢，带翻转）
  const petals = Array.from({ length: 18 }, () => ({
    x: Math.random(),
    y: Math.random(),
    r: Math.random() * 8 + 9,
    rot: Math.random() * Math.PI * 2,
    rs: (Math.random() - 0.5) * 0.04,
    vy: Math.random() * 0.35 + 0.15,
    swayA: Math.random() * 30 + 15,
    swayS: Math.random() * 0.8 + 0.4,
    ph: Math.random() * Math.PI * 2,
    fs: Math.random() * 1.2 + 0.6,
    fp: Math.random() * Math.PI * 2
  }));

  // 暗色：偶发长尾大流星
  let meteors = [];
  let nextMeteor = 1000 + Math.random() * 2500;

  // 鼠标轨迹
  let trail = [];
  let lastMx = null, lastMy = null;

  let last = 0;

  // 四芒星光
  function sparkle(x, y, r, a) {
    ctx.beginPath();
    ctx.moveTo(x, y - r);
    ctx.quadraticCurveTo(x, y, x + r, y);
    ctx.quadraticCurveTo(x, y, x, y + r);
    ctx.quadraticCurveTo(x, y, x - r, y);
    ctx.quadraticCurveTo(x, y, x, y - r);
    ctx.fillStyle = 'rgba(232, 236, 255, ' + a + ')';
    ctx.fill();
  }

  addEventListener('mousemove', (e) => {
    // 在上一点与当前点之间插值，保证轨迹连续
    if (lastMx !== null) {
      const dx = e.clientX - lastMx;
      const dy = e.clientY - lastMy;
      const steps = Math.min(Math.ceil(Math.hypot(dx, dy) / 8), 12);
      for (let i = 1; i <= steps; i++) {
        trail.push({
          x: lastMx + (dx * i) / steps,
          y: lastMy + (dy * i) / steps,
          life: 1
        });
      }
    }
    lastMx = e.clientX;
    lastMy = e.clientY;
    if (trail.length > 90) trail.splice(0, trail.length - 90);
  });

  function frame(now) {
    try {
      const dt = Math.min(now - last || 16, 50);
      last = now;
      const light = isLight();
      c.style.zIndex = light ? '30' : '-1';
      ctx.clearRect(0, 0, c.width, c.height);

      if (light) {
        // 樱花花瓣：带缺口的心形樱瓣，翻转飘落
        for (const p of petals) {
          p.y += (p.vy * dt) / 16;
          p.rot += p.rs;
          if (p.y * c.height > c.height + 24) { p.y = -0.04; p.x = Math.random(); }
          const x = p.x * c.width + Math.sin(now / 1000 * p.swayS + p.ph) * p.swayA;
          const y = p.y * c.height;
          const flip = 0.35 + 0.65 * Math.abs(Math.sin(now / 1000 * p.fs + p.fp));
          ctx.save();
          ctx.translate(x, y);
          ctx.rotate(p.rot);
          ctx.scale(flip, 1);
          const g = ctx.createLinearGradient(0, -p.r, 0, p.r);
          g.addColorStop(0, 'rgba(252, 214, 226, 0.9)');
          g.addColorStop(1, 'rgba(247, 158, 190, 0.78)');
          ctx.fillStyle = g;
          ctx.beginPath();
          ctx.moveTo(0, p.r);
          ctx.bezierCurveTo(-p.r * 1.15, p.r * 0.55, -p.r * 1.05, -p.r * 0.55, -p.r * 0.22, -p.r * 0.8);
          ctx.quadraticCurveTo(0, -p.r * 0.55, p.r * 0.22, -p.r * 0.8);
          ctx.bezierCurveTo(p.r * 1.05, -p.r * 0.55, p.r * 1.15, p.r * 0.55, 0, p.r);
          ctx.closePath();
          ctx.fill();
          ctx.restore();
        }
        // 粉色鼠标轨迹
        trail = trail.filter((p) => p.life > 0);
        for (const p of trail) {
          p.life -= 0.018;
          p.y -= 0.3;
          ctx.beginPath();
          ctx.arc(p.x, p.y, p.life * 3.2, 0, 7);
          ctx.fillStyle = 'rgba(230, 120, 165, ' + p.life * 0.55 + ')';
          ctx.fill();
        }
      } else {
        // 背景星星
        for (const s of stars) {
          s.tw += s.sp;
          const a = 0.3 + Math.abs(Math.sin(s.tw)) * 0.55;
          ctx.beginPath();
          ctx.arc(s.x * c.width, s.y * c.height, s.r, 0, 7);
          ctx.fillStyle = 'rgba(226, 229, 248, ' + a + ')';
          ctx.fill();
        }

        // 星落：四芒小星星从顶部持续掉落
        if (fall.length < 30 && Math.random() < 0.18) {
          fall.push({
            x: Math.random() * c.width,
            y: -10,
            vy: (Math.random() * 1.2 + 0.8) * (dt / 16),
            ph: Math.random() * 6,
            sway: 8 + Math.random() * 16,
            r: Math.random() * 2.6 + 2
          });
        }
        for (let i = fall.length - 1; i >= 0; i--) {
          const f = fall[i];
          f.y += f.vy;
          f.ph += 0.03;
          if (f.y > c.height + 14) { fall.splice(i, 1); continue; }
          const x = f.x + Math.sin(f.ph) * f.sway;
          sparkle(x, f.y, f.r * 2.2, 0.65 + Math.abs(Math.sin(f.ph * 2)) * 0.35);
        }

        // 大流星：长尾划过
        nextMeteor -= dt;
        if (nextMeteor <= 0) {
          nextMeteor = 1200 + Math.random() * 2500;
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
          m.life -= 0.005;
          const tail = 18;
          const g = ctx.createLinearGradient(m.x, m.y, m.x - m.vx * tail, m.y - m.vy * tail);
          g.addColorStop(0, 'rgba(210, 214, 255, ' + 0.95 * m.life + ')');
          g.addColorStop(1, 'rgba(210, 214, 255, 0)');
          ctx.strokeStyle = g;
          ctx.lineWidth = 2;
          ctx.beginPath();
          ctx.moveTo(m.x, m.y);
          ctx.lineTo(m.x - m.vx * tail, m.y - m.vy * tail);
          ctx.stroke();
        }

        // 紫色鼠标轨迹
        trail = trail.filter((p) => p.life > 0);
        for (const p of trail) {
          p.life -= 0.014;
          p.y -= 0.25;
          ctx.beginPath();
          ctx.arc(p.x, p.y, p.life * 3, 0, 7);
          ctx.fillStyle = 'rgba(150, 115, 225, ' + p.life * 0.6 + ')';
          ctx.fill();
        }
      }
    } catch (e) { /* 单帧异常不终止动画循环 */ }
    requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);
})();
