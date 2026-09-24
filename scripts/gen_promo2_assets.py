# -*- coding: utf-8 -*-
"""宣传片 v2 素材：看板娘讲解旁白 TTS（更软萌版）+ 片头/片尾卡"""
import asyncio
import os

import edge_tts
from PIL import Image, ImageDraw, ImageFont

VOICE = 'zh-CN-XiaoyiNeural'
RATE = '-12%'
PITCH = '+25Hz'
DEST = 'media/promo2'
W, H = 1080, 1920
URL_TEXT = 'susu-2x9.pages.dev'
os.makedirs(DEST, exist_ok=True)

NARRATION = [
    ('n1.mp3', '哈喽大家好呀～我是看板娘，欢迎来到二次元工具间！'),
    ('n2.mp3', '这里有五个开源作品，樱花雨、星空流星，都是我准备的哦！'),
    ('n3.mp3', '还有可爱的时间问候和今日运势签，每天来看看有好运哦！'),
    ('n4.mp3', '全部免费，全部开源！喜欢的话，点个关注再走嘛～'),
]

BUBBLES = [
    ['哈喽大家好呀～', '我是看板娘，欢迎来到', '二次元工具间！'],
    ['五个开源作品：', '樱花雨、星空流星，', '都是我准备的哦！'],
    ['还有可爱的时间问候', '和今日运势签，', '每天来看看有好运！'],
    ['全部免费，全部开源！', '喜欢的话，', '点个关注再走嘛～'],
]


def night_bg():
    bg = Image.new('RGB', (W, H))
    d = Image.new('RGB', (W, H))
    dd = ImageDraw.Draw(d)
    for y in range(H):
        k = y / H
        dd.line([(0, y), (W, y)], fill=(int(18 - 8 * k), int(14 - 6 * k), int(36 - 20 * k)))
    glow = Image.new('L', (W, H), 0)
    gd = ImageDraw.Draw(glow)
    for i in range(200):
        gd.ellipse([W * 0.6 - i * 2.2, -280 + i * 1.3, W * 0.6 + i * 2.2, 280 - i * 1.3], fill=int(50 * (1 - i / 200)))
    purple = Image.new('RGB', (W, H), (96, 60, 168))
    bg.paste(Image.composite(purple, bg, glow), (0, 0))
    import random
    rnd = random.Random(42)
    for _ in range(120):
        x, y = rnd.random() * W, rnd.random() * H
        r = rnd.random() * 1.8 + 0.6
        dd.ellipse([x - r, y - r, x + r, y + r], fill=(226, 229, 248, int(rnd.random() * 180 + 60)))
    for _ in range(14):
        x, y = rnd.random() * W, rnd.random() * H
        r = rnd.random() * 10 + 6
        dd.polygon([(x, y - r), (x + r * 0.8, y - r * 0.3), (x + r * 0.5, y + r * 0.8),
                    (x - r * 0.5, y + r * 0.8), (x - r * 0.8, y - r * 0.3)],
                   fill=(247, 158, 190, 160))
    return bg


def make_cards():
    f_big = ImageFont.truetype('C:/Windows/Fonts/msyhbd.ttc', 92)
    f_mid = ImageFont.truetype('C:/Windows/Fonts/msyh.ttc', 54)
    f_small = ImageFont.truetype('C:/Windows/Fonts/msyh.ttc', 40)
    # 片头卡
    bg = night_bg()
    d = ImageDraw.Draw(bg)
    d.text((W / 2, 620), '自己做工具的', font=f_big, fill=(242, 242, 248), anchor='mm')
    d.text((W / 2, 760), '二次元工具间', font=f_big, fill=(247, 158, 190), anchor='mm')
    d.text((W / 2, 910), '～看板娘带你逛～', font=f_mid, fill=(167, 139, 250), anchor='mm')
    d.text((W / 2, 1790), URL_TEXT, font=f_small, fill=(129, 230, 176), anchor='mm')
    bg.save(os.path.join(DEST, 'card-title.png'))
    # 片尾卡（平台匹配版）
    bg2 = night_bg()
    d2 = ImageDraw.Draw(bg2)
    d2.text((W / 2, 480), URL_TEXT, font=ImageFont.truetype('C:/Windows/Fonts/msyhbd.ttc', 78),
            fill=(242, 242, 248), anchor='mm')
    d2.text((W / 2, 660), 'GitHub 搜索 sdh0219', font=f_mid, fill=(167, 139, 250), anchor='mm')
    d2.text((W / 2, 780), '抖音搜索 芝士土豆', font=f_mid, fill=(34, 211, 238), anchor='mm')
    d2.text((W / 2, 930), '主人，点个关注再走嘛～ ＼(^o^)／', font=f_small, fill=(247, 158, 190), anchor='mm')
    bg2.save(os.path.join(DEST, 'card-end.png'))
    print('cards ok')


async def gen_narration():
    for name, text in NARRATION:
        out = os.path.join(DEST, name)
        c = edge_tts.Communicate(text, VOICE, rate=RATE, pitch=PITCH)
        await c.save(out)
        print(name, os.path.getsize(out) // 1024, 'KB')


if __name__ == '__main__':
    make_cards()
    asyncio.run(gen_narration())
    print('assets done')
