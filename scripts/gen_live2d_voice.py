# -*- coding: utf-8 -*-
"""Generate kawaii kanban-musume voice files via Edge neural TTS."""
import asyncio
import os

import edge_tts

VOICE = 'zh-CN-XiaoyiNeural'
RATE = '-8%'
PITCH = '+18Hz'
DEST = 'web/assets/voice'

LINES = [
    ('p0.mp3', '你好呀，我是这里的看板娘，点点我会有惊喜哦！'),
    ('p1.mp3', '今天也要元气满满哦！'),
    ('p2.mp3', '代码写累了，就休息一下嘛～'),
    ('p3.mp3', '偷偷告诉你，右上角的小太阳可以切换浅色主题！'),
    ('p4.mp3', '浅色主题里会下樱花雨，快去看看呀！'),
    ('p5.mp3', '发现页面坏掉了？邮件告诉主人哦！'),
    ('p6.mp3', '工具用得顺手的话，给项目点颗小星星嘛～'),
    ('p7.mp3', '博客里有新的随笔，去读读嘛～'),
    ('p8.mp3', '主人主人，今天也要开心哦！'),
]


async def gen(name, text):
    out = os.path.join(DEST, name)
    c = edge_tts.Communicate(text, VOICE, rate=RATE, pitch=PITCH)
    await c.save(out)
    size = os.path.getsize(out)
    print(f'{name}: {size // 1024}KB  "{text}"')


async def main():
    os.makedirs(DEST, exist_ok=True)
    for name, text in LINES:
        for attempt in range(3):
            try:
                await gen(name, text)
                break
            except Exception as e:  # noqa: BLE001
                print(f'{name} attempt {attempt + 1} failed: {e}')
                if attempt == 2:
                    raise
                await asyncio.sleep(2)


asyncio.run(main())
print('all voice files generated')
