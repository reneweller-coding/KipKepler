"""Synthesises the ambience beds under the music, one per level theme: assets/ambience/<theme>.ogg (stereo, 24 s,
seamless loops, quiet: -30 LUFS). The game plays the theme's bed with the effects volume.

    python tools/sfx/make_ambience.py              # all eight
    python tools/sfx/make_ambience.py ice hive     # only these

Everything is computed here (filtered noise, oscillators, sparse events), deterministic (fixed seeds), no samples.
"""
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy import signal

SR = 44100
LOOP = 24.0
FADE = 4.0
TARGET_LUFS = -30.0
PEAK_DB = -6.0
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "assets" / "ambience"
N = int(LOOP * SR)
M = int((LOOP + FADE) * SR)


# ----------------------------------------------------------------------------------------------------- blocks

def t_of(n=M):
    return np.arange(n) / SR


def noise(rng, n=M):
    return rng.standard_normal(n)


def brown(rng, n=M):
    x = np.cumsum(rng.standard_normal(n))
    x = signal.lfilter([1, -1], [1, -0.995], x)   # keeps the walk from drifting off
    return x / (np.max(np.abs(x)) + 1e-9)


def band(x, lo, hi, order=2):
    sos = signal.butter(order, [lo, hi], btype="bandpass", fs=SR, output="sos")
    return signal.sosfilt(sos, x)


def low(x, f, order=2):
    return signal.sosfilt(signal.butter(order, f, btype="lowpass", fs=SR, output="sos"), x)


def high(x, f, order=2):
    return signal.sosfilt(signal.butter(order, f, btype="highpass", fs=SR, output="sos"), x)


def lfo(rate, phase=0.0, depth=1.0, n=M):
    return 1.0 - depth * 0.5 * (1.0 - np.cos(2 * np.pi * rate * t_of(n) + phase))


