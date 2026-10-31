"""Rebuilds the sprite sheets into assets/sprites/ (and previews into work/sprites/).

    python tools/sprites/build.py              # all sheets
    python tools/sprites/build.py hero items   # only these models (module names in models/)
    python tools/sprites/build.py -j 1 hero    # serial (debugging)

Each model module in models/ provides jobs() -> [job...], frame(job) -> Sprite and sheets({job: Sprite}) -> [Sheet].
Frames render in parallel worker processes at below-normal priority (CPU only).
"""
import argparse
import importlib
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

MODELS = ["hero", "items", "objects", "shots", "fx"]
# episode 1 and 2 enemies
MODELS += ["sweeper", "sentry", "hoverdrone", "turret", "sparkmine", "rammer", "springbot", "fabricator"]
MODELS += ["beetle", "spitter", "mothling", "leaper", "snapvine", "sporepod", "stalker", "hivenest"]
# episode 3 enemies
MODELS += ["crystalcrab", "icebat", "shardling", "cryoturret", "minerbot", "burrower", "frostgolem", "wisp"]
# episode 4 enemies
MODELS += ["trooper", "shieldbot", "jetpacker", "gloamhound", "lasereye", "blinker", "brute", "riftgate"]
# bosses
MODELS += ["warden", "broodmother", "colossus", "gloam"]
# The third round: one new way of fighting per episode.
MODELS += ["mirrorbot", "brineeel", "shardsniper", "deckguard"]


def _below_normal():
    if os.name == "nt":
        try:
            import ctypes
            k = ctypes.windll.kernel32
            k.SetPriorityClass(k.GetCurrentProcess(), 0x00004000)  # BELOW_NORMAL_PRIORITY_CLASS
        except Exception:
            pass
    else:
        try:
            os.nice(5)
        except Exception:
            pass


def _init():
    _below_normal()


def _render(args):
    mod, job = args
    m = importlib.import_module(f"models.{mod}")
    return job, m.frame(job)


def build(names, workers=4):
    _below_normal()
    ok = True
    for name in names:
        t = time.time()
        m = importlib.import_module(f"models.{name}")
        jobs = m.jobs()
        frames = {}
        if workers > 1 and len(jobs) > 4:
            with ProcessPoolExecutor(max_workers=workers, initializer=_init) as ex:
                for job, spr in ex.map(_render, [(name, j) for j in jobs], chunksize=2):
                    frames[job] = spr
        else:
            for j in jobs:
                frames[j] = m.frame(j)
        for sh in m.sheets(frames):
            probs = sh.write()
            n = len(sh.frames)
            print(f"{sh.name}: {n} frames {sh.fw}x{sh.fh}, {len(sh.anims)} anims, {time.time() - t:.1f} s"
                  + ("" if not probs else "  PROBLEMS: " + "; ".join(probs)))
            ok &= not probs
    return ok


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("names", nargs="*", default=MODELS)
    ap.add_argument("-j", "--jobs", type=int, default=4)
    a = ap.parse_args()
    sys.exit(0 if build(a.names or MODELS, a.jobs) else 1)
