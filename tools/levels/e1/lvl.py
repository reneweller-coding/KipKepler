"""Tiny helper for hand-designed Kip Kepler maps: a canvas, rectangles and hand-drawn ASCII stamps.

Nothing here is random: every room is drawn by hand in the level scripts; this only places them.
A stamp is a multi-line string; the backtick ` keeps what is already on the canvas.
"""
import os
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
TOOL = os.path.join(ROOT, 'work', 'tool', 'KeplerTool.exe')
FIXED = set(" .#%-_BX^v<>~*$+H&kKdD?PEC")


class Map:
    def __init__(self, w, h, fill='#'):
        self.w, self.h = w, h
        self.g = [[fill] * w for _ in range(h)]

    def rect(self, x, y, w, h, ch):
        """Fills a rectangle (x, y = top left)."""
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.set(xx, yy, ch)

    def set(self, x, y, ch):
        if not (0 <= x < self.w and 0 <= y < self.h):
            raise ValueError(f'outside the map: {x},{y}')
        self.g[y][x] = ch

    def get(self, x, y):
        return self.g[y][x]

    def hline(self, x, y, n, ch):
        for i in range(n):
            self.set(x + i, y, ch)

    def vline(self, x, y, n, ch):
        for i in range(n):
            self.set(x, y + i, ch)

    def put(self, x, y, s):
        """One row of characters (` keeps)."""
        for i, ch in enumerate(s):
            if ch != '`':
                self.set(x + i, y, ch)

    def stamp(self, x, y, text):
        """A hand-drawn block; the first and last empty lines of the literal are dropped."""
        lines = text.split('\n')
        while lines and lines[0].strip() == '':
            lines.pop(0)
        while lines and lines[-1].strip() == '':
            lines.pop()
        for j, line in enumerate(lines):
            self.put(x, y + j, line)

    def border(self):
        for x in range(self.w):
            if self.g[0][x] not in '#%':
                self.g[0][x] = '#'
            if self.g[self.h - 1][x] not in '#%~^':
                self.g[self.h - 1][x] = '#'
        for y in range(self.h):
            for x in (0, self.w - 1):
                if self.g[y][x] not in '#%':
                    self.g[y][x] = '#'

    def place(self, x, y, ch):
        """Places a single item/enemy, but only on an empty cell (never overwrites a design)."""
        if self.g[y][x] not in ' .':
            raise ValueError(f'cell {x},{y} is {self.g[y][x]!r}, not empty')
        self.g[y][x] = ch

    def rows(self):
        return [''.join(r) for r in self.g]


def write(name, header, legend, m, signs=None):
    """Writes assets/levels/<name>.txt; header = list of (key, value), legend = dict char -> kind."""
    for ch in legend:
        if ch in FIXED or len(ch) != 1:
            raise ValueError(f'legend char {ch!r} is a fixed map character')
    used = set(''.join(m.rows()))
    for ch in used:
        if ch not in FIXED and ch not in legend:
            raise ValueError(f'char {ch!r} on the map has no legend')
    out = [f'# {name} -- written by tools/levels/e1/{name}.py (hand-designed rooms)']
    for k, v in header:
        out.append(f'{k:<9} {v}')
    for ch, kind in legend.items():
        if ch in used:
            out.append(f'legend {ch}  {kind}')
    out.append('map')
    out += m.rows()
    out.append('end')
    path = os.path.join(ROOT, 'assets', 'levels', name + '.txt')
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(out) + '\n')
    stats(name, legend, m)
    return path


def stats(name, legend, m):
    rows = m.rows()
    text = ''.join(rows)
    enemies = {}
    for ch, kind in legend.items():
        n = text.count(ch)
        if kind.startswith('enemy') and n:
            t = kind.split()[1] + (' ambush' if 'ambush' in kind else '')
            enemies[t] = enemies.get(t, 0) + n
    # secrets: connected groups of '?'
    seen = set()
    groups = 0
    for y in range(m.h):
        for x in range(m.w):
            if rows[y][x] == '?' and (x, y) not in seen:
                groups += 1
                st = [(x, y)]
                seen.add((x, y))
                while st:
                    cx, cy = st.pop()
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        nx, ny = cx + dx, cy + dy
                        if 0 <= nx < m.w and 0 <= ny < m.h and rows[ny][nx] == '?' and (nx, ny) not in seen:
                            seen.add((nx, ny))
                            st.append((nx, ny))
    print(f'{name}: {m.w}x{m.h} crystals {text.count("*")} treasure {text.count("$") + sum(text.count(c) for c, k in legend.items() if k.startswith("treasure"))} '
          f'secrets {groups} health {text.count("+")}+{text.count("H")}H checkpoints {text.count("C")} '
          f'enemies {sum(enemies.values())} {enemies}')


def check(name, render=True):
    lvl = os.path.join(ROOT, 'assets', 'levels', name + '.txt')
    out = os.path.join(ROOT, 'work', 'levels', 'e1')
    r = subprocess.run([TOOL, 'check', lvl, os.path.join(out, name + '_check.png')], capture_output=True, text=True)
    print(r.stdout.strip())
    if render:
        subprocess.run([TOOL, 'render', lvl, os.path.join(out, name + '.png'), '0.5'])


def part(name, x, y, w=24, h=14, tag=None, level=None):
    lvl = level or os.path.join(ROOT, 'assets', 'levels', name + '.txt')
    out = os.path.join(ROOT, 'work', 'levels', 'e1', f'{name}_{tag or f"{x}_{y}"}.png')
    subprocess.run([TOOL, 'render', lvl, out, str(x), str(y), str(w), str(h)])
    return out


if __name__ == '__main__':
    # python lvl.py part <name> x y [w h] [tag]
    if sys.argv[1] == 'part':
        a = sys.argv[2:]
        print(part(a[0], int(a[1]), int(a[2]), int(a[3]) if len(a) > 3 else 24, int(a[4]) if len(a) > 4 else 14,
                   a[5] if len(a) > 5 else None))
