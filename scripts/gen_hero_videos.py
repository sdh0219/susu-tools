# -*- coding: utf-8 -*-
"""Generate seamless looping hero background videos (night & day) via PIL frames + ffmpeg."""
import math
import os
import shutil
import subprocess
import tempfile

from PIL import Image, ImageDraw, ImageFilter

W, H = 1280, 720
FPS = 30
SECONDS = 10
P = FPS * SECONDS  # 300 frames per loop
FFMPEG = os.path.join('projects', 'bilinote', 'bin', 'ffmpeg.exe')
OUT_DIR = 'web/assets/video'

FONT_BOLD = 'C:/Windows/Fonts/msyhbd.ttc'


def lerp(a, b, t):
    return a + (b - a) * t


def ease(t):
    return t * t * (3 - 2 * t)


def make_night_bg():
    """夜空底图：深蓝紫渐变 + 右上角星云光晕"""
    bg = Image.new('RGB', (W, H))
    d = Image.new('RGB', (W, H))
    dd = ImageDraw.Draw(d)
    for y in range(H):
        t = y / H
        r = int(lerp(16, 8, t))
        g = int(lerp(12, 8, t))
        b = int(lerp(34, 12, t))
        dd.line([(0, y), (W, y)], fill=(r, g, b))
    glow = Image.new('L', (W, H), 0)
    gd = ImageDraw.Draw(glow)
    for i in range(160):
        a = int(60 * (1 - i / 160))
        gd.ellipse([W * 0.55 - i * 2.2, -260 + i * 1.4, W * 0.55 + i * 2.2, 260 - i * 1.4], fill=a)
    purple = Image.new('RGB', (W, H), (88, 60, 168))
    bg.paste(Image.composite(purple, bg, glow), (0, 0))
    return bg


def make_day_bg():
    """白日底图：暖燕麦渐变 + 柔粉光斑"""
    bg = Image.new('RGB', (W, H))
    d = Image.new('RGB', (W, H))
    dd = ImageDraw.Draw(d)
    for y in range(H):
        t = y / H
        r = int(lerp(250, 243, t))
        g = int(lerp(244, 237, t))
        b = int(lerp(240, 231, t))
        dd.line([(0, y), (W, y)], fill=(r, g, b))
    for (cx, cy, rr, col) in [
        (W * 0.15, H * 0.25, 190, (250, 226, 235)),
        (W * 0.85, H * 0.7, 230, (255, 236, 220)),
        (W * 0.5, H * 0.05, 160, (240, 232, 250)),
    ]:
        bokeh = Image.new('L', (W, H), 0)
        bd = ImageDraw.Draw(bokeh)
        bd.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], fill=200)
        bokeh = bokeh.filter(ImageFilter.GaussianBlur(60))
        tint = Image.new('RGB', (W, H), col)
        bg = Image.composite(tint, bg, bokeh)
    return bg


def star_positions(n, seed=7):
    import random
    rnd = random.Random(seed)
    return [(rnd.random() * W, rnd.random() * H * 0.85, rnd.random() * 1.4 + 0.5,
             rnd.randrange(1, 4), rnd.random() * 6.28) for _ in range(n)]


def petal_path(d, x, y, r, rot, alpha):
    ca, sa = math.cos(rot), math.sin(rot)
    def tp(px, py):
        return (x + px * ca - py * sa, y + px * sa + py * ca)
    p1 = tp(0, r)
    c1 = tp(-r * 1.15, r * 0.55)
    c2 = tp(-r * 1.05, -r * 0.55)
    p2 = tp(-r * 0.22, -r * 0.8)
    c3 = tp(0, -r * 0.55)
    p3 = tp(r * 0.22, -r * 0.8)
    c4 = tp(r * 1.05, -r * 0.55)
    p4 = tp(r * 1.15, r * 0.55)
    c5 = tp(0, r)
    d.polygon(
        [p1,
         (c1[0] * 0.66 + p1[0] * 0.34, c1[1] * 0.66 + p1[1] * 0.34),
         (c1[0] * 0.66 + c2[0] * 0.34, c1[1] * 0.66 + c2[1] * 0.34),
         (c2[0] * 0.66 + p2[0] * 0.34, c2[1] * 0.66 + p2[1] * 0.34),
         p2,
         (c3[0], c3[1]),
         p3,
         (c4[0] * 0.66 + p3[0] * 0.34, c4[1] * 0.66 + p3[1] * 0.34),
         (c4[0] * 0.66 + p4[0] * 0.34, c4[1] * 0.66 + p4[1] * 0.34),
         p4],
        fill=(247, 158, 190, alpha)
    )


