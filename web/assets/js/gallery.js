/* 画廊：读取 manifest 渲染卡片 + 灯箱 */
(function () {
  const grid = document.getElementById('galleryGrid');
  const empty = document.getElementById('galleryEmpty');
  if (!grid) return;

  fetch('/assets/gallery/manifest.json')
    .then((r) => r.json())
    .then((data) => {
      const items = data.items || [];
      if (!items.length) {
        if (empty) empty.style.display = 'block';
        return;
      }
      grid.innerHTML = items.map((it) => `
        <figure class="g-card">
          <img src="/assets/gallery/${it.file}" alt="${it.title}" loading="lazy">
          <figcaption>
            <strong>${it.title}</strong>
            <span>${it.desc || ''}</span>
          </figcaption>
        </figure>`).join('');
      grid.querySelectorAll('.g-card').forEach((card, i) => {
        card.addEventListener('click', () => openLightbox(items[i]));
      });
    })
    .catch(() => { if (empty) empty.style.display = 'block'; });

  function openLightbox(item) {
    let box = document.getElementById('gLightbox');
    if (!box) {
      box = document.createElement('div');
      box.id = 'gLightbox';
      box.className = 'g-lightbox';
      box.innerHTML = '<img alt=""><p></p>';
      box.addEventListener('click', () => box.classList.remove('open'));
      document.body.appendChild(box);
    }
    box.querySelector('img').src = '/assets/gallery/' + item.file;
    box.querySelector('p').textContent = item.title + (item.desc ? ' · ' + item.desc : '');
    box.classList.add('open');
  }
})();
