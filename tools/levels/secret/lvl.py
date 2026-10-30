"""Small helper for the four secret levels of KIP KEPLER (e1s ... e4s).

A level script fills a character grid with hand-placed shapes and hand-drawn ASCII stamps (no randomness), then
writes assets/levels/e<N>s.txt and runs the checker / renderer of work/tool/KeplerTool.exe into work/levels/secret/.

Coordinates: x = column (0 left), y = row (0 top), like the map file.
"""
import os
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
TOOL = os.path.join(ROOT, 'work', 'tool', 'KeplerTool.exe')
OUT = os.path.join('work', 'levels', 'secret')
FIXED = set(' .#%-_BX^v<>~*$+H&kKdD?PEC')


class Lv:
    def __init__(self, w, h, fill='#'):
        self.w, self.h = w, h
        self.g = [[fill] * w for _ in range(h)]
        self.legend = {}

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

    def mirror(self, x0, y0, w, h, axis_x, swap=None):
        """Copies the rectangle x0..x0+w-1 mirrored around the column axis_x (the copy's column = 2*axis_x - x).
        `swap` maps characters that must change in the mirror (e.g. '<' <-> '>')."""
        swap = swap or {'<': '>', '>': '<'}
        cells = [(x, y, self.g[y][x]) for y in range(y0, y0 + h) for x in range(x0, x0 + w)]
        for x, y, ch in cells:
            self.set(2 * axis_x - x, y, swap.get(ch, ch))

    def replace(self, x, y, w, h, old, new):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                if self.g[yy][xx] == old:
                    self.g[yy][xx] = new

    def count(self, ch):
        return sum(r.count(ch) for r in self.g)

    # ---- output --------------------------------------------------------------------------------------------
    def stats(self):
        flat = ''.join(''.join(r) for r in self.g)
        n = lambda pre: sum(flat.count(c) for c, v in self.legend.items() if v.startswith(pre))
        return {
            'size': '%dx%d' % (self.w, self.h),
            'crystals': flat.count('*'),
            'treasure $': flat.count('$'),
            'treasure named': n('treasure'),
            'crowns': n('treasure crown'),
            'idols': n('treasure idol'),
            'enemies': n('enemy'),
            'elite': sum(flat.count(c) for c, v in self.legend.items() if v.startswith('enemy') and 'elite' in v),
            'health': flat.count('+') + flat.count('H'),
            'ammo': flat.count('&'),
            'lore': n('lore'),
            'springs': n('spring'),
        }

    def save(self, name, meta, script):
        used = set(''.join(''.join(r) for r in self.g))
        for c in self.legend:
            if c in FIXED:
                raise ValueError('legend character %r is a fixed map character' % c)
        for c in used:
            if c not in FIXED and c not in self.legend:
                raise ValueError('character %r used but not in the legend' % c)
        for c in ('P', 'E'):
            n = sum(r.count(c) for r in self.g)
            if n != 1:
                raise ValueError('%s appears %d times' % (c, n))
        lines = ['# %s -- secret level, written by tools/levels/secret/%s (hand-placed rooms)' % (name, script)]
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
    png = os.path.join(OUT, name + '_check.png')
    r = subprocess.run([TOOL, 'check', lvl, png], cwd=ROOT, capture_output=True, text=True)
    return r.stdout + r.stderr


def render(name, scale=0.5, part=None, out=None):
    lvl = os.path.join('assets', 'levels', name + '.txt')
    if part:
        out = out or os.path.join(OUT, '%s_%d_%d.png' % (name, part[0], part[1]))
        args = [TOOL, 'render', lvl, out] + [str(v) for v in part]
    else:
        out = out or os.path.join(OUT, name + '.png')
        args = [TOOL, 'render', lvl, out, str(scale)]
    r = subprocess.run(args, cwd=ROOT, capture_output=True, text=True)
    return out, r.stdout + r.stderr


def main(build, name, meta):
    """Build and save; `python e1s.py check` runs the checker, `render [x y w h ...]` renders (whole level without
    numbers), `ascii` prints the map."""
    os.makedirs(os.path.join(ROOT, OUT), exist_ok=True)
    L = build()
    L.save(name, meta, name + '.py')
    print(L.stats())
    args = sys.argv[1:]
    if 'ascii' in args:
        for y, r in enumerate(L.g):
            print('%3d %s' % (y, ''.join(r)))
    if 'check' in args:
        print(check(name))
    if 'render' in args:
        nums = [int(a) for a in args[args.index('render') + 1:] if a.lstrip('-').isdigit()]
        if not nums:
            print(render(name, 0.5))
        for i in range(0, len(nums), 4):
            print(render(name, part=nums[i:i + 4]))
