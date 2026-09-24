# -*- coding: utf-8 -*-
"""生成音乐盒另外两首循环曲：战斗风(小调快节奏) / 像素风(跳跃琶音)"""
import os
import subprocess
import wave

import numpy as np

SR = 44100
E8 = int(0.5 * (60 / 150) * SR)  # 150bpm 八分音符


def tone(f, n, vol, decay):
    tt = np.arange(n) / SR
    seg = (np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(4 * np.pi * f * tt)) * np.exp(-tt * decay) * vol
    return np.tanh(seg * 1.6)


def build(note_seq, bass_seq, seconds):
    n_total = int(seconds * SR)
    mel = np.zeros(n_total)
    bass = np.zeros(n_total)
    pos = 0
    i = 0
    while pos < n_total:
        f = note_seq[i % len(note_seq)]
        n = min(E8 * 2, n_total - pos)
        if n > 0:
            mel[pos:pos + n] += tone(f, n, 0.2, 4)
        pos += E8
        i += 1
    pos = 0
    i = 0
    while pos < n_total:
        f, dur = bass_seq[i % len(bass_seq)]
        n = min(dur, n_total - pos)
        if n > 0:
            bass[pos:pos + n] += tone(f, n, 0.14, 2)
        pos += dur
        i += 1
    mix = np.tanh(mel + bass) * 0.55
    return (mix / np.max(np.abs(mix)) * 32767 * 0.8).astype(np.int16)


def write(pcm, wav_path, mp3_path):
    with wave.open(wav_path, 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    subprocess.run([
        'projects/bilinote/bin/ffmpeg.exe', '-y', '-i', wav_path,
        '-c:a', 'libmp3lame', '-b:a', '48k', mp3_path
    ], check=True, capture_output=True)
    print(mp3_path, os.path.getsize(mp3_path) // 1024, 'KB')


SECONDS = 32
BATTLE_NOTES = [220.0, 261.63, 329.63, 440.0, 523.25, 440.0, 329.63, 261.63]
BATTLE_BASS = [(110.0, E8 * 4), (82.41, E8 * 4)]
PX_NOTES = [523.25, 659.25, 783.99, 659.25, 587.33, 783.99, 880.0, 783.99]
PX_BASS = [(130.81, E8 * 2), (196.0, E8 * 2)]

os.makedirs('media', exist_ok=True)
write(build(BATTLE_NOTES, BATTLE_BASS, SECONDS), 'media/bgm-battle.wav', 'web/assets/audio/bgm-battle.mp3')
write(build(PX_NOTES, PX_BASS, SECONDS), 'media/bgm-pixel.wav', 'web/assets/audio/bgm-pixel.mp3')
