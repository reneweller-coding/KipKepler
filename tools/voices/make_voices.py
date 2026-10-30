"""Speaks the Commodore's radio messages (assets/text/<lang>/radio.txt) with Qwen3-TTS, locally (G:\\Tools\\VoiceLab):

    design   her voice per language from a description (VoiceDesign 1.7B), a few takes, the one nearest the middle of
             her pitch range kept -> tools/voices/commodore_<lang>.flac and .txt (kept: later lines keep her voice)
    speak    every message cloned from that voice (Base 1.7B) -> work/voice/<lang>/radio_<id>.wav, again when its
             length does not fit its text
    encode   a light suit-radio colour, levelled, OGG Vorbis -> assets/voice/<lang>/radio_<id>.ogg

    set PYTHONNOUSERSITE=1
    G:\\Tools\\VoiceLab\\env-qwen\\python.exe tools\\voices\\make_voices.py [--lang de] [--only e1l1 ...] [--force]

Runs below normal priority on the GPU (the caller keeps G:/Tools/Games/GPU_BELEGT.txt, see tools/gpu_queue.py).
"""
import argparse
import os
import re
import sys

import numpy as np
import soundfile as sf
from scipy.signal import butter, sosfilt

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "tools", "music"))
import make_music  # noqa: E402  (loudness and encoding)

MODELS = r"G:\Tools\VoiceLab\models"
REFS = os.path.join(ROOT, "tools", "voices")
WORK = os.path.join(ROOT, "work", "voice")
LANGS = {"de": "German", "en": "English"}
DESCRIBE = ("A woman in her late fifties, a seasoned starfleet commodore speaking over the radio: a calm, warm alto "
            "voice, clear diction, crisp and authoritative, with dry, understated humour; a measured pace.")
PITCH = (150.0, 220.0)   # Hz, an alto
CANDIDATES = 4
BATCH = 16
VOICE_LUFS = -17.0       # above the music (-20)
PEAK_DB = -2.0
QUALITY = 3


def messages(lang):
    out = {}
    for line in open(os.path.join(ROOT, "assets", "text", lang, "radio.txt"), encoding="utf-8"):
        m = re.match(r"^radio\.([A-Za-z0-9_]+)\s*=\s*(.*)$", line.rstrip("\n"))
        if m:
            out[m.group(1)] = clean(m.group(2))
    return out


def clean(text):
    """What is spoken: no quote marks, no bracketed asides, shouted words in normal case (else the model spells them)."""
    text = re.sub(r"\([^)]*\)", " ", text)
    text = re.sub(r"[»«„“”\"]", "", text)
    text = re.sub(r"\b([A-ZÄÖÜ]{4,})\b", lambda m: m.group(1).capitalize(), text)
    return re.sub(r"\s+", " ", text).strip()


def below_normal():
    if os.name == "nt":
        import ctypes
        ctypes.windll.kernel32.SetPriorityClass(ctypes.windll.kernel32.GetCurrentProcess(), 0x00004000)


def plausible(wav, sr, text):
    seconds = len(wav) / sr
    return len(text) / 30.0 + 0.3 <= seconds <= len(text) / 6.0 + 2.0


def pitch(wav, sr):
    import librosa
    x = librosa.resample(np.asarray(wav, dtype=np.float32), orig_sr=sr, target_sr=16000)
    f0, _, _ = librosa.pyin(x, fmin=60, fmax=500, sr=16000, frame_length=1024)
    return float(np.nanmedian(f0)) if np.any(np.isfinite(f0)) else 1.0


def design(langs):
    need = [l for l in langs if not os.path.exists(os.path.join(REFS, "commodore_%s.flac" % l))]
    if not need:
        return
    import torch
    from qwen_tts import Qwen3TTSModel
    model = Qwen3TTSModel.from_pretrained(os.path.join(MODELS, "Qwen3-TTS-12Hz-1.7B-VoiceDesign"), device_map="cuda:0",
                                          dtype=torch.bfloat16, attn_implementation="sdpa")
    os.makedirs(REFS, exist_ok=True)
    for lang in need:
        said = messages(lang)
        text = " ".join([said["e1l1"], said["e2l1"]])
        wavs, sr = model.generate_voice_design(text=[text] * CANDIDATES, instruct=[DESCRIBE] * CANDIDATES,
                                               language=[LANGS[lang]] * CANDIDATES)
        heard = [(pitch(w, sr), w) for w in wavs if plausible(w, sr, text)] or [(pitch(w, sr), w) for w in wavs]
        f0, wav = min(heard, key=lambda h: abs(np.log(h[0] / np.sqrt(PITCH[0] * PITCH[1]))))
        print("  commodore %s: %s Hz, kept %.0f" % (lang, " ".join("%.0f" % h[0] for h in heard), f0), flush=True)
        sf.write(os.path.join(REFS, "commodore_%s.flac" % lang), wav, sr)
        with open(os.path.join(REFS, "commodore_%s.txt" % lang), "w", encoding="utf-8") as f:
            f.write(text + "\n")
    del model
    torch.cuda.empty_cache()


