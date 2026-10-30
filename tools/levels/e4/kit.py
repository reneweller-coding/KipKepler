"""Small map kit for the hand-designed levels of episode 4 (KIP KEPLER).

Every room, floor, platform and pickup is placed by hand at chosen coordinates (tiles, x right, y down); the kit only
draws rectangles, lines and multi-line ASCII stamps onto a canvas and writes the level file (docs/DESIGN.md).
Nothing here is random.
"""
import os
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
TOOL = os.path.join(ROOT, 'work', 'tool', 'KeplerTool.exe')
FIXED = set(' .#%-_BX^v<>~*$+H&kKdD?PEC')


class Map:
    """A level canvas: rows of characters plus keys and legend."""

    def __init__(self, w, h, fill='#'):
        self.w, self.h = w, h
        self.g = [[fill] * w for _ in range(h)]
        self.keys = []      # (name, value) in order
        self.leg = {}       # char -> spec
        self.notes = []

    # ------------------------------------------------------------------ header
    def key(self, name, value):
        self.keys.append((name, str(value)))

    def legend(self, ch, spec):
        assert len(ch) == 1 and ch not in FIXED, 'legend char %r is a fixed character' % ch
        assert ch not in self.leg or self.leg[ch] == spec, 'legend %r redefined' % ch
        self.leg[ch] = spec
        return ch

    # ------------------------------------------------------------------ drawing
    def put(self, x, y, ch):
        if 0 <= x < self.w and 0 <= y < self.h:
            old = self.g[y][x]
            if old != ch and (old in '*$+H&kKPEC' or old in self.leg):
                self.notes.append('%r at %d,%d overwritten by %r' % (old, x, y, ch))
            self.g[y][x] = ch
        else:
            raise IndexError('put outside the map: %d,%d' % (x, y))

    def get(self, x, y):
        return self.g[y][x] if 0 <= x < self.w and 0 <= y < self.h else '#'

    def box(self, x, y, w, h, ch):
        """Fills the rectangle x..x+w-1, y..y+h-1."""
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.put(xx, yy, ch)

    def carve(self, x, y, w, h, ch):
        """Carves empty space; reports structure (not plain terrain) that it wipes out."""
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                old = self.get(xx, yy)
                if old not in '#. ?' and old != ch and not (old in '*$+H&kKPEC' or old in self.leg):
                    self.notes.append('carving %d,%d wipes %r' % (xx, yy, old))
                self.put(xx, yy, ch)

    def room(self, x, y, w, h):
        self.carve(x, y, w, h, '.')

    def sky(self, x, y, w, h):
        self.carve(x, y, w, h, ' ')

    def hl(self, x, y, n, ch):
        for i in range(n):
            self.put(x + i, y, ch)

    def vl(self, x, y, n, ch):
        for i in range(n):
            self.put(x, y + i, ch)

    def row(self, x, y, s):
        """Writes a string along a row; ',' keeps what is there, '.' over open sky keeps the sky (item trails)."""
        for i, c in enumerate(s):
            if c == ',' or (c == '.' and self.get(x + i, y) == ' '):
                continue
            self.put(x + i, y, c)

    def stamp(self, x, y, text):
        """A multi-line ASCII block; the first and last empty lines are dropped, ',' keeps what is there."""
        lines = text.split('\n')
        while lines and not lines[0].strip():
            lines.pop(0)
        while lines and not lines[-1].strip():
            lines.pop()
        for i, ln in enumerate(lines):
            self.row(x, y + i, ln)

    def replace(self, x, y, w, h, old, new):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                if self.get(xx, yy) in old:
                    self.put(xx, yy, new)

    def scatter(self, ch, cells):
        for (x, y) in cells:
            self.put(x, y, ch)

    # ------------------------------------------------------------------ output
    def stats(self):
        cnt = {}
        for r in self.g:
            for c in r:
                cnt[c] = cnt.get(c, 0) + 1
        enemies = {}
        for ch, spec in self.leg.items():
            words = spec.split()
            if words[0] == 'enemy' and cnt.get(ch):
                t = words[1] + (' ambush' if 'ambush' in words else '')
                enemies[t] = enemies.get(t, 0) + cnt[ch]
        # secret groups
        seen = set()
        groups = 0
        for y in range(self.h):
            for x in range(self.w):
                if self.g[y][x] == '?' and (x, y) not in seen:
                    groups += 1
                    st = [(x, y)]
                    seen.add((x, y))
                    while st:
                        cx, cy = st.pop()
                        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                            nx, ny = cx + dx, cy + dy
                            if 0 <= nx < self.w and 0 <= ny < self.h and self.g[ny][nx] == '?' and (nx, ny) not in seen:
                                seen.add((nx, ny))
                                st.append((nx, ny))
        tre = cnt.get('$', 0) + sum(cnt.get(ch, 0) for ch, s in self.leg.items() if s.startswith('treasure'))
        out = {
            'size': '%dx%d' % (self.w, self.h),
            'crystals': cnt.get('*', 0),
            'treasure': tre,
            'health': '%d small, %d big' % (cnt.get('+', 0), cnt.get('H', 0)),
            'ammo': cnt.get('&', 0),
            'checkpoints': cnt.get('C', 0),
            'secrets': groups,
            'enemies': sum(enemies.values()),
            'by type': enemies,
        }
        for ch, spec in self.leg.items():
            if not cnt.get(ch) and not spec.startswith('teleport'):
                self.notes.append('legend %r (%s) unused' % (ch, spec))
        return out

    def text(self, theme=None, bg=None):
        lines = []
        for name, value in self.keys:
            if theme and name == 'theme':
                value = theme
            if bg and name == 'bg':
                value = bg
            lines.append('%-9s %s' % (name, value))
        for ch in sorted(self.leg, key=lambda c: (self.leg[c].split()[0], c)):
            lines.append('legend %s  %s' % (ch, self.leg[ch]))
        lines.append('map')
        for r in self.g:
            lines.append(''.join(r).rstrip())
        lines.append('end')
        return '\n'.join(lines) + '\n'

    def write(self, level_id, preview_theme='station', preview_bg='station_b'):
        path = os.path.join(ROOT, 'assets', 'levels', level_id + '.txt')
        with open(path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(self.text())
        wdir = os.path.join(ROOT, 'work', 'levels', 'e4')
        os.makedirs(wdir, exist_ok=True)
        prev = os.path.join(wdir, level_id + '_preview.txt')
        with open(prev, 'w', encoding='utf-8', newline='\n') as f:
            f.write(self.text(theme=preview_theme, bg=preview_bg))
        return path, prev


def tool(*args):
    r = subprocess.run([TOOL] + [str(a) for a in args], cwd=ROOT, capture_output=True, text=True)
    return (r.stdout + r.stderr).strip()


def run(build, level_id, parts=(), scale=0.5, render=True):
    """Builds, writes, checks and renders a level. parts: (x, y, w, h) tuples rendered at full size."""
    m = build()
    path, prev = m.write(level_id)
    st = m.stats()
    for k, v in st.items():
        print('%-12s %s' % (k, v))
    for n in m.notes:
        print('NOTE', n)
    wdir = os.path.join('work', 'levels', 'e4')
    print(tool('check', os.path.join('assets', 'levels', level_id + '.txt'),
               os.path.join(wdir, level_id + '_check.png')))
    if render:
        print(tool('render', prev, os.path.join(wdir, level_id + '.png'), scale))
    for i, (x, y, w, h) in enumerate(parts):
        print(tool('render', prev, os.path.join(wdir, '%s_part%d.png' % (level_id, i)), x, y, w, h))
    return m


def main(build, level_id, parts=()):
    args = sys.argv[1:]
    if args and args[0] == 'part':
        x, y, w, h = map(int, args[1:5])
        m = build()
        _, prev = m.write(level_id)
        out = os.path.join('work', 'levels', 'e4', '%s_view_%d_%d.png' % (level_id, x, y))
        print(tool('render', prev, out, x, y, w, h))
        print(out)
        return
    if args and args[0] == 'checkpng':
        # enlarge the checker picture for a region (6 px per tile -> scale)
        from PIL import Image
        x, y, w, h = map(int, args[1:5])
        im = Image.open(os.path.join(ROOT, 'work', 'levels', 'e4', level_id + '_check.png'))
        im = im.crop((x * 6, y * 6, (x + w) * 6, (y + h) * 6))
        im = im.resize((im.width * 3, im.height * 3), Image.NEAREST)
        out = os.path.join(ROOT, 'work', 'levels', 'e4', '%s_checkzoom.png' % level_id)
        im.save(out)
        print(out)
        return
    run(build, level_id, parts, render=not (args and args[0] == 'norender'))
