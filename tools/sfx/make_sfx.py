"""Synthesises every sound effect of Kip Kepler (docs/DESIGN.md "Sounds") into assets/sound/<name>.wav.

Modern retro sci-fi: layered oscillators with pitch envelopes, filtered noise, FM, decaying-noise tails, bit-crush
only as seasoning. Everything is computed here, deterministic (fixed seeds), no samples.

    python tools/sfx/make_sfx.py              # all sounds + work/sfx/levels.txt + contact sheets
    python tools/sfx/make_sfx.py shoot jump   # only these (levels/contact sheets cover the written ones)
    python tools/sfx/make_sfx.py --list       # the names

Output: 44.1 kHz, 16 bit, mono, peaks <= -1 dBFS, 1.5 ms fade-in, short fade-out, ends trimmed.
Loudness: every sound gets a target (max momentary loudness over 100 ms, K-weighted, "LU" below); frequent sounds
(step, land, jump, shoot) sit lowest, rare events (boss, extra life, big explosions) highest.
"""
import argparse
import sys
import wave
from pathlib import Path

import numpy as np
from scipy import signal
from scipy.ndimage import minimum_filter1d, uniform_filter1d

SR = 44100
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "assets" / "sound"
WORK = ROOT / "work" / "sfx"
CEILING_DB = -1.1  # a hair under -1 dBFS so int16 rounding never crosses it


# ---------------------------------------------------------------------------------------------------------------
# Building blocks
# ---------------------------------------------------------------------------------------------------------------

def n_of(d):
    return max(1, int(round(d * SR)))


def tt(d):
    return np.arange(n_of(d)) / SR


def mtof(m):
    return 440.0 * 2.0 ** ((m - 69) / 12.0)


def F(freq, d=None):
    """A frequency (or any control) as a per-sample array."""
    if np.isscalar(freq):
        return np.full(n_of(d), float(freq))
    return np.asarray(freq, dtype=np.float64)


def glide(f0, f1, d, tau):
    """Exponential approach from f0 towards f1 with time constant tau."""
    return f1 + (f0 - f1) * np.exp(-tt(d) / tau)


def expseg(f0, f1, d, shape=1.0):
    """Exponential (musical) interpolation from f0 to f1 over d; shape < 1 = fast start."""
    x = np.linspace(0.0, 1.0, n_of(d)) ** shape
    return f0 * (f1 / f0) ** x


def hold(f, d):
    return np.full(n_of(d), float(f))


def cat(*parts):
    return np.concatenate([np.atleast_1d(np.asarray(p, dtype=np.float64)) for p in parts])


def fit(x, n):
    """Pads with the last value or cuts to n samples."""
    x = np.asarray(x, dtype=np.float64)
    if len(x) >= n:
        return x[:n]
    return np.concatenate([x, np.full(n - len(x), x[-1] if len(x) else 0.0)])