def speak(langs, only, force):
    todo = {}
    for lang in langs:
        os.makedirs(os.path.join(WORK, lang), exist_ok=True)
        for key, text in messages(lang).items():
            raw = os.path.join(WORK, lang, "radio_%s.wav" % key)
            if only and key not in only:
                continue
            if force and os.path.exists(raw):
                os.remove(raw)
            if not os.path.exists(raw):
                todo.setdefault(lang, []).append((key, text))
    if not todo:
        return
    import torch
    from qwen_tts import Qwen3TTSModel
    model = Qwen3TTSModel.from_pretrained(os.path.join(MODELS, "Qwen3-TTS-12Hz-1.7B-Base"), device_map="cuda:0",
                                          dtype=torch.bfloat16, attn_implementation="sdpa")
    for lang, lines in sorted(todo.items()):
        ref = os.path.join(REFS, "commodore_%s.flac" % lang)
        prompt = model.create_voice_clone_prompt(ref_audio=ref,
                                                 ref_text=open(ref[:-5] + ".txt", encoding="utf-8").read().strip())
        lines.sort(key=lambda l: len(l[1]))
        done = 0
        for i in range(0, len(lines), BATCH):
            batch = lines[i:i + BATCH]
            for attempt in range(4):
                if not batch:
                    break
                said = [t for _, t in batch]
                wavs, sr = model.generate_voice_clone(text=said, language=[LANGS[lang]] * len(said),
                                                      voice_clone_prompt=prompt * len(said),
                                                      max_new_tokens=int(12 * (len(max(said, key=len)) / 6.0 + 4)))
                again = []
                for (key, text), wav in zip(batch, wavs):
                    if plausible(wav, sr, text) or attempt == 3:
                        sf.write(os.path.join(WORK, lang, "radio_%s.wav" % key), wav, sr)
                        done += 1
                    else:
                        again.append((key, text))
                batch = again
            print("%d/%d  %s" % (done, len(lines), lang), flush=True)
    del model
    torch.cuda.empty_cache()


def trim(x, sr):
    hop = int(0.01 * sr)
    frames = np.array([np.sqrt(np.mean(x[i:i + hop] ** 2) + 1e-12) for i in range(0, max(1, len(x) - hop), hop)])
    loud = np.where(20.0 * np.log10(frames / frames.max()) > -40.0)[0]
    if not len(loud):
        return x
    return x[max(0, loud[0] * hop - int(0.05 * sr)):min(len(x), (loud[-1] + 1) * hop + int(0.15 * sr))]


def radio(x, sr):
    """A clean suit radio: a wide speech band, a touch of drive, a faint hiss (she must stay easy to follow)."""
    y = sosfilt(butter(2, [220.0, 5200.0], btype="band", fs=sr, output="sos"), x)
    y = np.tanh(1.6 * y / max(1e-6, np.max(np.abs(y)))) / np.tanh(1.6)
    return y + np.random.default_rng(len(x)).normal(0.0, 0.002, len(y))


def limit(x, sr, ceiling):
    from scipy.ndimage import maximum_filter1d, minimum_filter1d, uniform_filter1d
    w = int(0.02 * sr) | 1
    gain = np.minimum(1.0, 10.0 ** (ceiling / 20.0) / np.maximum(maximum_filter1d(np.abs(x), size=w), 1e-9))
    return x * uniform_filter1d(minimum_filter1d(gain, size=w), size=w)


def encode(langs, force):
    n = 0
    for lang in langs:
        for key in messages(lang):
            raw = os.path.join(WORK, lang, "radio_%s.wav" % key)
            out = os.path.join(ROOT, "assets", "voice", lang, "radio_%s.ogg" % key)
            if not os.path.exists(raw):
                continue
            if not force and os.path.exists(out) and os.path.getmtime(out) >= os.path.getmtime(raw):
                continue
            x, sr = sf.read(raw, dtype="float64")
            x = radio(trim(x, sr), sr)
            for _ in range(2):
                x = limit(x * 10.0 ** (min(12.0, VOICE_LUFS - make_music.lufs(x[:, None], sr)) / 20.0), sr, PEAK_DB)
            make_music.encode(x.astype(np.float32), sr, out, QUALITY)
            n += 1
    print("encoded", n)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", nargs="*", default=list(LANGS))
    ap.add_argument("--only", nargs="*", default=[], help="only these level ids")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--encode-only", action="store_true")
    a = ap.parse_args()
    below_normal()
    if not a.encode_only:
        design(a.lang)
        speak(a.lang, a.only, a.force)
    encode(a.lang, a.force and a.encode_only)


if __name__ == "__main__":
    main()
