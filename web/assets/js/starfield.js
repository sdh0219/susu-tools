/* 氛围层：按季节+主题自动切换
   暗色：星空 + 季节粒子(春星落/夏萤火虫/秋红叶/冬雪) + 流星 + 紫色轨迹
   浅色：季节粒子(春樱花/夏萤火虫/秋红叶/冬雪) + 粉色轨迹
   支持 susu-rainbow 事件：20 秒彩虹星雨（Konami 彩蛋） */
(function () {
  const c = document.createElement('canvas');
  c.id = 'starfield';
  const ctx = c.getContext('2d');
  function size() { c.width = innerWidth; c.height = innerHeight; }
  size();
  addEventListener('resize', size);
  Object.assign(c.style, { position: 'fixed', inset: '0', zIndex: '-1', pointerEvents: 'none', transition: 'opacity .35s ease' });
  document.body.prepend(c);

  const isLight = () => document.documentElement.getAttribute('data-theme') === 'light';
  const MONTH = new Date().getMonth() + 1;
  const SEASON = (MONTH === 12 || MONTH <= 2) ? 'winter'
    : (MONTH <= 4) ? 'spring'
    : (MONTH >= 6 && MONTH <= 8) ? 'summer'
    : (MONTH >= 9 && MONTH <= 11) ? 'autumn' : 'spring';

  // Konami 彩蛋：彩虹模式（20 秒）
  let rainbowUntil = 0;
  addEventListener('susu-rainbow', () => { rainbowUntil = performance.now() + 20000; });

  const stars = Array.from({ length: 150 }, () => ({
    x: Math.random(), y: Math.random(),
    r: Math.random() * 1.3 + 0.4,
    tw: Math.random() * Math.PI * 2, sp: Math.random() * 0.02 + 0.005
  }));

  // 季节粒子（冬季雪 / 春樱花 / 秋红叶）
  const seasonParts = [];
  if (SEASON === 'winter') { for (let i = 0; i < 70; i++) seasonParts.push({ kind: 'snow' }); }
  else if (SEASON === 'spring') { for (let i = 0; i < 18; i++) seasonParts.push({ kind: 'petal' }); }
  else if (SEASON === 'autumn') { for (let i = 0; i < 18; i++) seasonParts.push({ kind: 'leaf' }); }
  for (const p of seasonParts) {
    p.x = Math.random(); p.y = Math.random();
    p.r = p.kind === 'snow' ? Math.random() * 2 + 1.2 : Math.random() * 8 + 9;
    p.rot = Math.random() * 6.28;
    p.rs = (Math.random() - 0.5) * 0.04;
    p.vy = Math.random() * 0.35 + 0.15;
    p.swayA = Math.random() * 30 + 12;
    p.swayS = Math.random() * 0.8 + 0.4;
    p.ph = Math.random() * 6.28;
    p.fs = Math.random() * 1.2 + 0.6;
  }
  // 夏季萤火虫
  const flies = Array.from({ length: 14 }, () => ({
    x: Math.random(), y: Math.random() * 0.7 + 0.1,
    ph: Math.random() * 6.28, sp: Math.random() * 0.9 + 0.3,
    ax: Math.random() * 40 + 20, ay: Math.random() * 24 + 12
  }));

  let meteors = [];
  let nextMeteor = 1000 + Math.random() * 2500;
  let trail = [], bursts = [];
  let lastMx = null, lastMy = null;
  let last = 0;
  let rainbowHue = 0;

  function sparkle(x, y, r, color, a) {
    ctx.beginPath();
    ctx.moveTo(x, y - r); ctx.quadraticCurveTo(x, y, x + r, y);
    ctx.quadraticCurveTo(x, y, x, y + r);
    ctx.quadraticCurveTo(x, y, x - r, y);
    ctx.quadraticCurveTo(x, y, x, y - r);
    ctx.fillStyle = color.replace('$A', a);
    ctx.fill();
  }

  function petalShape(x, y, r, rot, colors, flip) {
    ctx.save();
    ctx.translate(x, y); ctx.rotate(rot); ctx.scale(flip, 1);
    const g = ctx.createLinearGradient(0, -r, 0, r);
    g.addColorStop(0, colors[0]); g.addColorStop(1, colors[1]);
    ctx.fillStyle = g;
    ctx.beginPath();
    ctx.moveTo(0, r);
    ctx.bezierCurveTo(-r * 1.15, r * 0.55, -r * 1.05, -r * 0.55, -r * 0.22, -r * 0.8);
    ctx.quadraticCurveTo(0, -r * 0.55, r * 0.22, -r * 0.8);
    ctx.bezierCurveTo(r * 1.05, -r * 0.55, r * 1.15, r * 0.55, 0, r);
    ctx.closePath(); ctx.fill();
    ctx.restore();
  }

  addEventListener('mousemove', (e) => {
    if (lastMx !== null) {
      const dx = e.clientX - lastMx, dy = e.clientY - lastMy;
      const steps = Math.min(Math.ceil(Math.hypot(dx, dy) / 8), 12);
      for (let i = 1; i <= steps; i++) {
        trail.push({ x: lastMx + dx * i / steps, y: lastMy + dy * i / steps, life: 1 });
      }
    }
    lastMx = e.clientX; lastMy = e.clientY;
    if (trail.length > 90) trail.splice(0, trail.length - 90);
  });

  addEventListener('click', (e) => {
    if (e.target.id === 'starfield') return;
    if (e.target.closest('button') || e.target.closest('a') || e.target.closest('input')) return;
    if (!e.target.closest('.hero') && e.target.tagName !== 'CANVAS' && !e.target.closest('body > .danmaku-layer')) {
      if (e.target.closest('.project-card') || e.target.closest('section') || e.target.closest('article')) {
        // 页面内容区域内的点击也触发爆裂（外链新标签不受影响）
      } else {
        return;
      }
    }
    for (let i = 0; i < 12; i++) {
      const ang = (i / 12) * Math.PI * 2 + Math.random() * 0.5;
      const sp = 1.5 + Math.random() * 2;
      bursts.push({ x: e.clientX, y: e.clientY, vx: Math.cos(ang) * sp, vy: Math.sin(ang) * sp - 0.6, life: 1, heart: isLight() });
    }
  });

  function frame(now) {
    try {
      const dt = Math.min(now - last || 16, 50);
      last = now;
      const light = isLight();
      const rainbow = now < rainbowUntil;
      if (rainbow) rainbowHue = (rainbowHue + dt * 0.18) % 360;
      ctx.clearRect(0, 0, c.width, c.height);

      if (light) {
        for (const p of seasonParts) {
          p.y += (p.vy * dt) / 16;
          const sway = Math.sin(now / 1000 * p.swayS + p.ph);
          p.rot += p.rs;
          if (p.y * c.height > c.height + 24) { p.y = -0.04; p.x = Math.random(); }
          if (p.kind === 'snow') {
            const x = p.x * c.width + sway * 14;
            ctx.beginPath();
            ctx.arc(x, p.y * c.height, p.r, 0, 7);
            ctx.fillStyle = 'rgba(190, 205, 230, 0.7)';
            ctx.fill();
          } else if (p.kind === 'petal') {
            const x = p.x * c.width + sway * p.swayA;
            const flip = 0.35 + 0.65 * Math.abs(Math.sin(now / 1000 * p.fs + p.ph));
            petalShape(x, p.y * c.height, p.r, p.rot, ['rgba(252,214,226,0.9)', 'rgba(247,158,190,0.78)'], flip);
          } else {
            const x = p.x * c.width + sway * p.swayA;
            const flip = 0.4 + 0.6 * Math.abs(Math.sin(now / 1000 * p.fs + p.ph));
            petalShape(x, p.y * c.height, p.r * 0.8, p.rot, ['rgba(250,190,120,0.9)', 'rgba(225,110,60,0.85)'], flip);
          }
        }
        trail = trail.filter((p) => p.life > 0);
        for (const p of trail) {
          p.life -= 0.018; p.y -= 0.3;
          ctx.beginPath();
          ctx.arc(p.x, p.y, p.life * 3.2, 0, 7);
          ctx.fillStyle = 'rgba(230, 120, 165, ' + p.life * 0.55 + ')';
          ctx.fill();
        }
      } else {
        for (const s of stars) {
          s.tw += s.sp;
          const a = 0.3 + Math.abs(Math.sin(s.tw)) * 0.55;
          ctx.beginPath();
          ctx.arc(s.x * c.width, s.y * c.height, s.r, 0, 7);
          ctx.fillStyle = 'rgba(226, 229, 248, ' + a + ')';
          ctx.fill();
        }
        if (SEASON === 'winter') {
          for (const p of seasonParts) {
            p.y += (p.vy * dt) / 16;
            const sway = Math.sin(now / 1000 * p.swayS + p.ph);
            if (p.y * c.height > c.height + 12) { p.y = -0.02; p.x = Math.random(); }
            const x = p.x * c.width + sway * 14;
            ctx.beginPath();
            ctx.arc(x, p.y * c.height, p.r, 0, 7);
            ctx.fillStyle = 'rgba(220, 230, 250, 0.75)';
            ctx.fill();
          }
        } else if (SEASON === 'autumn') {
          for (const p of seasonParts) {
            p.y += (p.vy * dt) / 16;
            p.rot += p.rs;
            const sway = Math.sin(now / 1000 * p.swayS + p.ph);
            if (p.y * c.height > c.height + 24) { p.y = -0.04; p.x = Math.random(); }
            const x = p.x * c.width + sway * p.swayA;
            const flip = 0.4 + 0.6 * Math.abs(Math.sin(now / 1000 * p.fs + p.ph));
            petalShape(x, p.y * c.height, p.r * 0.8, p.rot, ['rgba(255,140,80,0.85)', 'rgba(200,70,40,0.8)'], flip);
          }
        } else {
          const hueBase = rainbow ? rainbowHue : 226;
          if (fall.length < 30 && Math.random() < (rainbow ? 0.3 : 0.18)) {
            fall.push({
              x: Math.random() * c.width, y: -10,
              vy: (Math.random() * 1.2 + 0.8) * (dt / 16),
              ph: Math.random() * 6, sway: 8 + Math.random() * 16,
              r: Math.random() * 2.6 + 2
            });
          }
          for (let i = fall.length - 1; i >= 0; i--) {
            const f = fall[i];
            f.y += f.vy; f.ph += 0.03;
            if (f.y > c.height + 14) { fall.splice(i, 1); continue; }
            const x = f.x + Math.sin(f.ph) * f.sway;
            if (rainbow) {
              const hue = (f.ph * 57 + rainbowHue) % 360;
              sparkle(x, f.y, f.r * 2.2, 'hsl(' + hue + ',90%,72%,$A)', 0.85);
            } else {
              sparkle(x, f.y, f.r * 2.2, 'rgba(228, 232, 252, $A)', 0.65 + Math.abs(Math.sin(f.ph * 2)) * 0.35);
            }
          }
        }
        if (SEASON === 'summer') {
          for (const fl of flies) {
            fl.ph += 0.01;
            const x = fl.x * c.width + Math.sin(fl.ph * fl.sp) * fl.ax;
            const y = fl.y * c.height + Math.cos(fl.ph * fl.sp * 0.7) * fl.ay;
            const a = 0.35 + Math.abs(Math.sin(fl.ph * 2)) * 0.55;
            const g = ctx.createRadialGradient(x, y, 0, x, y, 8);
            g.addColorStop(0, 'rgba(220, 255, 150, ' + a + ')');
            g.addColorStop(1, 'rgba(220, 255, 150, 0)');
            ctx.fillStyle = g;
            ctx.beginPath(); ctx.arc(x, y, 8, 0, 7); ctx.fill();
          }
        }
        nextMeteor -= dt;
        if (nextMeteor <= 0) {
          nextMeteor = 1200 + Math.random() * 2500;
          meteors.push({ x: Math.random() * c.width * 0.85, y: -20, vx: 4 + Math.random() * 3, vy: 2.5 + Math.random() * 2, life: 1 });
        }
        meteors = meteors.filter((m) => m.life > 0 && m.y < c.height + 40);
        for (const m of meteors) {
          m.x += m.vx; m.y += m.vy; m.life -= 0.005;
          const tail = 18;
          const g = ctx.createLinearGradient(m.x, m.y, m.x - m.vx * tail, m.y - m.vy * tail);
          g.addColorStop(0, 'rgba(210, 214, 255, ' + 0.95 * m.life + ')');
          g.addColorStop(1, 'rgba(210, 214, 255, 0)');
          ctx.strokeStyle = g; ctx.lineWidth = 2;
          ctx.beginPath(); ctx.moveTo(m.x, m.y); ctx.lineTo(m.x - m.vx * tail, m.y - m.vy * tail); ctx.stroke();
        }
        trail = trail.filter((p) => p.life > 0);
        for (const p of trail) {
          p.life -= 0.014; p.y -= 0.25;
          ctx.beginPath();
          ctx.arc(p.x, p.y, p.life * 3, 0, 7);
          ctx.fillStyle = 'rgba(150, 115, 225, ' + p.life * 0.6 + ')';
          ctx.fill();
        }
      }
      bursts = bursts.filter((p) => p.life > 0);
      for (const p of bursts) {
        p.life -= 0.02;
        p.x += (p.vx * dt) / 16; p.y += (p.vy * dt) / 16; p.vy += 0.04;
        if (p.heart) {
          ctx.fillStyle = 'rgba(240, 110, 160, ' + p.life * 0.85 + ')';
          ctx.beginPath();
          ctx.moveTo(p.x, p.y + p.life * 5);
          ctx.bezierCurveTo(p.x - p.life * 7, p.y - p.life, p.x - p.life * 2.5, p.y - p.life * 6, p.x, p.y - p.life * 2);
          ctx.bezierCurveTo(p.x + p.life * 2.5, p.y - p.life * 6, p.x + p.life * 7, p.y - p.life, p.x, p.y + p.life * 5);
          ctx.fill();
        } else {
          sparkle(p.x, p.y, p.life * 5, 'rgba(226, 229, 248, $A)', p.life * 0.9);
        }
      }
    } catch (e) { /* 单帧异常不终止动画循环 */ }
    requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);
})();
