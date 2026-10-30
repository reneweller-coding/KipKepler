"""Small helpers to build the hand-designed maps of episode 2 (no random generation: every room, ledge and item is
placed by explicit coordinates in the e2lN.py scripts).

Coordinates: x = column (0 at the left), y = row (0 at the top), rectangles inclusive.
"""
import os
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
TOOL = os.path.join(ROOT, "work", "tool", "KeplerTool.exe")
SKIP = ","   # transparent character in stamps


class Map:
    def __init__(self, w, h, fill="#"):
        self.w, self.h = w, h
        self.g = [[fill] * w for _ in range(h)]

    def get(self, x, y):
        return self.g[y][x] if 0 <= x < self.w and 0 <= y < self.h else "#"

    def set(self, x, y, ch):
        if not (0 <= x < self.w and 0 <= y < self.h):
            raise ValueError(f"set outside the map: {x},{y}")
        self.g[y][x] = ch

    def rect(self, x0, y0, x1, y1, ch="."):
        for y in range(min(y0, y1), max(y0, y1) + 1):
            for x in range(min(x0, x1), max(x0, x1) + 1):
                self.set(x, y, ch)

    def hline(self, x0, x1, y, ch):
        self.rect(x0, y, x1, y, ch)

    def vline(self, x, y0, y1, ch):
        self.rect(x, y0, x, y1, ch)

    def put(self, x, y, s):
        """A string along a row; ',' leaves the cell as it is."""
        for i, ch in enumerate(s):
            if ch != SKIP:
                self.set(x + i, y, ch)

    def stamp(self, x, y, block):
        """A multi-line block (leading/trailing blank lines dropped); ',' leaves the cell as it is."""
        lines = block.split("\n")
        while lines and not lines[0].strip():
            lines.pop(0)
        while lines and not lines[-1].strip():
            lines.pop()
        for j, line in enumerate(lines):
            self.put(x, y + j, line)

    def sky(self, x0, x1, top, ch=" "):
        """Columns x0..x1: every row above `top` becomes open sky (the surface's top row is `top`)."""
        for x in range(x0, x1 + 1):
            for y in range(0, top):
                self.set(x, y, ch)

    def ground(self, segs, ch=" "):
        """segs: (x0, x1, top) -- the open sky above the surface row `top`."""
        for x0, x1, top in segs:
            self.sky(x0, x1, top, ch)

    def replace(self, x0, y0, x1, y1, old, new):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                if self.get(x, y) in old:
                    self.set(x, y, new)

    def count(self, chars):
        return sum(1 for row in self.g for c in row if c in chars)

    def text(self):
        rows = ["".join(r).rstrip() for r in self.g]
        return "\n".join(rows)

    def save(self, name, header, legend):
        path = os.path.join(ROOT, "assets", "levels", name + ".txt")
        out = [h for h in header]
        out += [f"legend {k} {v}" for k, v in legend]
        out.append("map")
        out.append(self.text())
        out.append("end")
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(out) + "\n")
        return path


def stats(m, legend):
    enemies = sum(m.count(k) for k, v in legend if v.startswith("enemy"))
    ambush = sum(m.count(k) for k, v in legend if v.startswith("enemy") and "ambush" in v)
    kinds = {}
    for k, v in legend:
        if v.startswith("enemy"):
            t = v.split()[1]
            kinds[t] = kinds.get(t, 0) + m.count(k)
    named = sum(m.count(k) for k, v in legend if v.startswith("treasure"))
    seen, groups = set(), []
    for y in range(m.h):
        for x in range(m.w):
            if m.g[y][x] == "?" and (x, y) not in seen:
                stack, cells = [(x, y)], []
                seen.add((x, y))
                while stack:
                    cx, cy = stack.pop()
                    cells.append((cx, cy))
                    for nx, ny in ((cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)):
                        if m.get(nx, ny) == "?" and (nx, ny) not in seen:
                            seen.add((nx, ny))
                            stack.append((nx, ny))
                groups.append(min(cells))
    return {
        "size": f"{m.w}x{m.h}",
        "crystals": m.count("*"),
        "treasure": m.count("$") + named,
        "enemies": enemies,
        "ambush": ambush,
        "kinds": kinds,
        "health": m.count("+H"),
        "ammo": m.count("&"),
        "checkpoints": m.count("C"),
        "secrets": groups,
    }


def run(name, parts=()):
    """Check and render the level; parts = (x, y, w, h) windows rendered at full size."""
    lvl = os.path.join(ROOT, "assets", "levels", name + ".txt")
    out = os.path.join(ROOT, "work", "levels", "e2")
    os.makedirs(out, exist_ok=True)
    r = subprocess.run([TOOL, "check", lvl, os.path.join(out, name + "_check.png")], capture_output=True, text=True)
    print(r.stdout.strip())
    if r.stderr.strip():
        print(r.stderr.strip())
    if "--render" in sys.argv:
        subprocess.run([TOOL, "render", lvl, os.path.join(out, name + ".png"), "0.5"], check=True)
        for i, (x, y, w, h) in enumerate(parts):
            subprocess.run([TOOL, "render", lvl, os.path.join(out, f"{name}_p{i}.png"), str(x), str(y), str(w),
                            str(h)], check=True)


def ladder(m, xa, xb, floor, top, w=2):
    """One-way logs every 3 rows from the floor (row of its top) up towards `top` (the row of the floor reached at
    the end), alternating between columns xa and xb; the last step is 3 rows or less."""
    y, i = floor - 3, 0
    while y > top:
        x = xa if i % 2 == 0 else xb
        m.hline(x, x + w - 1, y, "-")
        y -= 3
        i += 1
