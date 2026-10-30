"""Small helper for hand-designing the Episode 3 levels of KIP KEPLER.

A level script fills a character grid with hand-placed shapes and hand-drawn ASCII rooms (no randomness), then
writes assets/levels/e3lN.txt and runs the checker / renderer of work/tool/KeplerTool.exe.

Coordinates: x = column (0 left), y = row (0 top), like the map file.
"""
import os
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
TOOL = os.path.join(ROOT, 'work', 'tool', 'KeplerTool.exe')
FIXED = set(' .#%-_BX^v<>~*$+H&kKdD?PEC')

# The legend every Episode 3 level may use (a level adds or overrides entries).
BASE_LEGEND = {
    'a': 'enemy crystalcrab',
    'A': 'enemy crystalcrab ambush',
    'b': 'enemy icebat',
    'h': 'enemy shardling',
    'J': 'enemy shardling ambush',
    'u': 'enemy cryoturret',
    'n': 'enemy minerbot',
    'N': 'enemy minerbot ambush',
    'w': 'enemy burrower',
    'g': 'enemy frostgolem',
    'G': 'enemy frostgolem ambush',
    'o': 'enemy wisp',
    'O': 'enemy wisp ambush',
    'p': 'power overdrive',
    'Q': 'power shield',
    'U': 'power boots',
    'I': 'treasure idol',
    'R': 'treasure crown',
    '@': 'spring',
}


class Lv:
    def __init__(self, w, h, fill='#'):
        self.w, self.h = w, h
        self.g = [[fill] * w for _ in range(h)]
        self.legend = dict(BASE_LEGEND)

    # ---- drawing -------------------------------------------------------------------------------------------
    def set(self, x, y, ch):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.g[y][x] = ch
        else:
            raise ValueError('outside the map: %d,%d' % (x, y))

    def get(self, x, y):
        return self.g[y][x] if 0 <= x < self.w and 0 <= y < self.h else '#'

    def fill(self, x, y, w, h, ch):
        """Rectangle x..x+w-1, y..y+h-1."""
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.set(xx, yy, ch)

    def rect(self, x0, y0, x1, y1, ch):
        """Rectangle with inclusive corners."""
        self.fill(x0, y0, x1 - x0 + 1, y1 - y0 + 1, ch)

    def put(self, x, y, s, skip=','):
        """A horizontal string; `skip` characters leave the cell as it is."""
        for i, ch in enumerate(s):
            if ch != skip:
                self.set(x + i, y, ch)

    def col(self, x, y, s, skip=','):
        for i, ch in enumerate(s):
            if ch != skip:
                self.set(x, y + i, ch)

    def paste(self, x, y, block, skip=','):
        """A hand-drawn block (multi-line string; a leading newline is dropped). `skip` = leave the cell."""
        rows = block.split('\n')
        if rows and rows[0] == '':
            rows = rows[1:]
        if rows and rows[-1].strip() == '':
            rows = rows[:-1]
        for j, r in enumerate(rows):
            self.put(x, y + j, r, skip)
        return len(rows)

    def sky(self, x, y_top, w, ch=' '):
        """Clear columns x..x+w-1 from row 0 down to (excluding) y_top: the surface is at y_top."""
        for xx in range(x, x + w):
            for yy in range(0, y_top):
                self.set(xx, yy, ch)

    def ground(self, x, steps, ch=' '):
        """A surface profile: steps = [(width, top_row), ...] from column x on; above top_row becomes sky."""
        for w, top in steps:
            self.sky(x, top, w, ch)
            x += w
        return x

    def runs(self, x, spec, ch='.'):
        """A cave by its profile: spec = [(width, top_row, floor_row), ...] from column x on; rows top..floor-1 are
        carved, the floor row stays as it is."""
        for w, top, floor in spec:
            self.fill(x, top, w, floor - top, ch)
            x += w
        return x

    def replace(self, x, y, w, h, old, new):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                if self.g[yy][xx] == old:
                    self.g[yy][xx] = new

    # ---- output --------------------------------------------------------------------------------------------
    def stats(self):
        flat = ''.join(''.join(r) for r in self.g)
        enemies = sum(flat.count(c) for c, v in self.legend.items() if v.startswith('enemy'))
        treasure = flat.count('$') + sum(flat.count(c) for c, v in self.legend.items() if v.startswith('treasure'))
        return {
            'size': '%dx%d' % (self.w, self.h),
            'crystals': flat.count('*'),
            'treasure': treasure,
            'enemies': enemies,
            'health': flat.count('+') + flat.count('H'),
            'ammo': flat.count('&'),
            'checkpoints': flat.count('C'),
        }

    def save(self, name, meta):
        used = set(''.join(''.join(r) for r in self.g))
        for c in used:
            if c not in FIXED and c not in self.legend:
                raise ValueError('character %r used but not in the legend' % c)
        for c in ('P', 'E'):
            n = sum(r.count(c) for r in self.g)
            if n != 1:
                raise ValueError('%s appears %d times' % (c, n))
        lines = ['# %s -- Episode 3, made by tools/levels/e3/%s.py (hand-placed rooms)' % (name, name)]
        for k, v in meta:
            lines.append('%-9s %s' % (k, v))
        for c in sorted(self.legend, key=lambda c: (not c.isalpha(), c)):
            if c in used:
                lines.append('legend %s  %s' % (c, self.legend[c]))
        lines.append('map')
        for r in self.g:
            lines.append(''.join(r).rstrip() if all(ch == ' ' for ch in r) else ''.join(r))
        lines.append('end')
        path = os.path.join(ROOT, 'assets', 'levels', name + '.txt')
        with open(path, 'w', encoding='utf-8', newline='\n') as f:
            f.write('\n'.join(lines) + '\n')
        return path


def check(name):
    lvl = os.path.join('assets', 'levels', name + '.txt')
    png = os.path.join('work', 'levels', 'e3', name + '_check.png')
    r = subprocess.run([TOOL, 'check', lvl, png], cwd=ROOT, capture_output=True, text=True)
    return r.stdout + r.stderr


def render(name, scale=0.5, part=None, out=None):
    lvl = os.path.join('assets', 'levels', name + '.txt')
    if part:
        out = out or os.path.join('work', 'levels', 'e3', '%s_%d_%d.png' % (name, part[0], part[1]))
        args = [TOOL, 'render', lvl, out] + [str(v) for v in part]
    else:
        out = out or os.path.join('work', 'levels', 'e3', name + '.png')
        args = [TOOL, 'render', lvl, out, str(scale)]
    r = subprocess.run(args, cwd=ROOT, capture_output=True, text=True)
    return out, r.stdout + r.stderr


def main(build, name, meta):
    """Build, save, check; `python e3lN.py render [x y w h ...]` also renders."""
    L = build()
    L.save(name, meta)
    print(L.stats())
    print(check(name))
    args = sys.argv[1:]
    if args and args[0] == 'render':
        nums = [int(a) for a in args[1:]]
        if not nums:
            print(render(name, 0.5))
        for i in range(0, len(nums), 4):
            print(render(name, part=nums[i:i + 4]))
