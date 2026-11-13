"""生成二次元 UI 音效包（自托管，无外部依赖）。

用法：python scripts/gen_sfx.py
输出：web/assets/audio/sfx/{pop,chime,don,yoshi}.wav
全部为 44.1kHz 单声道 16bit 合成音，各 < 60KB。
"""
import os
import wave

import numpy as np

SR = 44100
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "web", "assets", "audio", "sfx")


def save(name, samples):
    os.makedirs(OUT, exist_ok=True)
    data = (np.clip(samples, -1.0, 1.0) * 32767).astype("<i2")
    path = os.path.join(OUT, name)
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(data.tobytes())
    print(f"{name}: {os.path.getsize(path)} bytes")


def env(n, attack=0.005, decay="exp"):
    """音量包络：快起指数衰减。"""
    t = np.linspace(0, 1, n)
    e = np.exp(-t * 6)
    a = int(n * attack)
    if a > 0:
        e[:a] *= np.linspace(0, 1, a)
    return e


def pop():
    """点击：短促水泡音，正弦 900→320Hz 下滑 70ms。"""
    dur = 0.07
    n = int(SR * dur)
    t = np.linspace(0, dur, n)
    freq = 900 * np.exp(-t * 18) + 320
    phase = 2 * np.pi * np.cumsum(freq) / SR
    return 0.55 * np.sin(phase) * env(n)


def chime():
    """成功：两音上行铃音 E6→A6，各 140ms。"""
    seg = int(SR * 0.14)
    out = []
    for f in (1318.5, 1760.0):
        t = np.linspace(0, 0.14, seg)
        tone = 0.4 * np.sin(2 * np.pi * f * t) + 0.12 * np.sin(2 * np.pi * f * 2 * t)
        out.append(tone * env(seg))
    return np.concatenate(out)


def don():
    """强调：低频鼓点 150Hz 衰减 180ms + 一点噪声冲击。"""
    dur = 0.18
    n = int(SR * dur)
    t = np.linspace(0, dur, n)
    body = np.sin(2 * np.pi * (150 * np.exp(-t * 8) + 60) * t)
    crack = np.random.default_rng(7).uniform(-1, 1, n) * np.exp(-t * 60) * 0.2
    return 0.7 * (body + crack) * env(n, attack=0.002)


def yoshi():
    """元气：三连上行琶音 C6-E6-G6，各 90ms。"""
    seg = int(SR * 0.09)
    out = []
    for f in (1046.5, 1318.5, 1568.0):
        t = np.linspace(0, 0.09, seg)
        out.append(0.42 * np.sin(2 * np.pi * f * t) * env(seg))
    return np.concatenate(out)


save("pop.wav", pop())
save("chime.wav", chime())
save("don.wav", don())
save("yoshi.wav", yoshi())
print("sfx done ->", OUT)
