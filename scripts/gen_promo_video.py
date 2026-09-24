# -*- coding: utf-8 -*-
"""生成抖音宣传视频：Susu 二次元工具站（1080x1920, 30fps, 18s, 含 8-bit BGM）"""
import math
import os
import shutil
import subprocess
import tempfile
import wave

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1080, 1920
FPS = 30
DUR = 18
P = FPS * DUR  # 540
FB = 'C:/Windows/Fonts/msyhbd.ttc'
FR = 'C:/Windows/Fonts/msyh.ttc'
URL = 'susu-2x9.pages.dev'
REPO = 'github.com/sdh0219/susu-tools'
FRAMES_DIR = os.path.join('media', 'promo_frames')
OUT = os.path.join('media', 'promo-douyin.mp4')
COVER = os.path.join('media', 'promo-cover.png')
BGM = os.path.join('media', 'promo-bgm.wav')

F = lambda size: ImageFont.truetype(FB, size)
R = lambda size: ImageFont.truetype(FR, size)


def lerp(a, b, t):
    return a + (b - a) * t

PINK = (248, 158, 192)
PINK_L = (252, 214, 226)
PURPLE = (167, 139, 250)
BLUE = (96, 165, 250)
CYAN = (103, 232, 249)
WHITE = (242, 242, 248)
MUTED = (152, 152, 170)

CARDS = [
    ('BiliNote 增强版', '视频一键转 AI 笔记', (248, 158, 192)),
    ('Knowledge Publisher', 'Markdown → 知乎 / 抖音图文', (167, 139, 250)),
    ('PPT医生', 'AI 生成医学 PPT', (96, 165, 250)),
    ('千瞳', '2D 视频 → 3D 场景', (34, 211, 238)),
    ('bg-skin', 'VS Code 樱花背景壁纸', (129, 230, 176)),
]
FEATURES = [
    '樱花雨 · 飘在页面里',
    '星空 + 流星 + 星落',
    '看板娘陪着你写代码',
    '暗夜 / 白日 一键切换',
]


def ease_out(t):
    return 1 - (1 - t) ** 3


def clamp01(t):
    return max(0.0, min(1.0, t))