def sweep_band(x, centre, q=4.0, block=2048):
    """A band pass whose centre follows `centre` (an array per sample), applied block by block."""
    out = np.zeros_like(x)
    zi = None
    for s in range(0, len(x), block):
        c = float(np.clip(centre[min(s + block // 2, len(x) - 1)], 40, SR * 0.45))
        b, a = signal.iirpeak(c, q, fs=SR)
        if zi is None:
            zi = signal.lfilter_zi(b, a) * 0
        out[s:s + block], zi = signal.lfilter(b, a, x[s:s + block], zi=zi)
    return out


def env(n, attack, decay):
    t = np.arange(n) / SR
    return np.minimum(1.0, t / max(attack, 1e-4)) * np.exp(-t / decay)


def place(dst, ev, at, pan):
    """Adds a mono event at sample `at`, panned (0 left .. 1 right)."""
    at = int(at)
    if at >= dst.shape[0]:
        return
    n = min(len(ev), dst.shape[0] - at)
    dst[at:at + n, 0] += ev[:n] * np.cos(pan * np.pi / 2)
    dst[at:at + n, 1] += ev[:n] * np.sin(pan * np.pi / 2)


def stereo(l, r=None):
    return np.stack([l, l if r is None else r], axis=1)


def blip(f, d, rng, shape="sine"):
    t = np.arange(int(d * SR)) / SR
    if shape == "sine":
        w = np.sin(2 * np.pi * f * t)
    else:
        w = signal.square(2 * np.pi * f * t) * 0.5
    return w * env(len(t), 0.004, d / 4)


def drip(rng):
    d = 0.18
    t = np.arange(int(d * SR)) / SR
    f = rng.uniform(900, 1700) * np.exp(-t / 0.03) + rng.uniform(500, 800)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * env(len(t), 0.001, 0.035)


def creak(rng):
    d = rng.uniform(0.6, 1.3)
    n = int(d * SR)
    t = np.arange(n) / SR
    f = rng.uniform(140, 260) * (1 + 0.25 * np.sin(2 * np.pi * rng.uniform(1, 3) * t))
    saw = signal.sawtooth(2 * np.pi * np.cumsum(f) / SR)
    grit = (rng.random(n) < f / SR * 1.5).astype(float)
    x = low(saw * 0.4 + grit, 1800)
    return x * np.sin(np.pi * t / d) ** 2


def clank(rng, base):
    d = 1.2
    n = int(d * SR)
    t = np.arange(n) / SR
    x = np.zeros(n)
    for k, ratio in enumerate([1.0, 2.76, 5.40, 8.93]):
        x += np.sin(2 * np.pi * base * ratio * t + rng.uniform(0, 6)) * np.exp(-t / (0.35 / (1 + k))) / (1 + k)
    hit = noise(rng, n) * env(n, 0.0005, 0.01)
    return x * 0.6 + band(hit, 800, 6000) * 0.5


def chime(rng, f):
    d = 4.0
    n = int(d * SR)
    t = np.arange(n) / SR
    x = np.zeros(n)
    for k, (ratio, a) in enumerate([(1.0, 1.0), (2.01, 0.5), (3.98, 0.25), (5.43, 0.12)]):
        x += a * np.sin(2 * np.pi * f * ratio * t) * np.exp(-t / (1.6 / (1 + 0.6 * k)))
    return x * env(n, 0.003, 10.0)


def crack(rng):
    d = 0.5
    n = int(d * SR)
    x = noise(rng, n) * env(n, 0.0003, 0.012)
    out = np.zeros(n)
    for f in rng.uniform(1500, 5000, 3):
        b, a = signal.iirpeak(f, 25, fs=SR)
        out += signal.lfilter(b, a, x)
    return out + 0.3 * x


def chirp_call(rng):
    d = rng.uniform(0.25, 0.5)
    n = int(d * SR)
    t = np.arange(n) / SR
    f0, f1 = rng.uniform(1800, 3200), rng.uniform(900, 4200)
    f = f0 + (f1 - f0) * (t / d) ** 0.7 + 180 * np.sin(2 * np.pi * rng.uniform(18, 30) * t)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * t / d) ** 1.5


def thump(rng, f=48):
    d = 0.7
    n = int(d * SR)
    t = np.arange(n) / SR
    fr = f * (1 + 1.5 * np.exp(-t / 0.03))
    return np.sin(2 * np.pi * np.cumsum(fr) / SR) * env(n, 0.002, 0.18)


def hiss(rng, d):
    n = int(d * SR)
    t = np.arange(n) / SR
    return high(noise(rng, n), 2500) * np.minimum(1, t / 0.08) * np.exp(-t / (d / 3))


def events(rng, count, lo=0.0, hi=LOOP + FADE):
    return np.sort(rng.uniform(lo, hi, count))


# ----------------------------------------------------------------------------------------------------- themes

def station(rng):
    t = t_of()
    hum = (np.sin(2 * np.pi * 50 * t) + 0.5 * np.sin(2 * np.pi * 100.4 * t) + 0.2 * np.sin(2 * np.pi * 150 * t)) * 0.12
    air_l, air_r = low(noise(rng), 700) * 0.5, low(noise(rng), 700) * 0.5
    x = stereo(hum + air_l * lfo(0.07, 0, 0.3), hum + air_r * lfo(0.05, 1, 0.3))
    for s in events(rng, 9):
        note = rng.choice([1200, 1500, 1800, 2400])
        ev = np.concatenate([blip(note, 0.09, rng), np.zeros(int(0.05 * SR)), blip(note * 1.25, 0.09, rng)])
        place(x, ev * 0.05, s * SR, rng.uniform(0.2, 0.8))
    for s in events(rng, 3):
        place(x, hiss(rng, 1.5) * 0.04, s * SR, rng.uniform(0.1, 0.9))
    return x


def hull(rng):
    t = t_of()
    rumble = low(brown(rng), 120) * 0.8
    wind_l = sweep_band(noise(rng), 300 + 220 * np.sin(2 * np.pi * 0.04 * t), 3) * 0.25
    wind_r = sweep_band(noise(rng), 320 + 220 * np.sin(2 * np.pi * 0.05 * t + 1.5), 3) * 0.25
    x = stereo(rumble + wind_l, rumble + wind_r)
    for s in events(rng, 6):
        place(x, creak(rng) * 0.12, s * SR, rng.uniform(0.1, 0.9))
    for s in events(rng, 3):
        place(x, clank(rng, rng.uniform(180, 320)) * 0.08, s * SR, rng.uniform(0.2, 0.8))
    return x


def jungle(rng):
    t = t_of()
    leaves_l = band(noise(rng), 1500, 6000) * 0.10 * lfo(0.11, 0, 0.6)
    leaves_r = band(noise(rng), 1500, 6000) * 0.10 * lfo(0.09, 2, 0.6)
    # Insects: a high carrier, pulsed fast, swelling slowly.
    ins = np.sin(2 * np.pi * 5200 * t) * (0.5 + 0.5 * signal.square(2 * np.pi * 34 * t, 0.3)) * lfo(0.08, 0, 0.9) * 0.03
    ins2 = np.sin(2 * np.pi * 4300 * t) * (0.5 + 0.5 * signal.square(2 * np.pi * 22 * t, 0.4)) * lfo(0.06, 3, 0.9) * 0.025
    # Frogs: a low croak pulse.
    frog = np.sin(2 * np.pi * 180 * t + 3 * np.sin(2 * np.pi * 90 * t)) * (signal.square(2 * np.pi * 1.6 * t, 0.12) > 0)
    frog = low(frog, 900) * lfo(0.05, 1, 1.0) * 0.05
    x = stereo(leaves_l + ins + frog * 0.6, leaves_r + ins2 + frog)
    for s in events(rng, 12):
        place(x, chirp_call(rng) * 0.06, s * SR, rng.uniform(0.0, 1.0))
    return x


def hive(rng):
    t = t_of()
    throb = low(brown(rng), 90) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.9 * t)) * 0.9
    buzz = low(signal.sawtooth(2 * np.pi * (140 + 6 * np.sin(2 * np.pi * 0.3 * t)) * t), 1200) * lfo(0.13, 0, 0.8) * 0.035
    buzz2 = low(signal.sawtooth(2 * np.pi * (152 + 5 * np.sin(2 * np.pi * 0.21 * t)) * t), 1200) * lfo(0.1, 2, 0.8) * 0.035
    wet = band(noise(rng), 200, 900) * 0.06 * lfo(0.2, 0, 0.7)
    x = stereo(throb + buzz + wet, throb + buzz2 + wet)
    for s in events(rng, 22):
        place(x, drip(rng) * 0.10, s * SR, rng.uniform(0.0, 1.0))
    return x


def ice(rng):
    t = t_of()
    wl = sweep_band(noise(rng), 700 + 500 * np.sin(2 * np.pi * 0.05 * t) + 200 * np.sin(2 * np.pi * 0.17 * t), 5) * 0.30
    wr = sweep_band(noise(rng), 760 + 520 * np.sin(2 * np.pi * 0.045 * t + 2) + 180 * np.sin(2 * np.pi * 0.13 * t), 5) * 0.30
    hiss_l, hiss_r = high(noise(rng), 5000) * 0.015, high(noise(rng), 5000) * 0.015
    x = stereo(wl * lfo(0.06, 0, 0.5) + hiss_l, wr * lfo(0.07, 1, 0.5) + hiss_r)
    for s in events(rng, 5):
        place(x, crack(rng) * 0.10, s * SR, rng.uniform(0.1, 0.9))
    return x


def crystal(rng):
    t = t_of()
    pad = sum(np.sin(2 * np.pi * f * t + rng.uniform(0, 6)) * a for f, a in [(110, 0.05), (165, 0.04), (220.6, 0.03), (330, 0.02)])
    pad = pad * lfo(0.05, 0, 0.5)
    air_l, air_r = band(noise(rng), 3000, 9000) * 0.02, band(noise(rng), 3000, 9000) * 0.02
    x = stereo(pad + air_l, pad * 0.9 + air_r)
    scale = [880, 990, 1108.7, 1318.5, 1480, 1760, 1975.5]
    for s in events(rng, 14):
        place(x, chime(rng, float(rng.choice(scale))) * 0.05, s * SR, rng.uniform(0.0, 1.0))
    return x


def foundry(rng):
    t = t_of()
    roar = low(brown(rng), 150) * 1.0 + band(noise(rng), 80, 400) * 0.10 * lfo(0.15, 0, 0.5)
    fire_l, fire_r = band(noise(rng), 400, 2500) * 0.03, band(noise(rng), 400, 2500) * 0.03
    x = stereo(roar + fire_l, roar + fire_r)
    # The machine's beat: a thump every 1.5 s (24 s hold 16 of them, so the loop keeps the beat).
    for k in range(int((LOOP + FADE) / 1.5)):
        place(x, thump(rng) * 0.35, k * 1.5 * SR, 0.5)
        place(x, clank(rng, 140) * 0.03, (k * 1.5 + 0.75) * SR, 0.35 if k % 2 else 0.65)
    for s in events(rng, 4):
        place(x, hiss(rng, 2.2) * 0.07, s * SR, rng.uniform(0.1, 0.9))
    return x


def citadel(rng):
    t = t_of()
    hum = sum(np.sin(2 * np.pi * 55 * k * t) / k for k in range(1, 7)) * 0.07 * lfo(0.25, 0, 0.3)
    sub = np.sin(2 * np.pi * 36 * t) * (0.5 + 0.5 * np.sin(2 * np.pi * (2 / 3) * t)) * 0.18
    drone = low(signal.sawtooth(2 * np.pi * 73.4 * t) + signal.sawtooth(2 * np.pi * 73.9 * t), 400) * 0.03
    x = stereo(hum + sub + drone, hum + sub + drone)
    for s in events(rng, 10):
        n = int(rng.integers(4, 9))
        ev = np.concatenate([blip(float(rng.choice([2200, 2600, 3100, 3500])), 0.035, rng, "square") for _ in range(n)])
        place(x, ev * 0.03, s * SR, rng.uniform(0.0, 1.0))
    return x


THEMES = {"station": station, "hull": hull, "jungle": jungle, "hive": hive, "ice": ice, "crystal": crystal,
          "foundry": foundry, "citadel": citadel}


# ----------------------------------------------------------------------------------------------------- loudness

def kweight(x, fs):
    g, q, fc = 3.999843853973347, 0.7071752369554196, 1681.974450955533
    a = 10.0 ** (g / 40.0)
    w0 = 2.0 * np.pi * fc / fs
    alpha = np.sin(w0) / (2.0 * q)
    c, s = np.cos(w0), 2.0 * np.sqrt(a) * alpha
    b1 = [a * ((a + 1) + (a - 1) * c + s), -2 * a * ((a - 1) + (a + 1) * c), a * ((a + 1) + (a - 1) * c - s)]
    a1 = [(a + 1) - (a - 1) * c + s, 2 * ((a - 1) - (a + 1) * c), (a + 1) - (a - 1) * c - s]
    q, fc = 0.5003270373238773, 38.13547087602444
    w0 = 2.0 * np.pi * fc / fs
    alpha = np.sin(w0) / (2.0 * q)
    return signal.lfilter([1.0, -2.0, 1.0], [1.0 + alpha, -2.0 * np.cos(w0), 1.0 - alpha],
                          signal.lfilter(b1, a1, x, axis=0), axis=0)


def lufs(x, fs):
    y = kweight(x, fs)
    block, hop = int(0.4 * fs), int(0.1 * fs)
    powers = np.array([float(np.mean(np.sum(y[s:s + block] ** 2, axis=1))) for s in range(0, len(y) - block + 1, hop)])
    loud = -0.691 + 10 * np.log10(np.maximum(powers, 1e-12))
    gated = powers[loud > -70]
    rel = -0.691 + 10 * np.log10(np.mean(gated)) - 10
    return -0.691 + 10 * np.log10(np.mean(powers[(loud > -70) & (loud > rel)]))


def make(name):
    rng = np.random.default_rng(sum(map(ord, name)) * 7919)
    x = high(THEMES[name](rng).T, 25).T
    # Seamless: the tail beyond the loop fades into its start (equal power).
    f = int(FADE * SR)
    w = np.sin(np.linspace(0, np.pi / 2, f))[:, None]
    out = x[:N].copy()
    out[:f] = out[:f] * w + x[N:N + f] * np.cos(np.linspace(0, np.pi / 2, f))[:, None]
    gain = min(TARGET_LUFS - lufs(out, SR), PEAK_DB - 20 * np.log10(np.max(np.abs(out)) + 1e-9))
    out *= 10 ** (gain / 20)
    OUT.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(suffix=".wav")
    os.close(fd)
    try:
        sf.write(tmp, out.astype(np.float32), SR, subtype="FLOAT")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", tmp, "-c:a", "libvorbis", "-q:a", "3",
                        str(OUT / (name + ".ogg"))], check=True)
    finally:
        os.remove(tmp)
    print("%-8s %+.1f dB  %.0f kB" % (name, gain, (OUT / (name + ".ogg")).stat().st_size / 1024))


if __name__ == "__main__":
    for name in sys.argv[1:] or THEMES:
        make(name)