def endfade(x, sec=0.004):
    """Brings the last few ms smoothly to zero, so a layer that stops while still sounding does not click."""
    x = np.array(x, dtype=np.float64)
    k = min(len(x) // 4, n_of(sec))
    if k > 1:
        x[len(x) - k:] *= np.cos(np.linspace(0, np.pi / 2, k)) ** 2
    return x


def decay(d, tau, attack=0.001):
    """Exponential decay with a smooth (sin^2) attack; ends at zero."""
    t = tt(d)
    e = np.exp(-t / tau)
    if attack > 0:
        a = np.clip(t / attack, 0.0, 1.0)
        e = e * np.sin(a * np.pi / 2) ** 2
    return endfade(e)


def adsr(d, a, dc, s, r):
    """Attack, decay to sustain level s, release over the last r seconds; total length d."""
    n = n_of(d)
    t = tt(d)
    e = np.where(t < a, np.sin(np.clip(t / max(a, 1e-6), 0, 1) * np.pi / 2) ** 2,
                 s + (1 - s) * np.exp(-(t - a) / max(dc, 1e-6)))
    nr = min(n, n_of(r))
    e[n - nr:] *= np.cos(np.linspace(0, np.pi / 2, nr)) ** 2
    return e


def swell(d, power=2.0):
    """Rising envelope 0 -> 1 (a reverse decay)."""
    return np.linspace(0.0, 1.0, n_of(d)) ** power


def phase_of(freq, ph0=0.0):
    return ph0 + np.cumsum(freq) / SR


def sine(freq, d=None, ph0=0.0):
    return np.sin(2 * np.pi * phase_of(F(freq, d), ph0))


def _blep(p, dt):
    out = np.zeros_like(p)
    m = p < dt
    x = p[m] / dt[m]
    out[m] = x + x - x * x - 1.0
    m = p > 1.0 - dt
    x = (p[m] - 1.0) / dt[m]
    out[m] = x * x + x + x + 1.0
    return out


def saw(freq, d=None, ph0=0.0):
    """Band-limited (PolyBLEP) sawtooth."""
    f = F(freq, d)
    dt = np.clip(np.abs(f) / SR, 1e-7, 0.5)
    p = phase_of(f, ph0) % 1.0
    return 2.0 * p - 1.0 - _blep(p, dt)


def square(freq, d=None, pw=0.5, ph0=0.0):
    """Band-limited pulse (difference of two saws); pw may be an array."""
    f = F(freq, d)
    dt = np.clip(np.abs(f) / SR, 1e-7, 0.5)
    p = phase_of(f, ph0) % 1.0
    p2 = (p + pw) % 1.0
    s = (2.0 * p - _blep(p, dt)) - (2.0 * p2 - _blep(p2, dt))
    return s - np.mean(s)


def tri(freq, d=None, ph0=0.0):
    p = phase_of(F(freq, d), ph0 + 0.25) % 1.0
    return 4.0 * np.abs(p - 0.5) - 1.0


def fm(fc, ratio, index, d=None):
    """Two-operator FM: carrier fc (array or scalar), modulator fc*ratio, index (array or scalar)."""
    if d is None and np.isscalar(fc) and not np.isscalar(index):
        d = len(index) / SR
    f = F(fc, d)
    n = len(f)
    idx = fit(F(index, n / SR), n) if not np.isscalar(index) else np.full(n, float(index))
    mod = np.sin(2 * np.pi * phase_of(f * ratio))
    return np.sin(2 * np.pi * phase_of(f) + idx * mod)


def noise(d, seed):
    return np.random.default_rng(seed).standard_normal(n_of(d))


def _sos(kind, fc, order):
    if kind == "band":
        lo, hi = fc
        return signal.butter(order, [max(lo, 10), min(hi, SR * 0.45)], "bandpass", fs=SR, output="sos")
    return signal.butter(order, min(max(fc, 10), SR * 0.45), kind, fs=SR, output="sos")


def lp(x, fc, order=2):
    return signal.sosfilt(_sos("low", fc, order), x)


def hp(x, fc, order=2):
    return signal.sosfilt(_sos("high", fc, order), x)


def bp(x, lo, hi, order=2):
    return signal.sosfilt(_sos("band", (lo, hi), order), x)


def svf(x, fc, q=0.707, mode="lp"):
    """Time-varying state-variable filter (TPT); fc and q may be arrays. mode lp, bp, hp."""
    x = np.asarray(x, dtype=np.float64)
    n = len(x)
    fc = fit(F(fc, n / SR), n) if not np.isscalar(fc) else np.full(n, float(fc))
    q = fit(F(q, n / SR), n) if not np.isscalar(q) else np.full(n, float(q))
    g = np.tan(np.pi * np.clip(fc, 15.0, SR * 0.45) / SR)
    k = 1.0 / q
    a1 = 1.0 / (1.0 + g * (g + k))
    a2 = g * a1
    a3 = g * a2
    xs, A1, A2, A3, K = x.tolist(), a1.tolist(), a2.tolist(), a3.tolist(), k.tolist()
    out = [0.0] * n
    ic1 = ic2 = 0.0
    m = {"lp": 0, "bp": 1, "hp": 2}[mode]
    for i in range(n):
        v0 = xs[i]
        v3 = v0 - ic2
        v1 = A1[i] * ic1 + A2[i] * v3
        v2 = ic2 + A2[i] * ic1 + A3[i] * v3
        ic1 = 2.0 * v1 - ic1
        ic2 = 2.0 * v2 - ic2
        out[i] = v2 if m == 0 else (v1 if m == 1 else v0 - K[i] * v1 - v2)
    return np.array(out)


def drive(x, amount):
    return np.tanh(x * amount) / np.tanh(amount)


def crush(x, bits=8, hold_n=2, mix=0.35):
    """Bit-crush seasoning: sample-and-hold plus quantisation, blended in."""
    y = np.repeat(x[::hold_n], hold_n)[: len(x)]
    q = 2.0 ** (bits - 1)
    y = np.round(y * q) / q
    return x * (1 - mix) + y * mix


def at(x, t0):
    """Delays x by t0 seconds."""
    return np.concatenate([np.zeros(n_of(t0) if t0 > 0 else 0), np.asarray(x, dtype=np.float64)])


def mix(*parts):
    """Sums layers of different lengths; each layer's end is faded so it cannot click."""
    n = max(len(p) for p in parts)
    out = np.zeros(n)
    for p in parts:
        out[: len(p)] += endfade(p, 0.002)
    return out


def norm(x):
    p = np.max(np.abs(x))
    return x / p if p > 0 else x


def tail(x, rt=0.4, wet=0.2, bright=7000.0, seed=1, predelay=0.008):
    """Short space: convolution with decaying, darkening noise (plus a few early reflections)."""
    rng = np.random.default_rng(seed)
    n = n_of(rt * 1.1 + predelay)
    t = np.arange(n) / SR
    ir = rng.standard_normal(n)
    lo = lp(ir, 1800.0)
    hi = ir - lo
    ir = lo * np.exp(-6.9 * t / rt) + hi * np.exp(-6.9 * t / (rt * 0.45))
    ir = lp(ir, bright)
    pd = n_of(predelay)
    ir[:pd] = 0.0
    for k in range(5):  # early reflections
        pos = pd + int(rng.uniform(0.002, 0.03) * SR)
        if pos < n:
            ir[pos] += rng.uniform(-1, 1) * 4.0
    ir[pd:pd + n_of(0.004)] *= np.linspace(0, 1, len(ir[pd:pd + n_of(0.004)]))
    ir /= np.sqrt(np.sum(ir ** 2))
    x = endfade(x, 0.003)
    w = signal.fftconvolve(x, ir)
    return mix(x * (1.0 - wet * 0.5), w * wet)


def grains(d, count, fmin, fmax, seed, glen=0.025, spread=1.0, skew=1.6, amp_tau=None, kind="sine", start=0.0):
    """A cloud of tiny pitched grains (sparkles, debris, tinkles)."""
    rng = np.random.default_rng(seed)
    out = np.zeros(n_of(d))
    for _ in range(count):
        t0 = start + (rng.random() ** skew) * spread * max(d - glen * 1.5 - start, 0.001)
        f = np.exp(rng.uniform(np.log(fmin), np.log(fmax)))
        gl = glen * rng.uniform(0.6, 1.4)
        if kind == "sine":
            g = sine(f, gl, ph0=rng.random()) * decay(gl, gl / 3.5, attack=0.0008)
        elif kind == "bell":
            g = (sine(f, gl) + 0.5 * sine(f * 2.32, gl) + 0.25 * sine(f * 4.13, gl)) * decay(gl, gl / 4, 0.0005)
        else:  # noise click
            g = bp(noise(gl, int(rng.integers(1 << 30))), f * 0.7, min(f * 1.4, 20000)) * decay(gl, gl / 4, 0.0003)
        a = rng.uniform(0.4, 1.0)
        if amp_tau:
            a *= np.exp(-(t0 - start) / amp_tau)
        i = n_of(t0)
        j = min(len(out), i + len(g))
        out[i:j] += a * g[: j - i]
    return out


def crackle(d, density, tau, seed, lo=1500.0, hi=9000.0):
    """Sparse impulses whose density decays (fire, sparks, debris)."""
    rng = np.random.default_rng(seed)
    n = n_of(d)
    t = np.arange(n) / SR
    dens = density / SR * np.exp(-t / tau)
    imp = (rng.random(n) < dens) * rng.uniform(-1, 1, n) * (0.4 + rng.random(n))
    k = np.exp(-np.arange(n_of(0.002)) / (0.0004 * SR))
    return bp(np.convolve(imp, k)[:n], lo, hi)


def bell(f, d, ratios=(1, 2.0, 3.0, 4.2, 5.4), amps=(1, 0.45, 0.28, 0.16, 0.1), decays=(0.4, 0.25, 0.15, 0.1, 0.06),
         attack=0.0008, seed=0):
    """Additive bell / chime: inharmonic partials with their own decays. f may be an array (pitch envelope).
    The result is at least as long as the slowest partial needs to fall to -40 dB (it may be longer than d)."""
    rng = np.random.default_rng(seed)
    base = F(f, d)
    need = n_of(4.6 * max(decays))  # the longest partial down to -40 dB
    if len(base) < need:
        base = fit(base, need)
    n = len(base)
    t = np.arange(n) / SR
    out = np.zeros(n)
    for r, a, dc in zip(ratios, amps, decays):
        out += a * np.sin(2 * np.pi * phase_of(base * r, rng.random())) * np.exp(-t / dc)
    a = np.clip(t / attack, 0, 1)
    return endfade(out * np.sin(a * np.pi / 2) ** 2)


def stutter(x, t0, seg, repeats, shrink=0.75):
    """Glitch: repeats the slice at t0 of length seg, each repeat shorter."""
    i = n_of(t0)
    out = [x[:i]]
    L = n_of(seg)
    for _ in range(repeats):
        s = x[i:i + L].copy()
        if len(s) < 8:
            break
        f = min(len(s) // 4, n_of(0.0015))
        s[:f] *= np.linspace(0, 1, f)
        s[-f:] *= np.linspace(1, 0, f)
        out.append(s)
        L = max(8, int(L * shrink))
    return np.concatenate(out)


# ---------------------------------------------------------------------------------------------------------------
# Levels
# ---------------------------------------------------------------------------------------------------------------

def _kweight(x):
    """ITU BS.1770 K-weighting (high shelf +4 dB at 1.5 kHz, high pass 38 Hz), RBJ biquads at 44.1 kHz."""
    G, Q, fc = 4.0, 0.7071, 1681.97
    A = 10 ** (G / 40)
    w0 = 2 * np.pi * fc / SR
    al = np.sin(w0) / (2 * Q)
    c = np.cos(w0)
    b = [A * ((A + 1) + (A - 1) * c + 2 * np.sqrt(A) * al), -2 * A * ((A - 1) + (A + 1) * c),
         A * ((A + 1) + (A - 1) * c - 2 * np.sqrt(A) * al)]
    a = [(A + 1) - (A - 1) * c + 2 * np.sqrt(A) * al, 2 * ((A - 1) - (A + 1) * c),
         (A + 1) - (A - 1) * c - 2 * np.sqrt(A) * al]
    y = signal.lfilter(b, a, x)
    Q, fc = 0.5003, 38.135
    w0 = 2 * np.pi * fc / SR
    al = np.sin(w0) / (2 * Q)
    c = np.cos(w0)
    b = [(1 + c) / 2, -(1 + c), (1 + c) / 2]
    a = [1 + al, -2 * c, 1 - al]
    return signal.lfilter(b, a, y)


def loudness(x, win=0.1):
    """Max momentary loudness (K-weighted, 100 ms windows, 10 ms hop) in LU (LUFS-like)."""
    y = _kweight(np.concatenate([x, np.zeros(n_of(win))])) ** 2
    w = n_of(win)
    c = np.concatenate([[0.0], np.cumsum(y)])
    hop = n_of(0.01)
    starts = np.arange(0, max(1, len(y) - w), hop)
    ms = (c[starts + w] - c[starts]) / w
    return -0.691 + 10 * np.log10(max(ms.max(), 1e-12))


def limit(x, ceiling, look=0.004, release=0.06):
    """Look-ahead peak limiter: gain <= the gain each sample needs, smooth attack, exponential release."""
    need = np.minimum(1.0, ceiling / np.maximum(np.abs(x), 1e-12))
    L = n_of(look)
    g = uniform_filter1d(minimum_filter1d(need, size=2 * L + 1), size=L + 1)
    g = np.minimum(g, need)
    coef = 1.0 - np.exp(-1.0 / (release * SR))
    gl = g.tolist()
    r = 1.0
    out = [0.0] * len(gl)
    for i, v in enumerate(gl):
        r = min(v, r + (1.0 - r) * coef)
        out[i] = r
    return x * np.array(out)


def finish_loop(x, target):
    """A seamless loop: only gain (to the target, peak under the ceiling), no filter, trim or fades."""
    x = np.asarray(x, dtype=np.float64)
    y = x * 10 ** ((target - loudness(np.tile(x, 3))) / 20)
    ceil = 10 ** (CEILING_DB / 20)
    p = np.max(np.abs(y))
    return y * (ceil / p) if p > ceil else y


def finish(x, target, fade_out=0.02, fade_in=0.0015, hp_hz=28.0, max_gr=6.0):
    """DC/rumble high pass, trim the silent tail, fades, loudness to target, limiter to the ceiling.
    fade_out None = a seamless loop (see finish_loop)."""
    if fade_out is None:
        return finish_loop(x, target)
    x = hp(np.asarray(x, dtype=np.float64), hp_hz)
    pk = np.max(np.abs(x))
    idx = np.nonzero(np.abs(x) > pk * 10 ** (-66 / 20))[0]
    end = min(len(x), int(idx[-1]) + n_of(0.012)) if len(idx) else len(x)
    x = x[:end].copy()
    fi = n_of(fade_in)
    x[:fi] *= np.sin(np.linspace(0, np.pi / 2, fi)) ** 2
    fo = min(len(x) // 3, n_of(fade_out))
    x[len(x) - fo:] *= np.cos(np.linspace(0, np.pi / 2, fo)) ** 2
    ceil = 10 ** (CEILING_DB / 20)
    gain_db = target - loudness(x)
    y = x
    for _ in range(4):
        pre = x * 10 ** (gain_db / 20)
        gr = 20 * np.log10(max(np.max(np.abs(pre)), 1e-12) / ceil)
        if gr > max_gr:  # would squash: accept a quieter result
            pre = pre * 10 ** (-(gr - max_gr) / 20)
        y = limit(pre, ceil)
        short = target - loudness(y)
        if short < 0.25 or gr > max_gr:
            break
        gain_db += short
    p = np.max(np.abs(y))
    if p > ceil:
        y *= ceil / p
    y[0] = 0.0
    y[-1] = 0.0
    return y


def write_wav(path, x):
    data = np.clip(np.round(x * 32767.0), -32767, 32767).astype("<i2")
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(data.tobytes())


def read_wav(path):
    with wave.open(str(path), "rb") as w:
        return np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").astype(np.float64) / 32767.0


# ---------------------------------------------------------------------------------------------------------------
# The sounds. Each returns (raw signal, loudness target in LU, fade-out seconds).
# ---------------------------------------------------------------------------------------------------------------

SOUNDS = {}


def sound(target, fade=0.02, loop=False):
    """Registers s_<name>: loudness target in LU, fade-out seconds; loop=True keeps it seamless (no trim/fades)."""
    def deco(fn):
        SOUNDS[fn.__name__[2:]] = (fn, target, None if loop else fade)
        return fn
    return deco


# --- hero movement -----------------------------------------------------------------------------------------------

@sound(-27)
def s_jump():
    d = 0.2
    t = tt(d)
    f = cat(expseg(250, 640, 0.075, 0.55), expseg(640, 760, d - 0.075))[: len(t)]
    f = f * (1 + 0.035 * np.sin(2 * np.pi * 24 * t) * np.exp(-t / 0.05))
    body = tri(f) * 0.8 + square(f * 2, pw=0.3) * 0.12 + sine(f * 0.5) * 0.25
    body = lp(body, 3800) * decay(d, 0.055, attack=0.002)
    air = bp(noise(d, 11), 2500, 7500) * decay(d, 0.014, attack=0.003) * 0.25
    return tail(body + air, rt=0.12, wet=0.08, seed=3)


@sound(-29)
def s_land():
    d = 0.16
    thud = sine(glide(150, 48, d, 0.022)) * decay(d, 0.032, attack=0.0015)
    dust = lp(noise(d, 21), 700) * decay(d, 0.018, attack=0.001) * 0.6
    tick = hp(noise(d, 22), 2500) * decay(d, 0.004, attack=0.0005) * 0.12
    return thud + dust + tick


def _step(seed, centre):
    d = 0.07
    click = bp(noise(d, seed), centre * 0.6, centre * 1.6) * decay(d, 0.007, attack=0.0006)
    thud = sine(glide(230, 110, d, 0.012)) * decay(d, 0.014, attack=0.001) * 0.7
    return click * 0.8 + thud


@sound(-33)
def s_step():
    return _step(31, 1800)


@sound(-33)
def s_step_2():
    return _step(32, 1550)


@sound(-33)
def s_step_3():
    return _step(33, 2100)


@sound(-21)
def s_spring():
    d = 0.5
    t = tt(d)
    f = expseg(170, 560, d, 0.45) * (1 + 0.22 * np.sin(2 * np.pi * 15 * t) * np.exp(-t / 0.13))
    body = sine(f) * 0.8 + tri(f * 2) * 0.25
    twang = fit(bell(f * 1.5, d, ratios=(1, 2.71, 4.6), amps=(0.3, 0.12, 0.05), decays=(0.14, 0.07, 0.04)), len(t))
    out = (body + twang) * decay(d, 0.16, attack=0.002)
    pop = lp(noise(d, 41), 1500) * decay(d, 0.01) * 0.4
    return tail(out + pop, rt=0.2, wet=0.12, seed=4)


# --- hero weapons ------------------------------------------------------------------------------------------------

def _shoot(k, seed, tau=0.034):
    d = 0.17
    f = glide(1450 * k, 240 * k, d, tau)
    zap = square(f, pw=0.5) * 0.6 + saw(f * 1.005) * 0.35
    zap = svf(zap, glide(7500, 900, d, 0.04), q=1.3) * decay(d, 0.048, attack=0.0008)
    punch = sine(glide(950 * k, 110, d, 0.016)) * decay(d, 0.03, attack=0.0008) * 0.9
    fmz = fm(glide(2600 * k, 700, d, 0.02), 1.5, glide(3.0, 0.2, d, 0.02)) * decay(d, 0.018) * 0.25
    snap = hp(noise(d, seed), 3000) * decay(d, 0.0035, attack=0.0003) * 0.35
    return tail(zap + punch + fmz + snap, rt=0.14, wet=0.1, seed=seed)


@sound(-25)
def s_shoot():
    return _shoot(1.0, 51)


@sound(-25)
def s_shoot_2():
    return _shoot(1.06, 52, tau=0.031)


@sound(-25)
def s_shoot_3():
    return _shoot(0.945, 53, tau=0.037)


@sound(-24, fade=0.04)
def s_charge():
    """Charging the blaster (0.8 s). Rises from A2 to A4; charge_loop holds the top, charge_full pings on top."""
    d = 0.8
    f = expseg(110, 440, d, 0.85)
    hum = sine(f) * 0.5 + sine(f * 2.0) * 0.3 + tri(f * 3.0) * 0.1 + sine(f * 0.5) * 0.3 + sine(f * 4.0) * 0.12
    trem = 1 + 0.25 * np.sin(2 * np.pi * phase_of(expseg(6, 22, d)))
    whine = sine(f * 8.0) * swell(d, 2.5) * 0.06
    sizzle = bp(noise(d, 501), 3000, 8000) * swell(d, 2.5) * 0.06
    env = np.minimum(1.0, 0.25 + 0.75 * swell(d, 0.7)) * decay(d, 99.0, attack=0.03)
    return (hum * trem + whine + sizzle) * env


@sound(-26, loop=True)
def s_charge_loop():
    """Seamless loop of the full charge (0.5 s, every partial an integer number of cycles, starts at zero)."""
    d = 0.5
    t = tt(d)
    w = 2 * np.pi * t
    hum = (np.sin(w * 220) * 0.3 + np.sin(w * 440) * 0.5 + np.sin(w * 880) * 0.3 + np.sin(w * 1320) * 0.1
           + np.sin(w * 1760) * 0.12)
    trem = 1 + 0.25 * np.sin(w * 22)
    shimmer = np.sin(w * 3520 + 0.8 * np.sin(w * 6)) * 0.05
    return hum * trem + shimmer


@sound(-20, fade=0.06)
def s_charge_full():
    blip = lp(square(mtof(81), 0.04, pw=0.25), 5000) * decay(0.04, 0.012)
    a = bell(mtof(93), 0.45, decays=(0.25, 0.15, 0.1, 0.06, 0.04), seed=5)
    b = bell(mtof(100), 0.4, decays=(0.22, 0.13, 0.08, 0.05, 0.03), seed=6)
    return tail(mix(blip * 0.6, at(a * 0.6, 0.02), at(b * 0.45, 0.07)), rt=0.3, wet=0.18, seed=50, bright=9000)


@sound(-17, fade=0.12)
def s_shoot_charged():
    d = 0.65
    f = glide(1100, 70, d, 0.06)
    stack = (saw(f) + saw(f * 1.01) + square(f * 0.5, pw=0.45)) / 3
    stack = svf(stack, glide(9000, 400, d, 0.08), q=1.4) * decay(d, 0.14, attack=0.001)
    punch = sine(glide(230, 38, d, 0.035)) * decay(d, 0.12, attack=0.001) * 1.2
    fmz = fm(glide(3000, 400, d, 0.03), 1.5, glide(5.0, 0.3, d, 0.04)) * decay(d, 0.04) * 0.4
    blast = svf(noise(d, 511), glide(9000, 300, d, 0.05), q=0.8) * decay(d, 0.06, attack=0.0008) * 0.7
    sub = sine(glide(80, 35, d, 0.2)) * decay(d, 0.25, attack=0.004) * 0.6
    return tail(drive(stack + punch + fmz + blast + sub, 1.6), rt=0.4, wet=0.16, seed=51, bright=5000)


def _repeater(k, seed):
    d = 0.085
    f = glide(1250 * k, 420 * k, d, 0.018)
    z = lp(tri(f) * 0.7 + square(f, pw=0.3) * 0.2, 3500) * decay(d, 0.022, attack=0.0008)
    punch = sine(glide(700 * k, 160, d, 0.01)) * decay(d, 0.016) * 0.6
    tick = bp(noise(d, seed), 1500, 4500) * decay(d, 0.002, 0.0003) * 0.15
    return tail(z + punch + tick, rt=0.08, wet=0.06, seed=seed)


@sound(-30)
def s_shoot_repeater():
    return _repeater(1.0, 521)


@sound(-30)
def s_shoot_repeater_2():
    return _repeater(1.045, 522)


@sound(-30)
def s_shoot_repeater_3():
    return _repeater(0.955, 523)


@sound(-22, fade=0.05)
def s_shoot_scatter():
    d = 0.32
    parts = []
    for i, r in enumerate((1.0, 1.19, 0.84, 1.41, 0.71)):
        f = glide(1600 * r, 300 * r, d, 0.025)
        z = square(f, pw=0.4) * 0.4 + saw(f * 1.003) * 0.25
        z = svf(z, glide(8000, 1000, d, 0.03), q=1.0) * decay(d, 0.035, attack=0.0008)
        parts.append(at(z, i * 0.006))
    blast = svf(noise(d, 531), glide(7000, 500, d, 0.03), q=0.8) * decay(d, 0.045, attack=0.0006) * 0.9
    punch = sine(glide(260, 50, d, 0.02)) * decay(d, 0.06, attack=0.001)
    cr = crackle(d, 1500, 0.06, 532, 2000, 9000) * 0.5
    return tail(drive(mix(*parts, blast, punch, cr), 1.4), rt=0.2, wet=0.12, seed=53)


@sound(-23, fade=0.05)
def s_shoot_ricochet():
    d = 0.32
    spin = 1 + 0.6 * np.sin(2 * np.pi * phase_of(expseg(55, 30, d)))
    whoosh = svf(noise(d, 541), expseg(1500, 4000, d, 0.5), q=3.0, mode="bp") * spin * adsr(d, 0.01, 0.1, 0.5, 0.15)
    ring = bell(expseg(1250, 1500, d, 0.5), d, ratios=(1, 2.32, 3.7), amps=(0.5, 0.25, 0.12),
                decays=(0.12, 0.07, 0.04))
    throw = sine(glide(500, 220, d, 0.02)) * decay(d, 0.03) * 0.5
    return tail(mix(whoosh * 0.6, ring, throw), rt=0.15, wet=0.1, seed=54)


@sound(-26)
def s_disc_bounce():
    d = 0.2
    ping = bell(glide(2100, 1850, d, 0.03), d, ratios=(1, 1.62, 2.93), amps=(0.6, 0.35, 0.15),
                decays=(0.07, 0.04, 0.025))
    tick = hp(noise(d, 551), 2500) * decay(d, 0.003, 0.0003) * 0.4
    thunk = sine(glide(600, 250, d, 0.008)) * decay(d, 0.012) * 0.4
    return tail(mix(ping, tick, thunk), rt=0.12, wet=0.1, seed=55)


@sound(-23, fade=0.06)
def s_shoot_cryo():
    d = 0.45
    hiss = hp(noise(d, 561), 3500) * adsr(d, 0.01, 0.1, 0.5, 0.2) * 0.5
    sweep = svf(noise(d, 562), expseg(9000, 3000, d), q=2.0, mode="bp") * adsr(d, 0.005, 0.08, 0.3, 0.2) * 0.4
    cold = fm(glide(2400, 1500, d, 0.1), 2.76, glide(2.5, 0.5, d, 0.1)) * adsr(d, 0.005, 0.1, 0.3, 0.2) * 0.3
    tinkle = grains(d, 18, 3500, 9500, 563, glen=0.03, kind="bell", skew=1.0, amp_tau=0.3) * 0.3
    punch = sine(glide(800, 200, d, 0.012)) * decay(d, 0.02) * 0.4
    return tail(hiss + sweep + cold + tinkle + punch, rt=0.3, wet=0.18, seed=56, bright=10000)


@sound(-20, fade=0.1)
def s_freeze():
    d = 0.8
    crackles = grains(0.62, 44, 1500, 7000, 571, glen=0.012, kind="noise", skew=0.7) * 0.7
    creak = svf(noise(0.62, 572), expseg(700, 3200, 0.62), q=8.0, mode="bp") * swell(0.62, 1.5) * 0.35
    frost = hp(noise(0.62, 573), 6000) * swell(0.62, 2.0) * 0.12
    chime = bell(mtof(96), 0.3, ratios=(1, 2.76, 5.4), amps=(0.5, 0.3, 0.15), decays=(0.15, 0.08, 0.04))
    tsch = hp(noise(0.2, 574), 4000) * decay(0.2, 0.03, attack=0.001) * 0.4
    return tail(mix(crackles + creak + frost, at(mix(chime, tsch), 0.58)), rt=0.4,
                wet=0.2, seed=57, bright=10000)


@sound(-17, fade=0.1)
def s_shatter():
    d = 0.8
    crack = hp(noise(d, 581), 1500) * decay(d, 0.015, attack=0.0004) * 1.3
    thud = sine(glide(200, 70, d, 0.02)) * decay(d, 0.06) * 0.7
    tinkles = grains(d, 60, 3000, 11000, 582, glen=0.07, kind="bell", skew=2.0, amp_tau=0.3) * 0.6
    glass = hp(noise(d, 583), 5000) * decay(d, 0.15, attack=0.001) * 0.3
    shards = grains(d, 20, 1500, 5000, 584, glen=0.02, kind="noise", skew=1.5, amp_tau=0.2) * 0.4
    return tail(crack + thud + tinkles + glass + shards, rt=0.5, wet=0.2, seed=58, bright=11000)


@sound(-21, fade=0.06)
def s_shoot_lancer():
    d = 0.45
    f = glide(3000, 1300, d, 0.025)
    beam = fm(f, 0.5, glide(4.5, 1.5, d, 0.05)) * 0.45
    body = (saw(f / 2) + saw(f / 2 * 1.007) + saw(f / 2 * 0.994)) / 3
    body = svf(body, glide(10000, 2500, d, 0.08), q=0.9) * 0.45
    sizzle = hp(noise(d, 591), 4000) * (0.5 + 0.5 * square(85, d, pw=0.5)) * 0.25
    env = adsr(d, 0.002, 0.05, 0.5, 0.2)
    cr = crackle(d, 1200, 0.2, 592, 3000, 12000) * 0.5
    punch = sine(glide(1500, 200, d, 0.012)) * decay(d, 0.02) * 0.7
    out = drive((beam + body + sizzle + cr) * env + punch, 1.3)
    return tail(crush(out, bits=9, hold_n=2, mix=0.15), rt=0.25, wet=0.14, seed=59)


@sound(-21, fade=0.06)
def s_shoot_mortar():
    d = 0.5
    thunk = sine(glide(170, 60, d, 0.03)) * decay(d, 0.08, attack=0.001) * 1.2
    tube = svf(noise(d, 601), 320, q=6.0, mode="bp") * decay(d, 0.06, attack=0.001) * 1.4
    pop = lp(noise(d, 602), 2000) * decay(d, 0.012) * 0.6
    whistle = at(sine(expseg(700, 1100, 0.35)) * adsr(0.35, 0.05, 1, 1, 0.15) * 0.1, 0.05)
    plasma = fm(glide(400, 200, d, 0.1), 1.5, 1.5) * decay(d, 0.1, attack=0.002) * 0.2
    return tail(mix(drive(thunk + tube + pop, 1.3), whistle, plasma), rt=0.25, wet=0.12, seed=60)


@sound(-22, fade=0.05)
def s_shoot_arc():
    d = 0.38
    t = tt(d)
    rng = np.random.default_rng(611)
    seg = np.repeat(rng.random(int(d * 90) + 2) < 0.6, n_of(1 / 90))[: len(t)].astype(float)
    gate = lp(fit(seg, len(t)), 400)
    jit = 1 + 0.08 * lp(rng.standard_normal(len(t)), 30) * 8
    buzz = lp(square(120 * jit, pw=0.3) * 0.5 + saw(240 * jit) * 0.4, 5000) * gate
    zaps = crackle(d, 2500, 0.25, 612, 2000, 12000)
    hiss = hp(noise(d, 613), 5000) * gate * 0.3
    snap = sine(glide(2500, 600, d, 0.008)) * decay(d, 0.015) * 0.4
    return tail((buzz * 0.6 + zaps + hiss) * adsr(d, 0.003, 0.1, 0.6, 0.15) + snap, rt=0.18, wet=0.12, seed=61)


@sound(-22, fade=0.06)
def s_shoot_seeker():
    parts = []
    for i in range(3):
        dd = 0.2
        pop = sine(glide(420 + 50 * i, 130, dd, 0.012)) * decay(dd, 0.025) * 0.7
        pop += bp(noise(dd, 625 + i), 800, 5000) * decay(dd, 0.006) * 0.5
        wh = svf(noise(dd, 621 + i), expseg(900, 4200 + 400 * i, dd, 0.5), q=2.5, mode="bp")
        wh = wh * decay(dd, 0.05, attack=0.008) * 0.8
        zp = sine(expseg(950 + 90 * i, 1700, dd)) * decay(dd, 0.04, attack=0.003) * 0.15
        parts.append(at(pop + wh + zp, i * 0.105))
    return tail(mix(*parts), rt=0.2, wet=0.12, seed=62)


@sound(-23, fade=0.04)
def s_weapon_switch():
    c1 = bp(noise(0.03, 631), 1500, 6000) * decay(0.03, 0.003)
    c2 = bp(noise(0.03, 632), 1000, 4500) * decay(0.03, 0.004) * 0.7
    wd = 0.16
    whine = svf(saw(expseg(500, 1300, wd, 0.6)), 2500, q=2.0) * adsr(wd, 0.01, 0.1, 0.6, 0.05) * 0.25
    lock = bell(2400, 0.1, ratios=(1, 1.8), amps=(0.4, 0.2), decays=(0.02, 0.012))
    return tail(mix(c1, at(whine, 0.02), at(c2, 0.045), at(lock, 0.17)), rt=0.12, wet=0.1, seed=63)


@sound(-21, fade=0.05)
def s_ammo():
    cl1 = bp(noise(0.04, 641), 800, 4000) * decay(0.04, 0.005)
    cl2 = bp(noise(0.04, 642), 1200, 5000) * decay(0.04, 0.004) * 0.8

    def note(m, d, tau):
        return lp(square(mtof(m), d, pw=0.35) * 0.4 + tri(mtof(m), d) * 0.6, 5000) * decay(d, tau, attack=0.002)
    return tail(mix(cl1, at(cl2, 0.05), at(note(84, 0.06, 0.03), 0.07), at(note(91, 0.22, 0.07), 0.12)),
                rt=0.2, wet=0.12, seed=64)


@sound(-28)
def s_no_ammo():
    d = 0.14
    k1 = mix(hp(noise(d, 651), 2000) * decay(d, 0.002, 0.0003),
             bell(1800, d, ratios=(1, 2.3), amps=(0.3, 0.1), decays=(0.01, 0.006)))
    k2 = hp(noise(d, 652), 2500) * decay(d, 0.002, 0.0003) * 0.5
    pft = lp(noise(d, 653), 1000) * decay(d, 0.02, attack=0.002) * 0.2
    return mix(k1, at(k2, 0.035), at(pft, 0.035))


@sound(-18, fade=0.15)
def s_buy():
    click = bp(noise(0.05, 661), 1500, 7000) * decay(0.05, 0.004)
    parts = [click]
    for i, m in enumerate((83, 88, 92)):  # B5 E6 G#6: "ka-ching"
        parts.append(at(bell(mtof(m), 0.7, decays=(0.24, 0.15, 0.1, 0.06, 0.04), seed=70 + i) * 0.45, 0.03 + i * 0.03))
    parts.append(at(grains(0.5, 14, 4500, 10000, 662, glen=0.016, amp_tau=0.2) * 0.25, 0.05))
    parts.append(at(lp(tri(mtof(64), 0.3) + square(mtof(64), 0.3, pw=0.4) * 0.2, 2500) * decay(0.3, 0.1) * 0.4, 0.03))
    return tail(mix(*parts), rt=0.45, wet=0.2, seed=65, bright=9000)


@sound(-28)
def s_hit_wall():
    d = 0.14
    ping = bell(2650, d, ratios=(1, 1.73, 2.41), amps=(0.6, 0.35, 0.2), decays=(0.035, 0.022, 0.014))
    spark = bp(noise(d, 91), 2500, 9000) * decay(d, 0.008, attack=0.0004) * 0.7
    thud = sine(glide(520, 190, d, 0.01)) * decay(d, 0.012) * 0.5
    return tail(mix(ping, spark, thud), rt=0.1, wet=0.1, seed=9)


@sound(-24)
def s_hit_enemy():
    d = 0.16
    thwack = sine(glide(640, 140, d, 0.018)) * decay(d, 0.05, attack=0.0008)
    smack = bp(noise(d, 101), 600, 3500) * decay(d, 0.018, attack=0.0005) * 0.8
    fz = fm(glide(900, 300, d, 0.02), 1.41, 2.5) * decay(d, 0.025) * 0.3
    return crush(thwack + smack + fz, bits=7, hold_n=3, mix=0.3)


@sound(-24)
def s_armour_ping():
    d = 0.45
    t = tt(d)
    f = 1900 * (1 - 0.06 * (1 - np.exp(-t / 0.08)))
    ping = bell(f, d, ratios=(1, 2.76, 5.4, 8.93), amps=(1, 0.5, 0.25, 0.12), decays=(0.14, 0.08, 0.05, 0.03))
    ric = sine(expseg(3600, 1700, 0.16, 0.6)) * decay(0.16, 0.05, attack=0.004) * 0.18
    tick = hp(noise(d, 111), 3000) * decay(d, 0.003) * 0.4
    return tail(mix(ping, at(ric, 0.01), tick), rt=0.3, wet=0.15, seed=11)


# --- hero state ----------------------------------------------------------------------------------------------------

@sound(-19)
def s_hurt():
    d = 0.36
    t = tt(d)
    f = glide(720, 210, d, 0.09) * (1 + 0.07 * np.sin(2 * np.pi * 32 * t))
    v = square(f, pw=0.32) * 0.5 + saw(f * 0.5) * 0.4
    v = svf(v, glide(5000, 900, d, 0.12), q=1.5) * decay(d, 0.11, attack=0.001)
    crunch = bp(noise(d, 121), 400, 4000) * decay(d, 0.02) * 0.6
    return tail(crush(v + crunch, bits=6, hold_n=2, mix=0.35), rt=0.2, wet=0.1, seed=12)


@sound(-17, fade=0.08)
def s_die():
    parts = []
    notes = (79, 75, 72, 67)  # G5 Eb5 C5 G4: a friendly "oh no"
    for i, m in enumerate(notes):
        d = 0.14
        f = mtof(m) * (1 - 0.05 * (1 - np.exp(-tt(d) / 0.05)))
        v = (square(f, pw=0.4) * 0.45 + tri(f) * 0.6) * decay(d, 0.07, attack=0.002)
        parts.append(at(lp(v, 4500), i * 0.12))
    d = 0.9
    t = tt(d)
    f = expseg(mtof(67), mtof(36), d, 1.4) * (1 + 0.04 * np.sin(2 * np.pi * 7 * t))
    v = svf(square(f, pw=0.45) * 0.5 + saw(f) * 0.3, expseg(4000, 300, d), q=1.8) * adsr(d, 0.01, 0.3, 0.6, 0.35)
    parts.append(at(crush(v, bits=6, hold_n=3, mix=0.4), 0.48))
    return tail(mix(*parts), rt=0.5, wet=0.18, seed=13)


# --- pickups -------------------------------------------------------------------------------------------------------

@sound(-21, fade=0.06)
def s_crystal():
    d = 0.75
    a = bell(mtof(88), d, decays=(0.2, 0.13, 0.09, 0.06, 0.04), seed=1)             # E6
    b = bell(mtof(95), d - 0.05, decays=(0.24, 0.15, 0.1, 0.06, 0.04), seed=2)      # B6
    shim = fm(mtof(100), 3.01, 1.2, d) * decay(d, 0.1, attack=0.004) * 0.12         # E7 glint
    spark = grains(d, 14, 4200, 9500, 141, glen=0.018, spread=0.55, amp_tau=0.15) * 0.25
    return tail(mix(a * 0.7, at(b * 0.75, 0.055), shim, spark), rt=0.6, wet=0.25, seed=14, bright=9000)


@sound(-15, fade=0.25)
def s_crystal_last():
    d = 2.2
    parts = []
    arp = (76, 80, 83, 88, 92, 95, 100)  # E major, up to E7
    for i, m in enumerate(arp):
        parts.append(at(bell(mtof(m), 1.2, seed=i) * 0.55, i * 0.06))
    pad_d = 1.7
    chord = (64, 68, 71, 76)
    pad = sum(saw(mtof(m) * (1 + dt), pad_d) for m in chord for dt in (-0.004, 0.0, 0.0045))
    pad = lp(pad / 12.0, 2600) * adsr(pad_d, 0.09, 0.4, 0.6, 0.8)
    parts.append(at(pad * 0.9, 0.32))
    rise = svf(noise(0.45, 151), expseg(800, 9000, 0.45), q=2.5, mode="bp") * swell(0.45, 1.5) * 0.25
    parts.append(rise)
    parts.append(at(grains(1.4, 40, 3500, 11000, 152, glen=0.02, spread=0.9, amp_tau=0.6) * 0.3, 0.35))
    parts.append(at(bell(mtof(64) / 2, 1.5, ratios=(1, 2, 3), amps=(0.6, 0.3, 0.1), decays=(0.4, 0.25, 0.15)), 0.36))
    return tail(mix(*parts), rt=1.1, wet=0.28, seed=15, bright=9000)


@sound(-20, fade=0.05)
def s_treasure():
    d1, d2 = 0.075, 0.5
    def coin(m, d, tau):
        f = mtof(m)
        v = square(f, d, pw=0.5) * 0.3 + fm(f, 3.5, glide(1.8, 0.3, d, 0.05)) * 0.6
        v = lp(v, 7000) * decay(d, tau, attack=0.001)
        return v * (1 + 0.25 * np.sin(2 * np.pi * 31 * tt(d)))
    a = coin(83, d1, 0.06)                                           # B5
    b = coin(88, d2, 0.16)                                           # E6
    spark = grains(0.4, 8, 5000, 10000, 161, glen=0.015, spread=0.6, amp_tau=0.15) * 0.2
    return tail(mix(a, at(b, 0.07), at(spark, 0.07)), rt=0.35, wet=0.18, seed=16)


@sound(-21, fade=0.06)
def s_health():
    parts = []
    for i, m in enumerate((72, 76, 79)):
        d = 0.12 if i < 2 else 0.5
        t = tt(d)
        f = mtof(m) * (1 + 0.006 * np.sin(2 * np.pi * 6 * t) * (i == 2))
        v = tri(f) * 0.6 + sine(f * 2) * 0.25 + sine(f * 1.003) * 0.4
        parts.append(at(lp(v, 4000) * decay(d, 0.06 if i < 2 else 0.2, attack=0.004), i * 0.07))
    bub = grains(0.35, 6, 500, 1400, 171, glen=0.03, spread=0.7) * 0.15
    return tail(mix(*parts, bub), rt=0.4, wet=0.2, seed=17)


@sound(-19, fade=0.05)
def s_key():
    def blip(m, d, pw=0.25):
        f = mtof(m)
        return lp(square(f, d, pw=pw), 6000) * decay(d, d / 4.0, attack=0.001)
    a = blip(96, 0.045)
    b = blip(100, 0.045)
    c1 = mix(blip(91, 0.36, 0.5) * 0.5, blip(96, 0.36, 0.5) * 0.45,
             bell(mtof(103), 0.36, decays=(0.15, 0.08, 0.05, 0.03, 0.02)) * 0.3)
    data = crush(mix(a, at(b, 0.055), at(c1, 0.11)), bits=6, hold_n=2, mix=0.3)
    return tail(data, rt=0.3, wet=0.15, seed=18)


@sound(-17, fade=0.1)
def s_power():
    d = 0.95
    t = tt(d)
    base = expseg(mtof(57), mtof(81), d, 0.8)
    steps = np.array([0, 4, 7, 12])[(t / 0.04).astype(int) % 4]
    f = base * 2 ** (steps / 12)
    v = square(f, pw=0.35) * 0.4 + saw(f * 1.004) * 0.3
    v = svf(v, expseg(900, 8000, d, 0.7), q=1.6) * adsr(d, 0.01, 0.4, 0.8, 0.3)
    shine = fm(expseg(mtof(81), mtof(93), d), 2.0, 1.5) * swell(d, 2.0) * 0.18
    chime = at(bell(mtof(93), 0.5, decays=(0.22, 0.15, 0.1, 0.07, 0.04)) * 0.5, 0.5)
    return tail(mix(v, shine, chime), rt=0.45, wet=0.2, seed=19)


@sound(-14, fade=0.2)
def s_extra():
    parts = []
    arp = (72, 76, 79, 84, 88, 91)
    for i, m in enumerate(arp):
        d = 0.11
        v = square(mtof(m), d, pw=0.4) * 0.35 + tri(mtof(m), d) * 0.6
        parts.append(at(lp(v, 6000) * decay(d, 0.08, attack=0.002), i * 0.075))
    d = 0.75
    t = tt(d)
    chord = sum((square(mtof(m) * (1 + 0.004 * np.sin(2 * np.pi * 5.5 * t)), pw=0.45) * 0.25 + tri(mtof(m), d) * 0.4)
                for m in (84, 88, 91, 96))
    parts.append(at(lp(chord, 5000) * adsr(d, 0.005, 0.25, 0.55, 0.35) * 0.6, 0.47))
    parts.append(at(grains(0.8, 18, 4000, 10000, 181, glen=0.02, amp_tau=0.35) * 0.25, 0.47))
    return tail(mix(*parts), rt=0.6, wet=0.2, seed=20)


@sound(-29)
def s_score_tick():
    d = 0.045
    v = lp(square(mtof(96), d, pw=0.25), 6500) * decay(d, 0.012, attack=0.0008) * 0.6 + sine(mtof(108), d) * decay(
        d, 0.006) * 0.2
    return v


# --- world ---------------------------------------------------------------------------------------------------------

@sound(-21, fade=0.06)
def s_door():
    d = 0.8
    t = tt(d)
    hiss = bp(noise(d, 201), 900, 6500) * adsr(d, 0.03, 0.15, 0.55, 0.3) * 0.5
    hiss *= 1 + 0.15 * np.sin(2 * np.pi * 11 * t)
    motor_f = expseg(80, 112, 0.55)
    motor = lp(saw(motor_f) + 0.5 * saw(motor_f * 2.01), 650) * adsr(0.55, 0.05, 0.2, 0.8, 0.12) * 0.55
    clunk_d = 0.25
    clunk = sine(glide(140, 55, clunk_d, 0.03)) * decay(clunk_d, 0.06) + lp(noise(clunk_d, 202), 900) * decay(
        clunk_d, 0.02) * 0.6
    clunk = mix(clunk, bell(380, clunk_d, ratios=(1, 2.6, 4.1), amps=(0.25, 0.12, 0.06), decays=(0.08, 0.05, 0.03)))
    return tail(mix(hiss, motor, at(clunk, 0.52)), rt=0.3, wet=0.15, seed=21)


@sound(-21)
def s_switch():
    d = 0.3
    c1 = bp(noise(0.03, 211), 1800, 7000) * decay(0.03, 0.003)
    c2 = bp(noise(0.03, 212), 1200, 5000) * decay(0.03, 0.004) * 0.8
    tick = bell(3100, 0.08, ratios=(1, 1.9, 2.8), amps=(0.3, 0.15, 0.08), decays=(0.025, 0.015, 0.01))
    blip = sine(expseg(1100, 1760, 0.06, 0.5)) * decay(0.12, 0.05, attack=0.002)[: n_of(0.06)] * 0.0
    b = tri(cat(hold(1175, 0.05), hold(1760, 0.08))) * cat(decay(0.05, 0.03, 0.002), decay(0.08, 0.04, 0.002)) * 0.4
    return tail(mix(c1, at(c2, 0.032), tick, blip, at(b, 0.06)), rt=0.15, wet=0.12, seed=22)


@sound(-20, fade=0.08)
def s_teleport():
    d = 0.85
    t = tt(d)
    parts = []
    for i, (f0, f1) in enumerate(((350, 2100), (520, 3100), (700, 4200), (260, 1400))):
        f = expseg(f0, f1, d, 0.8 + 0.15 * i)
        parts.append(sine(f, ph0=i * 0.3) * (0.5 - 0.08 * i))
    v = sum(parts) * (0.6 + 0.4 * np.sin(2 * np.pi * expseg(12, 32, d) * t)) * adsr(d, 0.05, 0.3, 0.8, 0.35)
    sw = svf(noise(d, 221), expseg(500, 9000, d, 0.9), q=3.0, mode="bp") * adsr(d, 0.1, 0.3, 0.7, 0.3) * 0.5
    pop = at(sine(glide(1800, 600, 0.12, 0.02)) * decay(0.12, 0.03) * 0.4, d - 0.1)
    spark = grains(d, 16, 3000, 9000, 222, glen=0.02, skew=0.8, amp_tau=None) * 0.15
    return tail(mix(v, sw, pop, spark), rt=0.5, wet=0.25, seed=23)


@sound(-18, fade=0.15)
def s_checkpoint():
    hum_d = 0.4
    hum = svf(saw(expseg(110, 220, hum_d)) + saw(expseg(110, 220, hum_d) * 1.5), expseg(300, 2500, hum_d), q=1.5)
    hum = hum * swell(hum_d, 1.2) * 0.35
    a = bell(mtof(79), 0.9, decays=(0.32, 0.2, 0.13, 0.09, 0.05), seed=3)       # G5
    b = bell(mtof(86), 0.9, decays=(0.36, 0.22, 0.14, 0.09, 0.05), seed=4)      # D6
    pad_d = 0.9
    pad = lp(sum(saw(mtof(m) * (1 + dt), pad_d) for m in (67, 74, 79) for dt in (-0.003, 0.003)) / 6, 2200)
    pad = pad * adsr(pad_d, 0.06, 0.3, 0.5, 0.45) * 0.5
    return tail(mix(hum, at(a * 0.6, 0.36), at(b * 0.6, 0.47), at(pad, 0.4)), rt=0.7, wet=0.25, seed=24)


@sound(-15, fade=0.25)
def s_exit_open():
    d = 1.7
    t = tt(d)
    drone = sum(saw(f * (1 + dt), d) for f in (55, 110) for dt in (-0.003, 0.004)) / 4
    drone = svf(drone, expseg(150, 3000, d, 0.6), q=2.0) * adsr(d, 0.4, 0.5, 0.8, 0.5) * 0.7
    parts = [drone]
    for i, m in enumerate((64, 71, 76, 80, 83, 88)):
        parts.append(at(bell(mtof(m), 1.0, seed=10 + i) * 0.4, 0.25 + i * 0.08))
    shimmer = fm(mtof(88), 2.0, 1.0 + np.sin(2 * np.pi * 3 * t), d) * swell(d, 1.5) * adsr(d, 0.01, 1, 1, 0.5) * 0.12
    parts.append(shimmer)
    parts.append(grains(d, 30, 3000, 10000, 231, glen=0.02, skew=1.0, start=0.3) * 0.2)
    return tail(mix(*parts), rt=0.9, wet=0.25, seed=25)


@sound(-16, fade=0.15)
def s_exit_enter():
    d = 1.05
    t = tt(d)
    sweep = svf(noise(d, 241), expseg(250, 9000, d, 1.6), q=3.5, mode="bp") * adsr(d, 0.2, 1, 1, 0.25) * 0.7
    f = expseg(180, 2400, d, 2.0)
    tone = (sine(f) * 0.6 + sine(f * 1.5) * 0.25) * (0.7 + 0.3 * np.sin(2 * np.pi * expseg(8, 40, d) * t))
    tone *= adsr(d, 0.15, 1, 1, 0.2) * 0.5
    zap = at(bell(mtof(96), 0.4, decays=(0.2, 0.12, 0.08, 0.05, 0.03)) * 0.4, d - 0.18)
    return tail(mix(sweep, tone, zap), rt=0.6, wet=0.25, seed=26)


@sound(-19)
def s_break():
    d = 0.55
    thump = sine(glide(120, 45, d, 0.04)) * decay(d, 0.08, attack=0.001)
    burst = lp(noise(d, 251), 3500) * decay(d, 0.06, attack=0.0008) * 0.8
    debris = grains(d, 22, 700, 4500, 252, glen=0.018, kind="noise", skew=1.3, amp_tau=0.2) * 0.6
    crunch = crush(bp(noise(d, 253), 300, 2500) * decay(d, 0.04), bits=5, hold_n=4, mix=0.6) * 0.5
    return tail(drive(thump + burst + debris + crunch, 1.4), rt=0.2, wet=0.12, seed=27)


@sound(-23, fade=0.08)
def s_crumble():
    d = 0.65
    rng = np.random.default_rng(261)
    t = tt(d)
    rough = np.abs(lp(rng.standard_normal(len(t)), 40)) * 8
    grit = lp(noise(d, 262), 1100) * rough * adsr(d, 0.03, 0.3, 0.6, 0.25)
    clicks = grains(d, 18, 500, 2500, 263, glen=0.015, kind="noise", skew=1.0, amp_tau=0.4) * 0.6
    rumble = lp(noise(d, 264), 120) * adsr(d, 0.04, 0.3, 0.5, 0.3) * 1.5
    return grit * 0.6 + clicks + rumble


@sound(-17, fade=0.2)
def s_secret():
    parts = []
    notes = (67, 71, 74, 78, 81, 86)  # G B D F# A D: a Gmaj9 shimmer
    for i, m in enumerate(notes):
        b = bell(mtof(m), 0.9, decays=(0.4, 0.25, 0.15, 0.1, 0.06), seed=30 + i)
        b = mix(b, fm(mtof(m), 2.0, glide(1.4, 0.2, 0.9, 0.2), 0.9) * decay(0.9, 0.2) * 0.25)
        parts.append(at(b * 0.45, i * 0.075))
    parts.append(at(grains(0.9, 22, 3500, 10000, 271, glen=0.02, amp_tau=0.4) * 0.22, 0.3))
    return tail(mix(*parts), rt=0.9, wet=0.3, seed=28, bright=9000)


@sound(-21, fade=0.05)
def s_laser_fence():
    d = 0.6
    t = tt(d)
    f = expseg(90, 125, 0.12)
    f = fit(f, len(t))
    hum = saw(f) * 0.5 + square(f * 2, pw=0.3) * 0.25 + saw(f * 3.01) * 0.2
    hum = lp(hum, 2600) * (0.8 + 0.2 * square(60, d, pw=0.5))
    gate = (np.random.default_rng(281).random(len(t)) < 0.0015).astype(float)
    gate = np.convolve(gate, np.ones(n_of(0.004)))[: len(t)]
    zz = hp(noise(d, 282), 2500) * np.clip(gate, 0, 1) * 0.35
    zap = svf(noise(0.08, 283), expseg(9000, 1500, 0.08), q=2, mode="bp") * decay(0.08, 0.02) * 0.8
    return mix(hum * adsr(d, 0.01, 0.2, 0.7, 0.2), zz * adsr(d, 0.01, 1, 1, 0.2), zap)


@sound(-16, fade=0.06)
def s_crusher():
    d = 0.75
    thump = sine(glide(95, 34, d, 0.05)) * decay(d, 0.14, attack=0.001)
    clank = bell(178, d, ratios=(1, 2.64, 4.83, 7.53), amps=(0.5, 0.4, 0.25, 0.15), decays=(0.2, 0.14, 0.09, 0.05))
    burst = lp(noise(d, 291), 2500) * decay(d, 0.035) * 0.8
    hiss = hp(noise(0.4, 292), 2500) * adsr(0.4, 0.06, 0.2, 0.6, 0.2) * 0.18
    return tail(mix(drive(mix(thump * 1.2, clank, burst), 1.6), at(hiss, 0.3)), rt=0.4, wet=0.15, seed=29)


@sound(-20, fade=0.08)
def s_splash():
    d = 0.7
    t = tt(d)
    n1 = noise(d, 301)
    body = svf(n1, expseg(2600, 700, d, 0.6), q=2.0, mode="bp") * decay(d, 0.09, attack=0.004)
    top = hp(noise(d, 302), 3500) * decay(d, 0.05, attack=0.002) * 0.4
    drops = grains(d, 10, 900, 3000, 303, glen=0.03, kind="noise", start=0.12, amp_tau=0.25) * 0.5
    bubbles = np.zeros(len(t))
    rng = np.random.default_rng(304)
    for _ in range(7):
        bd = rng.uniform(0.025, 0.05)
        f0 = rng.uniform(350, 900)
        b = sine(f0 * (1 + 2.5 * tt(bd) / bd)) * decay(bd, bd / 3, attack=0.002)
        i = n_of(rng.uniform(0.1, 0.5))
        bubbles[i:i + len(b)] += b[: len(bubbles) - i] * 0.25
    return tail(body + top + drops + bubbles, rt=0.25, wet=0.12, seed=30)


@sound(-21, fade=0.04)
def s_acid():
    d = 0.42
    spit = svf(noise(d, 311), expseg(3200, 700, d, 0.5), q=4.0, mode="bp") * decay(d, 0.07, attack=0.003)
    rng = np.random.default_rng(312)
    bl = []
    for i in range(5):
        bd = 0.03
        b = sine(rng.uniform(380, 700) * (1 + 2.8 * tt(bd) / bd)) * decay(bd, 0.01, attack=0.002) * 0.4
        bl.append(at(b, 0.04 + i * 0.05 + rng.uniform(0, 0.02)))
    return tail(mix(spit, *bl), rt=0.2, wet=0.1, seed=31)


# --- enemies -------------------------------------------------------------------------------------------------------

@sound(-23)
def s_enemy_shoot():
    d = 0.2
    f = glide(900, 170, d, 0.05)
    v = saw(f) * 0.5 + square(f * 0.5, pw=0.5) * 0.4
    v = svf(v, glide(4000, 600, d, 0.05), q=2.2) * decay(d, 0.06, attack=0.001)
    snap = hp(noise(d, 321), 2000) * decay(d, 0.004) * 0.3
    return tail(crush(v + snap, bits=6, hold_n=3, mix=0.25), rt=0.15, wet=0.1, seed=32)


@sound(-22, fade=0.05)
def s_enemy_orb():
    d = 0.42
    t = tt(d)
    f = glide(330, 170, d, 0.12) * (1 + 0.15 * np.sin(2 * np.pi * 17 * t))
    v = fm(f, 1.0, 1.5 + 1.2 * np.sin(2 * np.pi * 9 * t)) * adsr(d, 0.01, 0.15, 0.6, 0.2)
    whoom = lp(noise(d, 331), glide(2000, 300, d, 0.1)[0]) * decay(d, 0.08) * 0.0
    w2 = svf(noise(d, 332), glide(2500, 400, d, 0.12), q=1.5) * decay(d, 0.1, attack=0.004) * 0.5
    return tail(v + whoom + w2, rt=0.25, wet=0.12, seed=33)


@sound(-19, fade=0.12)
def s_missile():
    d = 0.95
    t = tt(d)
    pop = sine(glide(240, 70, 0.15, 0.025)) * decay(0.15, 0.04) + lp(noise(0.15, 341), 2000) * decay(0.15, 0.02)
    flutter = 1 + 0.35 * lp(np.random.default_rng(342).standard_normal(len(t)), 35) * 6
    roar = svf(noise(d, 343), expseg(700, 2400, d, 0.6), q=0.9) * flutter * adsr(d, 0.04, 0.3, 0.8, 0.4) * 0.7
    whistle = sine(expseg(650, 1150, d, 0.7)) * adsr(d, 0.15, 1, 1, 0.4) * 0.12
    return tail(mix(pop, roar, whistle), rt=0.3, wet=0.15, seed=34)


@sound(-21, fade=0.05)
def s_grenade():
    d = 0.38
    whoosh = svf(noise(0.18, 351), expseg(600, 2500, 0.18), q=2.0, mode="bp") * adsr(0.18, 0.04, 1, 1, 0.12) * 0.4
    tonk = bell(690, 0.3, ratios=(1, 2.32, 3.87, 5.6), amps=(0.7, 0.35, 0.2, 0.1), decays=(0.12, 0.07, 0.04, 0.025))
    knock = sine(glide(300, 120, 0.1, 0.01)) * decay(0.1, 0.02) * 0.5
    return tail(mix(whoosh, at(mix(tonk, knock), 0.08)), rt=0.2, wet=0.12, seed=35)


@sound(-19, fade=0.06)
def s_beam_in():
    d = 0.62
    t = tt(d)
    parts = []
    for i, (f0, f1) in enumerate(((3200, 700), (2400, 520), (4100, 900))):
        parts.append(sine(expseg(f0, f1, 0.42, 0.7)) * (0.45 - 0.1 * i))
    v = sum(parts) * (0.6 + 0.4 * np.sin(2 * np.pi * 34 * tt(0.42))) * adsr(0.42, 0.03, 1, 1, 0.12)
    sw = svf(noise(0.42, 361), expseg(9000, 900, 0.42), q=2.5, mode="bp") * adsr(0.42, 0.03, 1, 1, 0.1) * 0.4
    chunk = sine(glide(330, 140, 0.2, 0.03)) * decay(0.2, 0.05) * 0.7 + lp(noise(0.2, 362), 1500) * decay(
        0.2, 0.015) * 0.4
    return tail(mix(v, sw, at(chunk, 0.38)), rt=0.3, wet=0.18, seed=36)


def _explosion(size, seed):
    s = (0.55, 1.0, 1.9)[size]
    d = s
    k = (0.6, 1.0, 1.7)[size]
    thump = sine(glide(105 / (1 + 0.15 * size), 36, d, 0.06 * k)) * decay(d, 0.11 * k, attack=0.0015)
    body = svf(noise(d, seed), glide(5500, 220, d, 0.11 * k), q=0.8) * decay(d, 0.16 * k, attack=0.002)
    rumble = lp(noise(d, seed + 1), 160) * decay(d, 0.3 * k, attack=0.01) * 2.0
    crack = crackle(d, 500 + 300 * size, 0.12 * k, seed + 2) * 0.9
    out = drive(thump * 1.1 + body * 0.9 + rumble, 1.8) + crack
    return tail(out, rt=0.25 + 0.25 * size, wet=0.18, seed=seed, bright=4000)


@sound(-18, fade=0.08)
def s_explode_s():
    return _explosion(0, 371)


@sound(-15, fade=0.15)
def s_explode_m():
    return _explosion(1, 381)


@sound(-12, fade=0.3)
def s_explode_l():
    return _explosion(2, 391)


@sound(-17, fade=0.08)
def s_robot_die():
    d = 0.75
    t = tt(d)
    n1 = bp(noise(d, 401), 300, 6000)
    ring = n1 * (sine(370, d) * 0.6 + sine(1130, d) * 0.4) * decay(d, 0.07, attack=0.001)
    clang = bell(420, d, ratios=(1, 2.6, 4.15, 6.4, 9.07), amps=(0.6, 0.45, 0.3, 0.2, 0.1),
                 decays=(0.16, 0.12, 0.08, 0.05, 0.03))
    thump = sine(glide(130, 40, d, 0.04)) * decay(d, 0.09)
    beep = lp(square(expseg(1300, 160, 0.32, 0.8), pw=0.5), 3000) * decay(0.32, 0.12, attack=0.002) * 0.3
    out = mix(crush(mix(ring, clang, thump), bits=5, hold_n=4, mix=0.4), at(beep, 0.05))
    return tail(drive(out, 1.5), rt=0.3, wet=0.15, seed=40)


@sound(-18, fade=0.06)
def s_creature_die():
    d = 0.5
    t = tt(d)
    f = cat(expseg(520, 1500, 0.045, 0.6), expseg(1500, 260, d - 0.045, 0.7))[: len(t)]
    f = f * (1 + 0.05 * np.sin(2 * np.pi * 23 * t))
    chirp = (sine(f) * 0.7 + tri(f * 1.01) * 0.3) * adsr(d, 0.005, 0.12, 0.3, 0.2)
    chirp = svf(chirp, expseg(4000, 900, d), q=3.0, mode="lp")
    squelch = svf(noise(d, 411), expseg(2200, 280, d, 0.7), q=6.0, mode="bp") * decay(d, 0.12, attack=0.004) * 0.8
    rng = np.random.default_rng(412)
    bl = []
    for i in range(4):
        bd = 0.035
        b = sine(rng.uniform(200, 420) * (1 + 2.0 * tt(bd) / bd)) * decay(bd, 0.012) * 0.35
        bl.append(at(b, 0.1 + i * 0.07))
    return tail(mix(chirp, squelch, *bl), rt=0.2, wet=0.12, seed=41)


@sound(-17, fade=0.1)
def s_ice_die():
    d = 0.85
    crack = hp(noise(d, 421), 1800) * decay(d, 0.012, attack=0.0004) * 1.2
    snap = sine(glide(2400, 900, d, 0.006)) * decay(d, 0.01) * 0.4
    tinkle = grains(d, 46, 2600, 9500, 422, glen=0.06, kind="bell", skew=1.8, amp_tau=0.25, spread=0.9) * 0.55
    glass = hp(noise(d, 423), 4500) * decay(d, 0.12, attack=0.002) * 0.25
    thud = sine(glide(260, 120, d, 0.02)) * decay(d, 0.03) * 0.4
    return tail(crack + snap + tinkle + glass + thud, rt=0.45, wet=0.2, seed=42, bright=10000)


@sound(-16, fade=0.15)
def s_gloam_die():
    d1 = 0.34
    t = tt(d1)
    # 1. the implosion: a reverse swell that sucks in and falls
    f = expseg(900, 180, d1, 0.8)
    suck = (saw(f) + saw(f * 1.012) + saw(f * 0.5)) / 3
    suck = svf(suck, expseg(800, 6000, d1, 2.0), q=1.6) * swell(d1, 2.4)
    hiss = svf(noise(d1, 431), expseg(1500, 9000, d1, 2.0), q=2.0, mode="bp") * swell(d1, 3.0) * 0.6
    part1 = suck + hiss
    # 2. the glitch: crushed, stuttered tail of the swell
    g = crush(part1, bits=4, hold_n=6, mix=0.8)
    glitch = stutter(np.concatenate([g, g[::-1]]), d1 - 0.05, 0.05, 7, shrink=0.7)
    # 3. the drop: a deep sub falling away with a dark rumble
    d3 = 0.9
    sub = sine(glide(85, 26, d3, 0.25)) * decay(d3, 0.3, attack=0.003) * 1.1
    dark = lp(noise(d3, 432), glide(1200, 120, d3, 0.15)[0]) * decay(d3, 0.2) * 0.4
    bits = crush(bp(noise(d3, 433), 400, 3000) * decay(d3, 0.05), bits=3, hold_n=12, mix=1.0) * 0.4
    tail_start = len(glitch) / SR
    out = mix(glitch, at(drive(sub + dark, 1.5) + bits, tail_start - 0.01))
    return tail(out, rt=0.6, wet=0.2, seed=43, bright=3000)


# --- bosses --------------------------------------------------------------------------------------------------------

def _roar(d, f0, seed, rise=0.15):
    t = tt(d)
    rng = np.random.default_rng(seed)
    jitter = lp(rng.standard_normal(len(t)), 8) * 4
    f = f0 * (1 + rise * np.sin(np.pi * np.clip(t / d, 0, 1)) + 0.03 * jitter)
    v = sum(saw(f * (1 + dt), ph0=i * 0.17) for i, dt in enumerate((0.0, 0.007, -0.011, 0.016))) / 4
    v = v + square(f * 0.5, pw=0.4) * 0.5
    v = v * (1 + 0.35 * np.sin(2 * np.pi * 27 * t))  # growl rattle
    # vowel "aa" -> "oo": two formants moving down
    f1 = expseg(720, 430, d, 1.0)
    f2 = expseg(1250, 780, d, 1.0)
    form = svf(v, f1, q=4.0, mode="bp") * 1.6 + svf(v, f2, q=5.0, mode="bp") * 1.0 + lp(v, 300) * 0.8
    breath = bp(noise(d, seed + 1), 300, 2600) * 0.25
    out = (form + breath) * adsr(d, 0.14, 0.4, 0.8, d * 0.3)
    return drive(out * 1.5, 2.2)


@sound(-11, fade=0.3)
def s_boss_roar():
    d = 2.2
    v = _roar(d, 68, 441)
    sub = sine(glide(60, 40, d, 0.8)) * adsr(d, 0.2, 0.5, 0.7, 0.6) * 0.6
    return tail(v + sub, rt=1.0, wet=0.25, seed=44, bright=3500)


@sound(-16, fade=0.06)
def s_boss_hit():
    d = 0.5
    clang = bell(205, d, ratios=(1, 2.41, 3.93, 5.62, 7.9), amps=(0.6, 0.5, 0.35, 0.2, 0.12),
                 decays=(0.16, 0.12, 0.08, 0.05, 0.03))
    thump = sine(glide(160, 48, d, 0.03)) * decay(d, 0.08, attack=0.001)
    burst = bp(noise(d, 451), 500, 5000) * decay(d, 0.025) * 0.8
    return tail(drive(mix(clang, thump, burst), 1.5), rt=0.35, wet=0.15, seed=45)


@sound(-10, fade=0.4)
def s_boss_die():
    d = 3.3
    parts = []
    for i, (t0, g) in enumerate(((0.0, 0.5), (0.32, 0.45), (0.55, 0.55), (0.9, 0.5), (1.15, 0.6))):
        parts.append(at(_explosion(1, 460 + 10 * i) * g, t0))
    roar = _roar(1.5, 52, 470, rise=-0.25) * 0.35
    parts.append(at(roar, 0.1))
    parts.append(at(_explosion(2, 480) * 1.0, 1.45))
    parts.append(at(sine(glide(70, 24, 1.6, 0.5)) * decay(1.6, 0.6, attack=0.005) * 0.8, 1.45))
    return tail(mix(*parts), rt=1.2, wet=0.2, seed=46, bright=3500)


# --- menu ----------------------------------------------------------------------------------------------------------

@sound(-28)
def s_menu_move():
    d = 0.06
    f = glide(1400, 1250, d, 0.01)
    return (sine(f) * 0.7 + tri(f * 2) * 0.12) * decay(d, 0.016, attack=0.0015)


@sound(-24, fade=0.05)
def s_menu_ok():
    def n(m, d, tau):
        f = mtof(m)
        return (sine(f, d) * 0.7 + tri(f * 2, d) * 0.15 + sine(f * 3, d) * 0.08) * decay(d, tau, attack=0.002)
    return tail(mix(n(84, 0.08, 0.035), at(n(91, 0.3, 0.09), 0.065)), rt=0.25, wet=0.15, seed=47)


@sound(-26, fade=0.04)
def s_menu_back():
    def n(m, d, tau):
        f = mtof(m)
        return (sine(f, d) * 0.75 + tri(f * 2, d) * 0.1) * decay(d, tau, attack=0.002)
    return tail(mix(n(84, 0.07, 0.03), at(n(79, 0.22, 0.06), 0.06)), rt=0.2, wet=0.12, seed=48)


# ---------------------------------------------------------------------------------------------------------------
# Analysis pictures
# ---------------------------------------------------------------------------------------------------------------

def _cmap(v):
    stops = np.array([[0, 0, 0], [30, 12, 70], [110, 30, 130], [200, 60, 90], [245, 140, 40], [255, 225, 120],
                      [255, 255, 255]], dtype=np.float64)
    xs = np.linspace(0, 1, len(stops))
    return np.stack([np.interp(v, xs, stops[:, c]) for c in range(3)], -1).astype(np.uint8)


def panel(name, x, info, w=256, h=150):
    from PIL import Image, ImageDraw
    img = Image.new("RGB", (w, h), (12, 12, 18))
    dr = ImageDraw.Draw(img)
    dr.text((3, 1), f"{name}  {info}", fill=(230, 230, 230))
    wy0, wh = 13, 34
    n = len(x)
    pk = max(np.max(np.abs(x)), 1e-9)
    cols = np.array_split(np.arange(n), w)
    mid = wy0 + wh // 2
    for i, c in enumerate(cols):
        if len(c) == 0:
            continue
        lo, hi = x[c].min() / pk, x[c].max() / pk
        dr.line([(i, mid - hi * wh / 2), (i, mid - lo * wh / 2)], fill=(120, 220, 255))
    dr.line([(0, mid), (w, mid)], fill=(60, 60, 80))
    sy0, sh = 49, h - 50
    f, t, Z = signal.stft(x, SR, nperseg=512, noverlap=512 - 32, boundary=None, padded=True)
    db = 20 * np.log10(np.abs(Z) + 1e-9)
    fl = np.exp(np.linspace(np.log(40), np.log(20000), sh))[::-1]
    rows = np.clip(np.searchsorted(f, fl), 0, len(f) - 1)
    m = db[rows]
    ci = np.clip((np.linspace(0, m.shape[1] - 1, w)).astype(int), 0, m.shape[1] - 1)
    m = m[:, ci]
    v = np.clip((m + 100) / 94, 0, 1)
    img.paste(Image.fromarray(_cmap(v)), (0, sy0))
    for hz in (100, 1000, 10000):
        y = sy0 + int((1 - (np.log(hz) - np.log(40)) / (np.log(20000) - np.log(40))) * sh)
        dr.line([(0, y), (4, y)], fill=(200, 200, 200))
    return img


def sheets(names, results):
    from PIL import Image
    per = 20
    cols = 4
    for s in range(0, len(names), per):
        chunk = names[s:s + per]
        rows = (len(chunk) + cols - 1) // cols
        sheet = Image.new("RGB", (cols * 258, rows * 152), (40, 40, 48))
        for i, nm in enumerate(chunk):
            x, pk, rms, lu, dur = results[nm]
            p = panel(nm, x, f"{dur:.2f}s {lu:.0f}LU pk{pk:.1f}")
            sheet.paste(p, ((i % cols) * 258, (i // cols) * 152))
        sheet.save(WORK / f"contact_{s // per + 1}.png")


# ---------------------------------------------------------------------------------------------------------------

def design_names():
    """The sound names listed in docs/DESIGN.md, section "Sounds"."""
    try:
        text = (ROOT / "docs" / "DESIGN.md").read_text(encoding="utf-8")
    except OSError:
        return []
    part = text.split("## Sounds", 1)[-1].split("\n## ", 1)[0]
    body = part.split("\n", 1)[-1].replace("\n", " ")
    return [w.strip(" .") for w in body.split(",") if w.strip(" .")]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("names", nargs="*", help="only these sounds")
    ap.add_argument("--list", action="store_true", help="print the sound names")
    ap.add_argument("--no-sheets", action="store_true", help="skip the contact sheets")
    args = ap.parse_args()
    if args.list:
        print("\n".join(SOUNDS))
        return
    unknown = [n for n in args.names if n not in SOUNDS]
    if unknown:
        sys.exit(f"unknown sounds: {unknown}")
    OUT.mkdir(parents=True, exist_ok=True)
    WORK.mkdir(parents=True, exist_ok=True)
    missing = [n for n in design_names() if n not in SOUNDS]
    if missing:
        print(f"WARNING: DESIGN.md lists sounds this generator does not make: {missing}")
    for nm in args.names or list(SOUNDS):
        fn, target, fade = SOUNDS[nm]
        y = finish(fn(), target, fade_out=fade)
        write_wav(OUT / f"{nm}.wav", y)
        print(f"{nm:14s} {len(y) / SR:5.2f} s")
    # the table covers every wav present, so a partial run keeps it complete
    results = {}
    for nm in SOUNDS:
        p = OUT / f"{nm}.wav"
        if not p.exists():
            continue
        x = read_wav(p)
        pk = 20 * np.log10(np.max(np.abs(x)) + 1e-12)
        rms = 20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-12)
        results[nm] = (x, pk, rms, loudness(x), len(x) / SR)
    with open(WORK / "levels.txt", "w", encoding="utf-8") as fh:
        fh.write("# Kip Kepler sound levels (tools/sfx/make_sfx.py)\n")
        fh.write("# peak dBFS, RMS dBFS over the whole file, max momentary loudness (K-weighted, 100 ms) in LU,\n")
        fh.write("# target LU, length, first/last sample\n")
        fh.write(f"{'name':16s}{'peak':>8s}{'rms':>8s}{'loud':>8s}{'target':>8s}{'len s':>8s}{'first':>8s}"
                 f"{'last':>8s}\n")
        for nm, (x, pk, rms, lu, dur) in results.items():
            fh.write(f"{nm:16s}{pk:8.2f}{rms:8.2f}{lu:8.1f}{SOUNDS[nm][1]:8d}{dur:8.3f}{x[0]:8.4f}{x[-1]:8.4f}\n")
    print(f"levels -> {WORK / 'levels.txt'}")
    if not args.no_sheets:
        sheets(list(results), results)
        print(f"contact sheets -> {WORK}")


if __name__ == "__main__":
    main()