def text_layer(text, font, fill, pad=40):
    """把文字渲染成带透明通道的图层，方便做淡入/位移"""
    dummy = ImageDraw.Draw(Image.new('RGBA', (10, 10)))
    box = dummy.textbbox((0, 0), text, font=font)
    w, h = box[2] - box[0], box[3] - box[1]
    layer = Image.new('RGBA', (w + pad * 2, h + pad * 2), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    ld.text((pad - box[0], pad - box[1]), text, font=font, fill=fill)
    return layer, box


def paste_center(base, layer, cx, cy, alpha=255, dy=0):
    layer = layer.copy()
    if alpha < 255:
        a = layer.getchannel('A').point(lambda v: int(v * alpha / 255))
        layer.putalpha(a)
    base.alpha_composite(layer, (int(cx - layer.width / 2), int(cy - layer.height / 2 + dy)))


def base_bg(t):
    """夜空底 + 星星 + 两片装饰樱花（t: 全局秒）"""
    bg = Image.new('RGB', (W, H))
    d = ImageDraw.Draw(bg)
    for y in range(H):
        k = y / H
        d.line([(0, y), (W, y)], fill=(int(lerp(18, 10, k)), int(lerp(14, 10, k)), int(lerp(36, 16, k))))
    # 星星
    rnd = np.random.RandomState(7)
    for _ in range(110):
        x, y = rnd.random() * W, rnd.random() * H * 0.9
        r = rnd.random() * 1.6 + 0.6
        ph = rnd.random() * 6.28
        a = 0.3 + abs(math.sin(ph + t * 1.6)) * 0.5
        d.ellipse([x - r, y - r, x + r, y + r], fill=(226, 229, 248, int(a * 255)))
    # 星云光
    glow = Image.new('L', (W, H), 0)
    gd = ImageDraw.Draw(glow)
    for i in range(180):
        gd.ellipse([W * 0.7 - i * 2, -200 + i, W * 0.7 + i * 2, 300 - i], fill=int(46 * (1 - i / 180)))
    purple = Image.new('RGBA', (W, H), (96, 60, 168, 255))
    bg.paste(Image.composite(purple, bg, glow), (0, 0))
    return bg.convert('RGBA')


def petals_overlay(t, n=16):
    """飘落的樱花花瓣（RGBA 覆盖层）"""
    ov = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    period = 6.0
    n = 12
    for i in range(n):
        ph = i * 0.618
        y = ((t / period + ph) % 1.0) * (H + 80) - 40
        x = (i * 173.3) % W + math.sin(t * 0.9 + ph * 3) * 36
        r = 14 + (i * 7 % 12)
        rot = t * (0.6 + (i % 3) * 0.25) + ph * 2
        ca, sa = math.cos(rot), math.sin(rot)
        def tp(px, py):
            return (x + px * ca - py * sa, y + px * sa + py * ca)
        a = 185
        # 外层花瓣
        p1 = tp(0, r)
        c1 = tp(-r * 1.15, r * 0.55)
        c2 = tp(-r * 1.05, -r * 0.55)
        p2 = tp(-r * 0.22, -r * 0.8)
        c3 = tp(0, -r * 0.55)
        p3 = tp(r * 0.22, -r * 0.8)
        c4 = tp(r * 1.05, -r * 0.55)
        p4 = tp(r * 1.15, r * 0.55)
        d.polygon([p1,
                   (c1[0] * .66 + p1[0] * .34, c1[1] * .66 + p1[1] * .34),
                   (c1[0] * .66 + c2[0] * .34, c1[1] * .66 + c2[1] * .34),
                   (c2[0] * .66 + p2[0] * .34, c2[1] * .66 + p2[1] * .34),
                   p2, (c3[0], c3[1]), p3,
                   (c4[0] * .66 + p3[0] * .34, c4[1] * .66 + p3[1] * .34),
                   (c4[0] * .66 + p4[0] * .34, c4[1] * .66 + p4[1] * .34), p4],
                  fill=(247, 158, 190, a))
        # 内层浅色，做出花瓣立体感
        p1i = tp(0, r * 0.55)
        c1i = tp(-r * 0.7, r * 0.3)
        c2i = tp(-r * 0.6, -r * 0.35)
        p2i = tp(-r * 0.13, -r * 0.5)
        c3i = tp(0, -r * 0.32)
        p3i = tp(r * 0.13, -r * 0.5)
        c4i = tp(r * 0.6, -r * 0.35)
        p4i = tp(r * 1.15 * 0.55, r * 0.55 * 0.55)
        d.polygon([p1i,
                   (c1i[0] * .6 + p1i[0] * .4, c1i[1] * .6 + p1i[1] * .4),
                   (c1i[0] * .6 + c2i[0] * .4, c1i[1] * .6 + c2i[1] * .4),
                   (c2i[0] * .6 + p2i[0] * .4, c2i[1] * .6 + p2i[1] * .4),
                   p2i, (c3i[0], c3i[1]), p3i,
                   (c4i[0] * .6 + p3i[0] * .4, c4i[1] * .6 + p3i[1] * .4),
                   p4i],
                  fill=(255, 214, 230, min(255, a + 45)))
    return ov


def sparkle(d, x, y, r, a):
    d.line([(x - r, y), (x + r, y)], fill=(226, 229, 248, int(a * 255)), width=2)
    d.line([(x, y - r), (x, y + r)], fill=(226, 229, 248, int(a * 255)), width=2)


def make_bg_frames():
    """背景 + 花瓣是全片连续的，预渲染成序列（降低每帧成本）"""
    os.makedirs(FRAMES_DIR, exist_ok=True)
    for i in range(P):
        bg = base_bg(i / FPS).convert('RGBA')
        bg.alpha_composite(petals_overlay(i / FPS))
        bg.convert('RGB').save(os.path.join(FRAMES_DIR, f'{i:04d}.jpg'), quality=88)
        if i % 120 == 0:
            print('bg frame', i)


def compose(i):
    """在第 i 帧的背景上叠加当帧文字动效，返回 RGB 帧"""
    bg = Image.open(os.path.join(FRAMES_DIR, f'{i:04d}.jpg')).convert('RGBA')
    t = i / FPS

    def scene_progress(start, dur):
        return clamp01((i - start) / dur)

    # ---- S1 开场标题 (0-89) ----
    if i < 92:
        pr = ease_out(scene_progress(2, 26))
        layer, box = text_layer('自己做工具', F(120), WHITE + (255,))
        paste_center(bg, layer, W / 2, H * 0.30, int(pr * 255), dy=int((1 - pr) * 60))
        pr2 = ease_out(scene_progress(14, 26))
        layer2, _ = text_layer('也收藏好工具', F(120), PINK + (255,))
        paste_center(bg, layer2, W / 2, H * 0.30 + 170, int(pr2 * 255), dy=int((1 - pr2) * 60))
        pr3 = ease_out(scene_progress(30, 24))
        layer3, _ = text_layer('Susu · 二次元工具站', R(46), MUTED + (230,))
        paste_center(bg, layer3, W / 2, H * 0.30 + 320, int(pr3 * 255))
        # 闪光点缀
        d = ImageDraw.Draw(bg)
        for k in range(3):
            ph = (i / FPS * 2 + k * 1.1) % 3
            a = max(0, 1 - abs(ph - 1.5)) * 255
            sparkle(d, 200 + k * 340, H * 0.62, 12 + k * 3, a)

    # ---- S2 作品 (90-269) ----
    if 88 <= i < 272:
        pr = ease_out(clamp01((i - 88) / 24))
        layer, _ = text_layer('5 个开源作品', F(88), WHITE + (255,))
        paste_center(bg, layer, W / 2, 300, int(pr * 255), dy=int((1 - pr) * 40))
        base_y = 520
        for idx, (name, desc, accent) in enumerate(CARDS):
            start = 100 + idx * 26
            pr = ease_out(clamp01((i - start) / 22))
            if pr <= 0:
                continue
            card = Image.new('RGBA', (900, 210), (0, 0, 0, 0))
            cd = ImageDraw.Draw(card)
            cd.rounded_rectangle([0, 0, 900, 210], 26, fill=(22, 22, 26, int(215 * pr)), outline=accent + (int(160 * pr),), width=2)
            cd.rectangle([0, 0, 10, 210], fill=accent + (int(230 * pr),))
            cd.text((46, 40), name, font=F(52), fill=WHITE + (int(255 * pr),))
            cd.text((46, 122), desc, font=R(36), fill=(196, 196, 214, int(240 * pr)))
            dx = int((1 - pr) * 400)
            bg.alpha_composite(card, (90 + dx, base_y + idx * 228))
        if i >= 262:
            a = int(255 * clamp01((i - 262) / 10))
            layer, _ = text_layer('…还有一只看板娘', R(40), PINK_L + (a,))
            paste_center(bg, layer, W / 2, 1790, a)

    # ---- S3 特色 (270-389) ----
    if 270 <= i < 392:
        pr = ease_out(clamp01((i - 270) / 24))
        layer, _ = text_layer('这个站有什么', F(88), WHITE + (255,))
        paste_center(bg, layer, W / 2, 340, int(pr * 255), dy=int((1 - pr) * 40))
        for idx, feat in enumerate(FEATURES):
            start = 292 + idx * 22
            pr = ease_out(clamp01((i - start) / 22))
            if pr <= 0:
                continue
            ly, _ = text_layer(feat, R(56), (235, 236, 246, int(255 * pr)))
            dot_r = 10 * pr
            y = 560 + idx * 170
            paste_center(bg, ly, W / 2 + 40, y, int(pr * 255))
            dd = ImageDraw.Draw(bg)
            dd.ellipse([W / 2 - 300 - dot_r, y - dot_r, W / 2 - 300 + dot_r, y + dot_r], fill=PINK + (int(220 * pr),))

    # ---- S4 免费 (392-449) ----
    if 392 <= i < 452:
        pr = ease_out(clamp01((i - 392) / 20))
        layer, _ = text_layer('全部免费 · 全部开源', F(96), WHITE + (255,))
        paste_center(bg, layer, W / 2, H * 0.42, int(pr * 255), dy=int((1 - pr) * 50))
        pr2 = ease_out(clamp01((i - 406) / 18))
        layer2, _ = text_layer('没有广告 · 没有套路 · 点开就用', R(44), MUTED + (int(235 * pr2 * 255),))
        paste_center(bg, layer2, W / 2, H * 0.42 + 190, int(pr2 * 255))

    # ---- S5 结尾 (450-539) ----
    if i >= 450:
        pr = ease_out(clamp01((i - 450) / 24))
        layer, _ = text_layer(URL, F(84), WHITE + (255,))
        paste_center(bg, layer, W / 2, H * 0.36, int(pr * 255), dy=int((1 - pr) * 46))
        pr2 = ease_out(clamp01((i - 462) / 20))
        layer2, _ = text_layer('GitHub · B站 · 抖音：搜 Susu', R(42), PINK_L + (int(240 * pr2 * 255),))
        paste_center(bg, layer2, W / 2, H * 0.36 + 150, int(pr2 * 255))
        pr3 = ease_out(clamp01((i - 474) / 20))
        layer3, _ = text_layer('主人，点个关注再走嘛～', R(42), PINK + (int(235 * pr3 * 255),))
        paste_center(bg, layer3, W / 2, H * 0.36 + 260, int(pr3 * 255))
        # 看板娘头像（圆形 + 白边）
        pr4 = ease_out(clamp01((i - 468) / 20))
        if pr4 > 0 and os.path.exists('web/assets/img/about-portrait.png'):
            portrait = Image.open('web/assets/img/about-portrait.png').convert('RGBA').resize((420, 420))
            mask = Image.new('L', (420, 420), 0)
            ImageDraw.Draw(mask).ellipse([0, 0, 420, 420], fill=255)
            ring = Image.new('RGBA', (460, 460), (0, 0, 0, 0))
            ImageDraw.Draw(ring).ellipse([0, 0, 460, 460], fill=(248, 158, 192, int(220 * pr4)))
            px = int(W / 2 - 230), int(H * 0.56)
            bg.alpha_composite(ring, px)
            tmp = Image.new('RGBA', (420, 420), (0, 0, 0, 0))
            tmp.paste(portrait, (0, 0), mask)
            bg.alpha_composite(tmp, (px[0] + 20, px[1] + 20))
    return bg.convert('RGB')


def gen_bgm(path):
    """8-bit 甜美小曲：C 大调五声音阶 + 低音，18 秒"""
    sr = 44100
    bpm = 126
    eighth = 60 / bpm / 2
    n_total = int(DUR * sr)
    t_all = np.arange(n_total) / sr

    NOTE = {'C5': 523.25, 'D5': 587.33, 'E5': 659.25, 'G5': 783.99, 'A5': 880, 'C6': 1046.5, 'B5': 987.77, 'D6': 1174.66}
    melody = ['E5', 'G5', 'A5', 'C6', 'A5', 'G5', 'E5', 'G5',
              'A5', 'C6', 'D6', 'C6', 'A5', 'G5', 'A5', 'G5',
              'E5', 'G5', 'A5', 'C6', 'D6', 'C6', 'A5', 'G5',
              'A5', 'G5', 'E5', 'D5', 'E5', 'G5', 'E5', 'D5',
              'C5', 'D5', 'E5', 'G5', 'A5', 'C6', 'A5', 'G5',
              'E5', 'D5', 'C5', 'D5', 'E5', 'G5', 'A5', 'G5',
              'E5', 'G5', 'A5', 'G5', 'E5', 'D5', 'C5', 'D5',
              'E5', 'D5', 'C5', 'A4', 'C5', 'D5', 'E5', 'D5']
    A4 = 440.0
    f_of = {}
    for k, v in NOTE.items():
        f_of[k] = v
    f_of['A4'] = A4
    f_of.setdefault('D5', 587.33)

    mel = np.zeros(n_total)
    pos = 0
    for i, name in enumerate(melody * 3):
        if pos >= n_total:
            break
        f = f_of[name]
        dur = eighth
        n = int(dur * sr)
        tt = np.arange(n) / sr
        env = np.exp(-tt * 6)
        seg = (np.sin(2 * np.pi * f * tt) + 0.35 * np.sin(4 * np.pi * f * tt)) * env * 0.16
        mel[pos:pos + n] += seg[:max(0, min(n, n_total - pos))][:n]
        pos += n

    # 低音：每两拍一个根音
    bass_notes = ['C3', 'G3', 'A3', 'F3'] * 9
    BASS = {'C3': 130.81, 'G3': 196.0, 'A3': 220.0, 'F3': 174.61}
    bass = np.zeros(n_total)
    beat = eighth * 4
    for i, name in enumerate(bass_notes):
        pos = int(i * beat * 2 * sr)
        if pos >= n_total:
            break
        f = BASS[name]
        n = min(int(beat * 2 * sr), n_total - pos)
        tt = np.arange(n) / sr
        bass[pos:pos + n] += np.sin(2 * np.pi * f * tt) * np.exp(-tt * 2) * 0.12

    mix = np.tanh(mel * 1.4 + bass) * 0.6
    pcm = (mix / np.max(np.abs(mix)) * 32767 * 0.85).astype(np.int16)
    with wave.open(path, 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm.tobytes())
    print('bgm ok', os.path.getsize(path) // 1024, 'KB')


def make_cover():
    img = base_bg(1.2).convert('RGBA')
    ov = petals_overlay(0.8)
    img.alpha_composite(ov)
    d = ImageDraw.Draw(img)
    layer, box = text_layer('自己做工具的', F(110), WHITE + (255,))
    paste_center(img, layer, W / 2, 620, 255)
    layer, _ = text_layer('二次元', F(110), PINK + (255,))
    paste_center(img, layer, W / 2, 780, 255)
    layer, _ = text_layer('全部免费 · 全部开源', R(52), MUTED + (235,))
    paste_center(img, layer, W / 2, 940, 235)
    layer, _ = text_layer(URL, F(60), (129, 230, 176, 255))
    paste_center(img, layer, W / 2, 1120, 255)
    img.convert('RGB').save(COVER, quality=92)
    print('cover ok', os.path.getsize(COVER) // 1024, 'KB')


if __name__ == '__main__':
    os.makedirs('media', exist_ok=True)
    print('>> 背景/花瓣序列渲染')
    make_bg_frames()
    print('>> 合成视频帧 + 编码')
    tmp = tempfile.mkdtemp(prefix='promo_')
    for i in range(P):
        compose(i).save(os.path.join(tmp, f'{i:04d}.jpg'), quality=90)
        if i % 120 == 0:
            print('compose', i)
    print('>> BGM')
    gen_bgm(BGM)
    print('>> 编码 mp4')
    subprocess.run([
        'projects/bilinote/bin/ffmpeg.exe', '-y',
        '-framerate', '30', '-i', os.path.join(tmp, '%04d.jpg'),
        '-i', BGM,
        '-map', '0:v', '-map', '1:a',
        '-c:v', 'libx264', '-preset', 'medium', '-crf', '22',
        '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '128k',
        '-shortest', '-movflags', '+faststart', OUT
    ], check=True, capture_output=True)
    print('OUT:', OUT, os.path.getsize(OUT) // 1024, 'KB')
    make_cover()
    shutil.rmtree(tmp, ignore_errors=True)
    shutil.rmtree(FRAMES_DIR, ignore_errors=True)
    print('DONE')
