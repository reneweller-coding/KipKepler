"""Makes Kip Kepler's music: tools/music/music.json -> the AudioGenerator's soundtrack mode (ACE-Step 1.5, local on
the GPU) -> work/music, then every take levelled to the same loudness and written as OGG Vorbis (what raylib plays)
-> assets/music/<cue>_t<take>.ogg (the game picks a take per level).

    G:\\Tools\\PythonSkripts\\AudioGenerator\\venv\\Scripts\\python.exe tools\\music\\make_music.py [--encode-only]

The generator runs below normal priority and writes G:/Tools/Games/GPU_BELEGT.txt while it runs (the shared GPU
flag of the sister projects). Needs numpy, scipy, soundfile (the AudioGenerator's venv has them) and ffmpeg.
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile

import numpy as np
import soundfile as sf
from scipy.signal import lfilter

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
AUDIOGEN = r"G:\Tools\PythonSkripts\AudioGenerator"
FLAG = r"G:\Tools\Games\GPU_BELEGT.txt"
PLANNER = "acestep-5Hz-lm-1.7B"
MUSIC_LUFS = -20.0   # the effects peak higher; the music sits under them
PEAK_DB = -1.0


def kweight(x, fs):
    """BS.1770 K-weighting: a high shelf (+4 dB above ~1.7 kHz) and a high pass at ~38 Hz."""
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
    b2 = [1.0, -2.0, 1.0]
    a2 = [1.0 + alpha, -2.0 * np.cos(w0), 1.0 - alpha]
    return lfilter(b2, a2, lfilter(b1, a1, x, axis=0), axis=0)


def lufs(x, fs):
    """Integrated loudness (BS.1770-4: 400 ms blocks, 75 % overlap, absolute and relative gate)."""
    y = kweight(x, fs)
    block, hop = int(0.4 * fs), int(0.1 * fs)
    if len(y) < block:
        return -70.0
    powers = []
    for start in range(0, len(y) - block + 1, hop):
        powers.append(float(np.mean(np.sum(y[start:start + block] ** 2, axis=1))))
    powers = np.array(powers)
    loud = -0.691 + 10 * np.log10(np.maximum(powers, 1e-12))
    gated = powers[loud > -70]
    if not len(gated):
        return -70.0
    rel = -0.691 + 10 * np.log10(np.mean(gated)) - 10
    gated = powers[(loud > -70) & (loud > rel)]
    return -0.691 + 10 * np.log10(np.mean(gated))


def encode(data, fs, path, quality=4):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fd, tmp = tempfile.mkstemp(suffix=".wav")
    os.close(fd)
    try:
        sf.write(tmp, data.astype(np.float32), fs, subtype="FLOAT")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", tmp, "-c:a", "libvorbis", "-q:a", str(quality), path],
                       check=True)
    finally:
        os.remove(tmp)


def generate(spec, work):
    env = dict(os.environ, PYTHONUTF8="1")
    flags = 0x00004000 if os.name == "nt" else 0   # BELOW_NORMAL_PRIORITY_CLASS
    held = os.environ.get("KEPLER_GPU_FLAG_HELD") == "1"   # the GPU queue holds the flag for the whole run
    if not held:
        with open(FLAG, "w", encoding="utf-8") as f:
            f.write("KipKepler make_music.py (ACE-Step)\n")
    try:
        with open(os.path.join(work, "gen.log"), "w", encoding="utf-8") as out:
            # The smaller planner (1.7B instead of 4B) leaves several GB of the GPU free for the desktop.
            r = subprocess.run([os.path.join(AUDIOGEN, "venv", "Scripts", "python.exe"), "main.py", "--soundtrack", spec,
                                "--soundtrack-out", work, "--planner", PLANNER], cwd=AUDIOGEN, env=env, stdout=out,
                               stderr=subprocess.STDOUT, creationflags=flags)
    finally:
        if not held and os.path.exists(FLAG):
            os.remove(FLAG)
    if r.returncode:
        sys.exit("generator failed (%d), see %s" % (r.returncode, os.path.join(work, "gen.log")))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--encode-only", action="store_true")
    args = ap.parse_args()
    spec = os.path.join(ROOT, "tools", "music", "music.json")
    work = os.path.join(ROOT, "work", "music")
    os.makedirs(work, exist_ok=True)
    if not args.encode_only:
        generate(spec, work)
    found = [d for d in os.listdir(work) if os.path.isfile(os.path.join(work, d, "manifest.json"))]
    if not found:
        sys.exit("no manifest.json under " + work)
    src = os.path.join(work, found[0])
    manifest = json.load(open(os.path.join(src, "manifest.json"), encoding="utf-8"))
    out = os.path.join(ROOT, "assets", "music")
    total = 0
    for cue in manifest["cues"]:
        files = [f for lv in cue["levels"] for f in lv["files"]]
        shown = []
        for n, f in enumerate(files[:2]):
            x, fs = sf.read(os.path.join(src, f), dtype="float32", always_2d=True)
            gain = min(MUSIC_LUFS - lufs(x, fs), PEAK_DB - 20 * np.log10(max(1e-9, float(np.max(np.abs(x))))))
            path = os.path.join(out, "%s_t%d.ogg" % (cue["id"], n + 1))
            encode(x * 10.0 ** (gain / 20.0), fs, path)
            total += os.path.getsize(path)
            shown.append("t%d %+.1f dB" % (n + 1, gain))
        print("%-12s %s" % (cue["id"], ", ".join(shown)))
    print("music: %.1f MB" % (total / 1e6))


if __name__ == "__main__":
    main()
