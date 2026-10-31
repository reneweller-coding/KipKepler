"""Raises the pools the checker calls deep (KeplerTool checkall: "WARN  pool: columns a-b, map line r: ...") so that
the surface lies at most three cells below the lower of the two banks: a pool throws the hero about four cells high
(phys::PoolLift), so from such a pool he gets out. The whole surface stretch the warning lies in is raised; spawns in
the flooded cells move up onto the new surface. Pools with walls on both sides (no bank) are only reported.

    python tools/levels/raise_pools.py work/check.txt [--dry]
    python tools/levels/raise_pools.py --level e2l5 --columns 50-107 --line 56 --to 52
"""
import argparse
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LEVELS = os.path.join(ROOT, "assets", "levels")
SOLID = set("#%XBdD")
TERRAIN = SOLID | set("-_^v<>~")
EMPTY = set(" .")


def load(level):
    text = open(os.path.join(LEVELS, level + ".txt"), "rb").read().decode("utf-8")
    lines = text.split("\n")
    a = lines.index("map") + 1
    b = lines.index("end", a)
    return lines, a, b


def save(level, lines):
    open(os.path.join(LEVELS, level + ".txt"), "wb").write("\n".join(lines).encode("utf-8"))


def at(rows, x, y):
    return rows[y][x] if 0 <= y < len(rows) and 0 <= x < len(rows[y]) else "#"


def bank_top(rows, x, y):
    """The line (0-based row) of the top of the wall in column x beside a pool surface at row y; None for a wall
    going up a long way (a cave wall, not a bank)."""
    t = y
    while t - 1 >= 0 and at(rows, x, t - 1) in SOLID:
        t -= 1
    if t == y and at(rows, x, y) not in SOLID:
        return None
    return t if y - t <= 12 else None


def raise_pool(level, col, line, to=None, dry=False):
    lines, a, b = load(level)
    rows = [list(r) for r in lines[a:b]]
    y = line - 1
    x = col - 1
    # The whole surface stretch.
    x0 = x
    while at(rows, x0 - 1, y) == "~":
        x0 -= 1
    x1 = x
    while at(rows, x1 + 1, y) == "~":
        x1 += 1
    if to is None:
        tops = [t for t in (bank_top(rows, x0 - 1, y), bank_top(rows, x1 + 1, y)) if t is not None]
        if not tops:
            print("%s columns %d-%d line %d: walls on both sides, raise it by hand" % (level, x0 + 1, x1 + 1, line))
            return False
        new = max(tops) + 3
    else:
        new = to - 1
    if new >= y:
        print("%s columns %d-%d line %d: banks within reach already" % (level, x0 + 1, x1 + 1, line))
        return False
    moved = []
    for cx in range(x0, x1 + 1):
        for cy in range(new, y):
            c = rows[cy][cx]
            if c in TERRAIN:
                continue
            if c not in EMPTY:
                moved.append((cx, cy, c))
            rows[cy][cx] = "~"
    for cx, cy, c in moved:
        # Onto the new surface (eels and pickups alike), the nearest free cell in the row above it.
        for d in sorted(range(-(x1 - x0 + 2), x1 - x0 + 3), key=abs):
            if at(rows, cx + d, new - 1) in EMPTY and cx + d >= 0:
                rows[new - 1][cx + d] = c
                break
        else:
            print("  %s: no room for %r from column %d, line %d" % (level, c, cx + 1, cy + 1))
    open_sides = [cy + 1 for cy in range(new, y) for side in (x0 - 1, x1 + 1) if at(rows, side, cy) not in TERRAIN]
    print("%s columns %d-%d: surface line %d -> %d%s%s" % (
        level, x0 + 1, x1 + 1, line, new + 1, ", moved %d" % len(moved) if moved else "",
        ", OPEN beside lines %s" % sorted(set(open_sides)) if open_sides else ""))
    if not dry:
        lines[a:b] = ["".join(r) for r in rows]
        save(level, lines)
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("report", nargs="?")
    ap.add_argument("--level")
    ap.add_argument("--columns")
    ap.add_argument("--line", type=int)
    ap.add_argument("--to", type=int, help="the new surface line")
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()
    if a.level:
        raise_pool(a.level, int(a.columns.split("-")[0]), a.line, a.to, a.dry)
        return
    warns, done = [], set()
    for line in open(a.report, encoding="utf-8"):
        m = re.match(r"WARN  pool: columns (\d+)-(\d+), map line (\d+):", line)
        if m:
            warns.append((int(m.group(1)), int(m.group(3))))
        m = re.match(r"(OK|FAIL) +(\w+):", line)
        if m:
            for col, ln in warns:
                if (m.group(2), ln, col) not in done:
                    raise_pool(m.group(2), col, ln, None, a.dry)
                    done.add((m.group(2), ln, col))
            warns = []


if __name__ == "__main__":
    main()
