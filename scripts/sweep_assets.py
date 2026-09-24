# -*- coding: utf-8 -*-
"""Sweep every referenced asset on the live site for availability."""
import re
import urllib.error
import urllib.request

BASE = 'https://susu-2x9.pages.dev'
pages = ['/', '/blog.html', '/404.html']
assets = set()

for pg in pages:
    try:
        html = urllib.request.urlopen(urllib.request.Request(BASE + pg, headers={'User-Agent': 'Mozilla/5.0'}), timeout=20).read().decode('utf-8')
    except Exception as e:  # noqa: BLE001
        print('PAGE FAIL', pg, e)
        continue
    for m in re.finditer(r'(?:src|href)="(assets/[^"]+|/assets/[^"]+)"', html):
        u = m.group(1)
        if u.startswith('/'):
            assets.add(BASE + u)
        else:
            assets.add(BASE + '/' + u)

extras = ['/assets/video/hero-night.mp4', '/assets/video/hero-day.mp4']
extras += ['/assets/voice/p%d.mp3' % i for i in range(9)]
extras += [
    '/assets/models/Hiyori/Hiyori.model3.json',
    '/assets/models/chino/model.json',
    '/assets/models/Senko_Normals/senko.model3.json',
    '/assets/models/koharu/model.json',
    '/assets/js/oml2d.min.js',
    '/sitemap.xml', '/rss.xml', '/robots.txt',
]
for e in extras:
    assets.add(BASE + e)

fail = []
for u in sorted(assets):
    try:
        r = urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0'}), timeout=25)
        code = r.status
    except urllib.error.HTTPError as e2:
        code = e2.code
    except Exception as e2:  # noqa: BLE001
        code = str(e2)[:30]
    if code != 200:
        fail.append((u, code))

print(f'checked {len(assets)} assets, failures: {len(fail)}')
for u, c in fail:
    print('  FAIL', c, u)
