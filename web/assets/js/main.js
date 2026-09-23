(function () {
  const nav = document.getElementById('nav');
  const navToggle = document.getElementById('navToggle');
  const navLinks = document.getElementById('navLinks');

  window.addEventListener('scroll', () => {
    if (window.scrollY > 50) {
      nav.classList.add('scrolled');
    } else {
      nav.classList.remove('scrolled');
    }
  });

  if (navToggle && navLinks) {
    navToggle.addEventListener('click', () => {
      navToggle.classList.toggle('active');
      navLinks.classList.toggle('open');
    });

    navLinks.querySelectorAll('a').forEach(link => {
      link.addEventListener('click', () => {
        navToggle.classList.remove('active');
        navLinks.classList.remove('open');
      });
    });
  }

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
          observer.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.1, rootMargin: '0px 0px -40px 0px' }
  );

  document.querySelectorAll('.fade-in').forEach(el => observer.observe(el));

  const statNumbers = document.querySelectorAll('.stat-number[data-count]');
  if (statNumbers.length > 0) {
    const statsObserver = new IntersectionObserver(
      (entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            animateCount(entry.target);
            statsObserver.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.5 }
    );

    statNumbers.forEach(el => statsObserver.observe(el));
  }

  function animateCount(el) {
    const target = parseInt(el.dataset.count, 10);
    const duration = 1500;
    const start = performance.now();

    function update(now) {
      const elapsed = now - start;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      el.textContent = Math.round(target * eased);
      if (progress < 1) {
        requestAnimationFrame(update);
      } else {
        el.textContent = target;
      }
    }

    requestAnimationFrame(update);
  }

  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
      const targetId = this.getAttribute('href');
      if (targetId === '#') return;
      const targetEl = document.querySelector(targetId);
      if (targetEl) {
        e.preventDefault();
        targetEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });
  });
})();

  // 联系邮箱：静态 HTML 中不出现完整地址，运行时拼装，降低爬虫抓取
  const mailBtn = document.getElementById('mail-btn');
  if (mailBtn) {
    const parts = ['2388647455', '@', 'qq', '.', 'com'];
    const addr = parts.join('');
    mailBtn.href = 'mailto:' + addr;
    mailBtn.textContent = '📮 ' + addr;
  }

  // 主题切换：暗色为默认，选择记忆在 localStorage
  const themeBtn = document.getElementById('themeToggle');
  if (themeBtn) {
    const root = document.documentElement;
    const syncIcon = () => {
      themeBtn.textContent = root.getAttribute('data-theme') === 'light' ? '🌙' : '☀️';
    };
    syncIcon();
    themeBtn.addEventListener('click', () => {
      const next = root.getAttribute('data-theme') === 'light' ? 'dark' : 'light';
      root.setAttribute('data-theme', next);
      try { localStorage.setItem('susu-theme', next); } catch (e) { /* 隐私模式忽略 */ }
      syncIcon();
    });
  }

  // Hero 背景视频：主题联动（暗=夜樱 / 浅=白日樱吹雪），load 后再加载
  const heroVideo = document.querySelector('.hero-video');
  if (heroVideo) {
    const applyHeroSrc = () => {
      const want = document.documentElement.getAttribute('data-theme') === 'light'
        ? 'hero-day.mp4' : 'hero-night.mp4';
      if (!heroVideo.src.endsWith(want)) {
        heroVideo.src = 'assets/video/' + want;
        heroVideo.play().catch(() => { /* 自动播放被拦截时保持静帧 */ });
      }
    };
    const startHero = () => {
      applyHeroSrc();
      new MutationObserver(applyHeroSrc).observe(
        document.documentElement, { attributes: true, attributeFilter: ['data-theme'] }
      );
    };
    if (document.readyState === 'complete') setTimeout(startHero, 600);
    else window.addEventListener('load', () => setTimeout(startHero, 600));
  }
