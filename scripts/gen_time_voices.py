# -*- coding: utf-8 -*-
"""生成看板娘按时段问候语音（edge-tts Xiaoyi）"""
import asyncio
import os

import edge_tts

VOICE = 'zh-CN-XiaoyiNeural'
RATE = '-8%'
PITCH = '+18Hz'
DEST = 'web/assets/voice'

GREETINGS = [
    ('greet-morning.mp3', '早上好呀主人！新的一天也要元气满满哦！'),
    ('greet-noon.mp3', '中午啦，记得吃饭，不要久坐哦！'),
    ('greet-afternoon.mp3', '下午容易犯困呢，来杯咖啡陪陪我嘛！'),
    ('greet-evening.mp3', '晚上好呀，今天辛苦啦！'),
    ('greet-night.mp3', '这么晚还不睡吗？早点休息，晚安喵～'),
]


async def main():
    os.makedirs(DEST, exist_ok=True)
    for name, text in GREETINGS:
        out = os.path.join(DEST, name)
        c = edge_tts.Communicate(text, VOICE, rate=RATE, pitch=PITCH)
        await c.save(out)
        print(name, os.path.getsize(out) // 1024, 'KB')


asyncio.run(main())
