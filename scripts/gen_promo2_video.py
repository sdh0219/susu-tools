# -*- coding: utf-8 -*-
"""宣传片 v2（24s 加长版）：夜樱背景 + 立绘主讲人 + 语音气泡（晓伊软萌旁白）+ 平台匹配片尾"""
import math
import os
import shutil
import subprocess
import tempfile

from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920
FPS = 30
SECONDS = 24
P = FPS * SECONDS  # 720
TITLE_END = 90        # 0-3s 片头
PRES_START = 90       # 3s
PRES_END = 495        # 16.5s 看板娘主讲（4 个气泡各 ~3.4s）
END_START = 495       # 16.5-24s 片尾
URL_TEXT = 'susu-2x9.pages.dev'
FB = 'C:/Windows/Fonts/msyhbd.ttc'
FR = 'C:/Windows/Fonts/msyh.ttc'
F_BIG = ImageFont.truetype(FB, 104)
F_MID = ImageFont.truetype(FB, 84)
F_MID2 = ImageFont.truetype(FR, 56)
F_SMALL = ImageFont.truetype(FR, 40)
F_BUB = ImageFont.truetype(FR, 46)

TMP = os.path.join('media', 'promo2_frames')
OUT = os.path.join('media', 'promo-douyin-v2.mp4')
BGM = 'media/promo-bgm.wav'
NARR = ['media/promo2/n1.mp3', 'media/promo2/n2.mp3', 'media/promo2/n3.mp3', 'media/promo2/n4.mp3']
NARR_DELAYS = [4200, 7400, 10600, 13800]
TITLE_END = 90
SEG = 90
PRES_START = 90
PRES_END = 495
END_START = 495

os.makedirs(TMP, exist_ok=True)
os.makedirs('media', exist_ok=True)

# 1) 抽取夜樱背景帧（10s 无缝循环 ×2.4 覆盖 24s）
subprocess.run([
    'projects/bilinote/bin/ffmpeg.exe', '-y',
    '-i', 'web/assets/video/hero-night.mp4',
    '-vf', 'fps=30,scale=1080:1920',
    os.path.join(TMP, 'bg_%04d.jpg')
], check=True, capture_output=True)
bg_frames = sorted(f for f in os.listdir(TMP) if f.startswith('bg_'))
print('bg frames:', len(bg_frames))

portrait = Image.open('web/assets/img/about-portrait.png').convert('RGBA')
BUBBLES = [
    ['哈喽大家好呀～', '我是看板娘，欢迎来到', '二次元工具间！'],
    ['五个开源作品：', '樱花雨、星空流星，', '都是我准备的哦！'],
    ['还有可爱的时间问候', '和今日运势签，', '每天来看看有好运！'],
    ['全部免费，全部开源！', '喜欢的话，', '点个关注再走嘛～'],
]


