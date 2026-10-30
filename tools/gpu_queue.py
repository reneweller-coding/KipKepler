"""Runs Kip Kepler's GPU jobs one after the other, politely: it waits until no other job holds the shared flag
G:/Tools/Games/GPU_BELEGT.txt, no G:/Tools/Games/GPU_PAUSE.txt exists, no game of the sister projects runs and enough
GPU memory is free -- for a whole minute -- then holds the flag itself while its jobs run.

    python tools/gpu_queue.py music stills voices
"""
import os
import random
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FLAG = r"G:\Tools\Games\GPU_BELEGT.txt"
PAUSE = r"G:\Tools\Games\GPU_PAUSE.txt"
GAMES = ("kipkepler.exe", "spaceopera.exe", "darkconcordance", "sunstreak", "tyrian")
NEED_MB = 24000
AUDIOGEN_PY = r"G:\Tools\PythonSkripts\AudioGenerator\venv\Scripts\python.exe"
QWEN_PY = r"G:\Tools\VoiceLab\env-qwen\python.exe"


def free_mb():
    try:
        out = subprocess.run(["nvidia-smi", "--query-gpu=memory.free", "--format=csv,noheader,nounits"], capture_output=True,
                             text=True).stdout
        return int(out.strip().splitlines()[0])
    except Exception:
        return 0


def games_running():
    out = subprocess.run(["tasklist"], capture_output=True, text=True).stdout.lower()
    return any(g in out for g in GAMES)


def wait_free():
    # Other sessions' queues wait for the same flag: a random length of quiet keeps two of them from starting together.
    need = 60 + random.randint(0, 40)
    quiet = 0
    while quiet < need:
        busy = os.path.exists(FLAG) or os.path.exists(PAUSE) or games_running() or free_mb() < NEED_MB
        quiet = 0 if busy else quiet + 5
        time.sleep(5)


def hold(what):
    """Takes the flag; false when another queue wrote it at the same moment (read back after a few seconds)."""
    mine = "KipKepler GPU queue (%s), %s, %d\n" % (what, time.ctime(), os.getpid())
    with open(FLAG, "w", encoding="utf-8") as f:
        f.write(mine)
    time.sleep(4)
    try:
        return open(FLAG, encoding="utf-8").read() == mine
    except OSError:
        return False


def release():
    if os.path.exists(FLAG):
        os.remove(FLAG)


def run(cmd, env=None):
    print(time.strftime("%H:%M:%S"), " ".join(cmd), flush=True)
    r = subprocess.run(cmd, cwd=ROOT, env=env, creationflags=0x00004000 if os.name == "nt" else 0)
    print(time.strftime("%H:%M:%S"), "exit", r.returncode, flush=True)
    return r.returncode


def main():
    jobs = sys.argv[1:] or ["music", "stills"]
    for job in jobs:
        while True:
            wait_free()
            if hold(job):
                break
        try:
            env = dict(os.environ, KEPLER_GPU_FLAG_HELD="1", PYTHONUTF8="1")
            if job == "music":
                run([AUDIOGEN_PY, os.path.join("tools", "music", "make_music.py")], env)
            elif job == "stills":
                if run([sys.executable, os.path.join("tools", "story", "make_stills.py"), "paint"], env) == 0:
                    run([sys.executable, os.path.join("tools", "story", "make_stills.py"), "pixel"], env)
                    run([sys.executable, os.path.join("tools", "story", "make_stills.py"), "sheet"], env)
            elif job == "voices":
                run([QWEN_PY, os.path.join("tools", "voices", "make_voices.py")], dict(env, PYTHONNOUSERSITE="1"))
        finally:
            release()


if __name__ == "__main__":
    main()
