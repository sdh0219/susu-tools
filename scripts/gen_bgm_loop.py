# -*- coding: utf-8 -*-
"""生成看板娘音乐盒的循环 BGM（软萌 8-bit，48 秒可循环）"""
import os
import subprocess
import wave

import numpy as np

SR = 44100
BPM = 108
EIGHTH = 60 / BPM / 2
SECONDS = 48
N = int(SECONDS * SR)

NOTE = {
    'C4': 261.63, 'D4': 293.66, 'E4': 329.63, 'G4': 392.0, 'A4': 440.0,
    'C5': 523.25, 'D5': 587.33, 'E5': 659.25, 'G5': 783.99, 'A5': 880.0,
}

# 主旋律（八分音符序列，96 个 = 48 秒），C 大调五声，软萌上行下行
MEL = (
    ['E5', 'G5', 'A5', 'G5', 'E5', 'D5', 'C5', 'D5'] * 2
    + ['E5', 'G5', 'A5', 'C6' if False else 'A5', 'G5', 'E5', 'G5', 'A5'] * 2
    + ['C5', 'E5', 'G5', 'E5', 'A5', 'G5', 'E5', 'D5'] * 2
    + ['E5', 'D5', 'C5', 'D5', 'E5', 'G5', 'E5', 'D5'] * 2
)
MEL = MEL[:96]

# 低音（每 4 个八分音符换一次根音）
BASS_SEQ = (['C4', 'G4'] * 12 + ['A4', 'E5'] * 6 + ['C4', 'G4'] * 12 + ['F4' if False else 'G4', 'D5'] * 6)[:96]
BASS_F = {'C4': 130.81, 'G4': 196.0, 'A4': 220.0, 'E5': 164.81, 'D5': 146.83}


def tone(f, n, vol, decay):
    tt = np.arange(n) / SR
    seg = (np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(4 * np.pi * f * tt)) * np.exp(-tt * decay) * vol
    return np.tanh(seg * 1.6)


mel = np.zeros(N)
bass = np.zeros(N)
for i, name in enumerate(MEL):
    pos = int(i * EIGHTH * SR)
    n = min(int(EIGHTH * SR * 1.6), N - pos)
    if n <= 0:
        break
    mel[pos:pos + n] += tone(NOTE[name], n, 0.22, 5)

for i, name in enumerate(BASS_SEQ[:96]):
    pos = int(i * EIGHTH * 2 * SR)
    n = min(int(EIGHTH * 2 * SR * 1.5), N - pos)
    if n <= 0:
        break
    bass[pos:pos + n] += tone(BASS_F[name], n, 0.16, 3)

mix = np.tanh(mel + bass) * 0.55
pcm = (mix / np.max(np.abs(mix)) * 32767 * 0.8).astype(np.int16)

wav_path = 'media/bgm-loop.wav'
os.makedirs('media', exist_ok=True)
with wave.open(wav_path, 'wb') as w:
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())

mp3 = 'web/assets/audio/bgm-loop.mp3'
os.makedirs('web/assets/audio', exist_ok=True)
subprocess.run([
    'projects/bilinote/bin/ffmpeg.exe', '-y', '-i', wav_path,
    '-c:a', 'libmp3lame', '-b:a', '48k', mp3
], check=True, capture_output=True)
os.remove(wav_path)
print('bgm-loop.mp3', os.path.getsize(mp3) // 1024, 'KB')
