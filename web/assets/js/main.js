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
    const syncNavAria = () => {
      const open = navLinks.classList.contains('open');
      navToggle.setAttribute('aria-expanded', String(open));
      navToggle.setAttribute('aria-label', open ? '关闭菜单' : '打开菜单');
    };
    navToggle.addEventListener('click', () => {
      navToggle.classList.toggle('active');
      navLinks.classList.toggle('open');
      syncNavAria();
    });

    navLinks.querySelectorAll('a').forEach(link => {
      link.addEventListener('click', () => {
        navToggle.classList.remove('active');
        navLinks.classList.remove('open');
        syncNavAria();
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
        // 尊重系统"减弱动态效果"：reduce 时瞬时跳转，与 style.css 的 CSS 降级保持一致
        const behavior = window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth';
        // 滚动后把键盘焦点移到目标（WCAG 2.4.3）；非交互元素运行时补 tabindex（已有时不动，避免移出 Tab 序列）
        if (!targetEl.hasAttribute('tabindex')) targetEl.setAttribute('tabindex', '-1');
        targetEl.scrollIntoView({ behavior: behavior, block: 'start' });
        targetEl.focus({ preventScroll: true });
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

  // Hero 背景视频已停用：hero 改用看板立绘，保留昼夜视频文件备复用


  // ---- Konami 秘技彩蛋：↑↑↓↓←→←→BA ----
  const KONAMI = ['ArrowUp', 'ArrowUp', 'ArrowDown', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'ArrowLeft', 'ArrowRight', 'b', 'a'];
  let kIdx = 0;
  addEventListener('keydown', (e) => {
    const k = e.key.length === 1 ? e.key.toLowerCase() : e.key;
    kIdx = (k === KONAMI[kIdx]) ? kIdx + 1 : (k === KONAMI[0] ? 1 : 0);
    if (kIdx === KONAMI.length) {
      kIdx = 0;
      window.dispatchEvent(new CustomEvent('susu-rainbow'));
      window.dispatchEvent(new CustomEvent('susu-konami'));
    }
  });

  // ---- 双击点赞：全站计数 ----
  let siteLikes = parseInt(localStorage.getItem('susu-likes') || '0', 10);
  const likeChip = document.createElement('div');
  likeChip.className = 'like-chip';
  likeChip.textContent = '💕 已被摸 ' + siteLikes + ' 次';
  document.body.appendChild(likeChip);
  addEventListener('dblclick', (e) => {
    siteLikes++;
    localStorage.setItem('susu-likes', String(siteLikes));
    likeChip.textContent = '💕 已被摸 ' + siteLikes + ' 次';
    likeChip.classList.remove('pop');
    void likeChip.offsetWidth;
    likeChip.classList.add('pop');
  });
