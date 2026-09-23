# -*- coding: utf-8 -*-
"""Download live2d models into web/assets/models for self-hosting."""
import json
import os
import posixpath
import time
import urllib.request

BASE = 'https://model.hacxy.cn/'
DEST = 'web/assets/models'
MODELS = [
    ('Hiyori', 'Hiyori.model3.json'),
    ('chino', 'model.json'),
    ('Senko_Normals', 'senko.model3.json'),
    ('koharu', 'model.json'),
]


def fetch(url, retries=2):
    last = None
    for i in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read()
        except Exception as e:  # noqa: BLE001
            last = e
            if i == retries:
                raise
            time.sleep(1.5)
    raise last


def walk_refs(node, out):
    if isinstance(node, dict):
        for v in node.values():
            walk_refs(v, out)
    elif isinstance(node, list):
        for v in node:
            walk_refs(v, out)
    elif isinstance(node, str):
        if node.endswith(('.moc', '.moc3', '.png', '.jpg', '.jpeg', '.exp.json',
                          '.motion3.json', '.pose3.json', '.cdi3.json',
                          '.physics.json', '.physics3.json', '.pose.json')) \
                and not node.startswith('http'):
            out.add(node)


total = 0
for dirname, entry in MODELS:
    durl = BASE + dirname + '/' + entry
    ddir = os.path.join(DEST, dirname)
    os.makedirs(ddir, exist_ok=True)
    data_bytes = fetch(durl)
    with open(os.path.join(ddir, entry), 'wb') as f:
        f.write(data_bytes)
    data = json.loads(data_bytes)
    refs = set()
    walk_refs(data, refs)
    print(f'[{dirname}] entry={entry}, files={len(refs)}')
    for ref in sorted(refs):
        rel = ref.replace('\\', '/')
        furl = BASE + dirname + '/' + rel
        fpath = os.path.join(ddir, *rel.split('/'))
        os.makedirs(os.path.dirname(fpath), exist_ok=True)
        blob = fetch(furl)
        with open(fpath, 'wb') as f:
            f.write(blob)
        total += len(blob)
        print(f'   {rel}  {len(blob) // 1024}KB')
print('models total:', total // 1024, 'KB')
