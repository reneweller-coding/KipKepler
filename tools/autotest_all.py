"""Runs the autopilot over every level (36 + the 4 secret ones) in three processes below normal priority, muted and
without a window (the test runs on the processor alone and leaves the graphics card to others), each with a hard time
limit; the reports land in work/autotest/<worker>.txt and a summary is printed.

    python tools/autotest_all.py [--limit 600] [--minutes 45]
"""
import argparse
import os
import subprocess
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAME = os.path.join(ROOT, "bin", "msvc", "KipKepler.exe")
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
    os.makedirs(WORK, exist_ok=True)
    procs = {}
    for name, runs in WORKERS.items():
        report = os.path.join(WORK, name + ".txt")
        if os.path.exists(report):
            os.remove(report)
        # One shell line per worker: its runs one after the other.
        cmds = [[GAME, "--autotest", report, "--limit", a.limit] + r for r in runs]
        script = " & ".join(subprocess.list2cmdline(c) for c in cmds)
        procs[name] = subprocess.Popen(script, cwd=ROOT, shell=True, creationflags=0x08004000)  # below normal priority, no console window
    end = time.time() + a.minutes * 60
    while time.time() < end and any(p.poll() is None for p in procs.values()):
        time.sleep(5)
    for name, p in procs.items():
        if p.poll() is None:
            print("worker", name, "ran out of time")
            subprocess.run(["taskkill", "/T", "/F", "/PID", str(p.pid)], capture_output=True)
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
