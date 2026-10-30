"""Runs the autopilot over every level (36 + the 4 secret ones) in three processes below normal priority, muted and
headless, each with a hard time limit, while it holds the shared GPU flag G:/Tools/Games/GPU_BELEGT.txt; the reports
land in work/autotest/<worker>.txt and a summary is printed.

    python tools/autotest_all.py [--limit 600] [--minutes 45]
"""
import argparse
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAME = os.path.join(ROOT, "bin", "msvc", "KipKepler.exe")
FLAG = r"G:\Tools\Games\GPU_BELEGT.txt"
PAUSE = r"G:\Tools\Games\GPU_PAUSE.txt"
WORK = os.path.join(ROOT, "work", "autotest")
# Three workers of about the same length: the later episodes have the bigger levels.
WORKERS = {"a": [["--episode", "1"], ["--episode", "2"]],
           "b": [["--episode", "3"], ["--level", "assets/levels/e1s.txt"], ["--level", "assets/levels/e2s.txt"]],
           "c": [["--episode", "4"], ["--level", "assets/levels/e3s.txt"], ["--level", "assets/levels/e4s.txt"]]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", default="600", help="game seconds per level")
    ap.add_argument("--minutes", type=float, default=45, help="wall-clock limit per worker")
    a = ap.parse_args()
    if os.path.exists(FLAG) or os.path.exists(PAUSE):
        sys.exit("the GPU is taken: " + open(FLAG if os.path.exists(FLAG) else PAUSE, encoding="utf-8").read().strip())
    os.makedirs(WORK, exist_ok=True)
    with open(FLAG, "w", encoding="utf-8") as f:
        f.write("KipKepler autopilot test (headless, muted), %s\n" % time.ctime())
    try:
        procs = {}
        for name, runs in WORKERS.items():
            report = os.path.join(WORK, name + ".txt")
            if os.path.exists(report):
                os.remove(report)
            # One shell line per worker: its runs one after the other.
            cmds = [[GAME, "--autotest", report, "--limit", a.limit] + r for r in runs]
            script = " && ".join(subprocess.list2cmdline(c) for c in cmds).replace(" && ", " & ")
            procs[name] = subprocess.Popen(script, cwd=ROOT, shell=True, creationflags=0x00004000)
        end = time.time() + a.minutes * 60
        while time.time() < end and any(p.poll() is None for p in procs.values()):
            time.sleep(5)
        for name, p in procs.items():
            if p.poll() is None:
                print("worker", name, "ran out of time")
                subprocess.run(["taskkill", "/T", "/F", "/PID", str(p.pid)], capture_output=True)
    finally:
        if os.path.exists(FLAG):
            os.remove(FLAG)
    done = 0
    for name in WORKERS:
        report = os.path.join(WORK, name + ".txt")
        for line in open(report, encoding="utf-8", errors="replace") if os.path.exists(report) else []:
            w = line.split()
            ok = "finished=1" in line
            done += ok
            print("%-5s %s %s" % (w[0], "ok  " if ok else "FAIL", " ".join(x for x in w[1:7])))
    print("finished %d of 40" % done)


if __name__ == "__main__":
    main()
