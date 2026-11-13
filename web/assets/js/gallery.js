/* 画廊：读取 manifest 渲染卡片 + 灯箱 */
(function () {
  const grid = document.getElementById('galleryGrid');
  const empty = document.getElementById('galleryEmpty');
  if (!grid) return;

  let lastTrigger = null; // 触发灯箱的卡片，关闭后归还焦点

  fetch('/assets/gallery/manifest.json')
    .then((r) => r.json())
    .then((data) => {
      const items = data.items || [];
      if (!items.length) {
        if (empty) empty.style.display = 'block';
        return;
      }
      grid.innerHTML = items.map((it) => `
        <figure class="g-card" role="button" tabindex="0" aria-label="放大查看${it.title}">
          <img src="/assets/gallery/${it.file}" alt="${it.title}" loading="lazy">
          <figcaption>
            <strong>${it.title}</strong>
            <span>${it.desc || ''}</span>
          </figcaption>
        </figure>`).join('');
      grid.querySelectorAll('.g-card').forEach((card, i) => {
        card.addEventListener('click', () => openLightbox(items[i], card));
        card.addEventListener('keydown', (e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            openLightbox(items[i], card);
          }
        });
      });
    })
    .catch(() => { if (empty) empty.style.display = 'block'; });

  function openLightbox(item, trigger) {
    let box = document.getElementById('gLightbox');
    if (!box) {
      box = document.createElement('div');
      box.id = 'gLightbox';
      box.className = 'g-lightbox';
      box.setAttribute('role', 'dialog');
      box.setAttribute('aria-modal', 'true');
      box.setAttribute('aria-label', '图片放大');
      box.innerHTML = '<img alt=""><p></p><button type="button" class="g-lightbox-close" aria-label="关闭">✕</button>';
      box.querySelector('.g-lightbox-close').style.cssText =
        'position:absolute;top:18px;right:22px;width:40px;height:40px;'
        + 'border:1px solid var(--border-color);border-radius:50%;'
        + 'background:rgba(255,255,255,0.08);color:#fff;font-size:1.1rem;cursor:pointer;';
      box.addEventListener('click', () => closeLightbox());
      document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && box.classList.contains('open')) closeLightbox();
      });
      document.body.appendChild(box);
    }
    lastTrigger = trigger || null;
    box.querySelector('img').src = '/assets/gallery/' + item.file;
    box.querySelector('p').textContent = item.title + (item.desc ? ' · ' + item.desc : '');
    box.classList.add('open');
    document.body.style.overflow = 'hidden'; // 锁背景滚动
    box.querySelector('.g-lightbox-close').focus();
  }

  function closeLightbox() {
    const box = document.getElementById('gLightbox');
    if (!box || !box.classList.contains('open')) return;
    box.classList.remove('open');
    document.body.style.overflow = '';
    if (lastTrigger) lastTrigger.focus();
  }
})();