def gen_frames(theme, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    night = theme == 'night'
    bg = make_night_bg() if night else make_day_bg()
    stars = star_positions(90 if night else 0)
    bokeh = [(0.12, 0.3, 1), (0.5, 0.15, 2), (0.8, 0.5, 1)]
    # 夜樱花瓣（9 片，循环无缝：每片整周期恰好落完整屏）
    import random
    rnd = random.Random(21)
    petals = []
    for _ in range(9):
        petals.append({
            'x0': rnd.random() * W,
            'y0': rnd.random() * (H + 60) - 30,
            'r': rnd.random() * 6 + 8,
            'rot': rnd.random() * 6.28,
            'rs': rnd.choice([0.02, 0.03, -0.025]),
            'k': rnd.choice([1, 1, 2]),
            'swayA': rnd.random() * 26 + 10,
            'swayK': rnd.choice([1, 2]),
        })
    # 日间樱吹雪（20 片）
    day_petals = []
    for _ in range(20):
        day_petals.append({
            'x0': rnd.random() * W,
            'y0': rnd.random() * (H + 60) - 30,
            'r': rnd.random() * 7 + 7,
            'rot': rnd.random() * 6.28,
            'rs': rnd.choice([0.02, 0.035, -0.03]),
            'k': rnd.choice([1, 2]),
            'swayA': rnd.random() * 30 + 12,
            'swayK': rnd.choice([1, 2]),
        })
    overlay = Image.new('RGBA', (W, H), (0, 0, 0, 0))

    for i in range(P):
        t = i / P
        frame = bg.copy().convert('RGBA')
        d = ImageDraw.Draw(frame, 'RGBA')
        if night:
            # 闪烁星星
            for (x, y, r, k, ph) in stars:
                a = 0.35 + abs(math.sin(2 * math.pi * k * t + ph)) * 0.5
                d.ellipse([x - r, y - r, x + r, y + r], fill=(226, 229, 248, int(a * 255)))
            # 两颗流星（周期内定时划过）
            for (m_start, m_dur, mx0, my0, mvx, mvy) in [
                (0.08, 0.14, W * 0.7, 40, -7, 3.2),
                (0.55, 0.12, W * 0.45, 20, -6, 2.8),
            ]:
                lt = (t - m_start) / m_dur
                if 0 <= lt <= 1:
                    mx = mx0 + mvx * lt * 260
                    my = my0 + mvy * lt * 260
                    a = int(230 * math.sin(math.pi * lt))
                    tail = 90
                    g = d.line(
                        [(mx, my), (mx - mvx * tail / 3, my - mvy * tail / 3)],
                        fill=(205, 210, 255, a), width=3)
            # 夜樱花瓣
            for p in petals:
                y = ((p['y0'] + p['k'] * (H + 60) * t) % (H + 60)) - 30
                x = p['x0'] + math.sin(2 * math.pi * p['swayK'] * t + p['rot']) * p['swayA']
                petal_path(d, x, y, p['r'], p['rot'] + 6.28 * p['rs'] * t, 165)
        else:
            # 樱吹雪
            for p in day_petals:
                y = ((p['y0'] + p['k'] * (H + 60) * t) % (H + 60)) - 30
                x = p['x0'] + math.sin(2 * math.pi * p['swayK'] * t + p['rot']) * p['swayA']
                petal_path(d, x, y, p['r'], p['rot'] + 6.28 * p['rs'] * t, 200)
        frame = frame.convert('RGB')
        frame.save(os.path.join(out_dir, f'{i:04d}.jpg'), quality=85)
        if i % 60 == 0:
            print(f'[{theme}] frame {i}/{P}')


def encode(frames_dir, out_name):
    os.makedirs(OUT_DIR, exist_ok=True)
    out = os.path.join(OUT_DIR, out_name)
    subprocess.run([
        FFMPEG, '-y', '-framerate', '30', '-i', os.path.join(frames_dir, '%04d.jpg'),
        '-c:v', 'libx264', '-preset', 'medium', '-crf', '24',
        '-pix_fmt', 'yuv420p', '-movflags', '+faststart', out
    ], check=True, capture_output=True)
    print(out, os.path.getsize(out) // 1024, 'KB')


if __name__ == '__main__':
    tmp = tempfile.mkdtemp(prefix='hero_vid_')
    print('generating night frames...')
    gen_frames('night', tmp)
    encode(tmp, 'hero-night.mp4')
    print('generating day frames...')
    gen_frames('day', tmp + '_day')
    encode(tmp + '_day', 'hero-day.mp4')
    shutil.rmtree(tmp, ignore_errors=True)
    shutil.rmtree(tmp + '_day', ignore_errors=True)
    print('DONE')