def text_layer(lines, font, fill, pad=30):
    dummy = ImageDraw.Draw(Image.new('RGBA', (10, 10)))
    boxes = []
    w_max = 0
    h_sum = 0
    for ln in lines:
        box = dummy.textbbox((0, 0), ln, font=font)
        boxes.append(box)
        w_max = max(w_max, box[2] - box[0])
        h_sum += box[3] - box[1] + 20
    layer = Image.new('RGBA', (w_max + pad * 2, h_sum + pad * 2), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    yy = pad
    for ln, box in zip(lines, boxes):
        ld.text((pad - box[0], yy - box[1]), ln, font=font, fill=fill)
        yy += box[3] - box[1] + 20
    return layer


def ease_out(t):
    return 1 - (1 - t) ** 3


composed = []
for i in range(P):
    bg_name = bg_frames[i % len(bg_frames)]
    frame = Image.open(os.path.join(TMP, bg_name)).convert('RGBA')

    # ---- 片头 (0-90) ----
    if i < TITLE_END:
        pr = ease_out(i / TITLE_END)
        layer = text_layer(['自己做工具的', '二次元工具间'], F_BIG, (242, 242, 248, int(255 * pr)))
        frame.alpha_composite(layer, (int(W / 2 - layer.width / 2), int(H * 0.33 + (1 - pr) * 60)))
        layer2 = text_layer(['～看板娘带你逛～'], F_MID2, (167, 139, 250, int(235 * pr)))
        frame.alpha_composite(layer2, (int(W / 2 - layer2.width / 2), int(H * 0.33 + layer.height + 30)))
        sm = text_layer([URL_TEXT], F_SMALL, (129, 230, 176, int(230 * pr)))
        frame.alpha_composite(sm, (int(W / 2 - sm.width / 2), int(H * 0.86)))

    # ---- 看板娘主讲 (90-495)：4 个气泡各 ~3.4s ----
    if PRES_START <= i < PRES_END:
        k = min((i - PRES_START) // 100, len(BUBBLES) - 1)
        pr_in = min(1, ((i - PRES_START) % 100) / 12)
        bob = math.sin((i % SEG) / FPS * 2 * math.pi) * 10
        ph = portrait.resize((620, 620))
        px, py = W - 500, H - 580 + int(bob)
        mask = Image.new('L', (620, 620), 0)
        ImageDraw.Draw(mask).rounded_rectangle([0, 0, 620, 620], radius=52, fill=255)
        frame.paste(ph, (px, py), mask)
        fd = ImageDraw.Draw(frame)
        fd.rounded_rectangle([px - 4, py - 4, px + 624, py + 624], radius=56,
                             outline=(248, 158, 192, 235), width=6)
        lines = BUBBLES[k]
        bl = text_layer(lines, F_BUB, (60, 50, 62, 255), pad=36)
        sc = 0.85 + 0.15 * pr_in
        bl = bl.resize((max(1, int(bl.width * sc)), max(1, int(bl.height * sc))))
        bubble = Image.new('RGBA', (bl.width + 28, bl.height + 28), (0, 0, 0, 0))
        bd = ImageDraw.Draw(bubble)
        bd.rounded_rectangle([0, 0, bubble.width, bubble.height], 30, fill=(255, 248, 252, int(242 * pr_in)))
        bubble.alpha_composite(bl, (14, 14))
        bd2 = ImageDraw.Draw(bubble)
        bd2.polygon([(bubble.width - 70, bubble.height - 2), (bubble.width - 14, bubble.height - 2),
                     (bubble.width - 50, bubble.height + 18)], fill=(255, 248, 252, int(242 * pr_in)))
        frame.alpha_composite(bubble, (max(20, px - bl.width - 120), py - bl.height - 40))
        if k == 0:
            tt = text_layer(['Susu · 二次元工具间'], F_MID2,
                            (242, 242, 248, int(235 * min(1, (i - PRES_START) / 20))))
            frame.alpha_composite(tt, (int(W / 2 - tt.width / 2), 150))

    # ---- 片尾 (495-720) ----
    if i >= END_START:
        pr = min(1, (i - END_START) / 18)
        tt = text_layer([URL_TEXT], F_MID, (242, 242, 248, int(255 * pr)))
        frame.alpha_composite(tt, (int(W / 2 - tt.width / 2), int(H * 0.30)))
        tt2 = text_layer(['GitHub 搜索 sdh0219'], F_MID2, (167, 139, 250, int(235 * pr)))
        frame.alpha_composite(tt2, (int(W / 2 - tt2.width / 2), int(H * 0.30) + 140))
        tt3 = text_layer(['抖音搜索 芝士土豆'], F_MID2, (34, 211, 238, int(235 * pr)))
        frame.alpha_composite(tt3, (int(W / 2 - tt2.width / 2), int(H * 0.30) + 250))
        tt4 = text_layer(['主人，点个关注再走嘛～ ＼(^o^)／'], F_SMALL, (247, 158, 190, int(235 * pr)))
        frame.alpha_composite(tt4, (int(W / 2 - tt4.width / 2), int(H * 0.30) + 380))

    frame.convert('RGB').save(os.path.join(TMP, f'c_{i:04d}.jpg'), quality=90)
    if i % 120 == 0:
        print('compose', i)

# 2) 编码 + 音频混流（BGM 延长到 24s + 四段旁白按气泡时间轴插入）
print('encoding...')
filter_complex = (
    '[1:a]apad=whole_dur=24,volume=0.22[b];'
    '[2:a]adelay=4200|4200[n1];'
    '[3:a]adelay=7400|7400[n2];'
    '[4:a]adelay=10600|10600[n3];'
    '[5:a]adelay=13800|13800[n4];'
    '[b][n1][n2][n3][n4]amix=inputs=5:normalize=0[a]'
)
subprocess.run([
    'projects/bilinote/bin/ffmpeg.exe', '-y',
    '-framerate', '30', '-i', os.path.join(TMP, 'c_%04d.jpg'),
    '-i', BGM, '-i', NARR[0], '-i', NARR[1], '-i', NARR[2], '-i', NARR[3],
    '-filter_complex', filter_complex,
    '-map', '0:v', '-map', '[a]',
    '-c:v', 'libx264', '-preset', 'medium', '-crf', '22',
    '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '128k',
    '-t', str(SECONDS), '-movflags', '+faststart', OUT
], check=True, capture_output=True)
print('OUT:', OUT, os.path.getsize(OUT) // 1024, 'KB')
shutil.rmtree(TMP, ignore_errors=True)
print('DONE')
