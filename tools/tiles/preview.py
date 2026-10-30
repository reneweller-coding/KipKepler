"""Renders a test map with a theme's tile set the way the engine will (masks, variants by cell hash, back wall behind
every non-sky cell, deco on back walls), to work/tiles/<theme>_preview.png: the whole map at 1x, a 640 x 360 view at
2x, and the block / liquid / platform / deco sheets at 2x.

    python tools/tiles/preview.py station [--frame N] [--crop x y w h scale]
"""
import argparse
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tilelib import ROOT, T, DIRS  # noqa: E402

MAP = [
    "####################################################",
    "#.........vvv.......#.......#                 ######",
    "#...................#.......#                   ####",
    "#....%%%.......................     #            ###",
    "#....%%%..............---.....     ###     #      ##",
    "#.........#........................ #   #   #      #",
    "#.........#....###..........#.....     # #         #",
    "#...#.....#....#.#..........#.....      #     ##   #",
    "#...#..........###.....B....#.....  -------   ##   #",
    "#>..#..................B....#.....                 #",
    "#>..#....----..........B....#..d..  #  #  #  #     #",
    "######.......######.........#..d..                 #",
    "#....#..................######..d..#.#.#.#.        #",
    "#....#.................##....#######.#.#.###########",
    "#.......%%%%%%........###...........#.#.#.#.......##",
    "#......%%%%%%%%......####...................D....<##",
    "#..^^^.%%%%%%%%.....#####.......-..........ZD....<##",
    "###############....#########..cccc.###____..########",
    "#.............#~~~~#.......#.......###......#.##...#",
    "#.............#~~~~#.......#AAAA...###......########",
    "#####.........######.......#.......###.....#########",
    "#...#......#####...........#...........#....########",
    "#...#......#####..#.#......#...######..#....########",
    "#...........###...#.#.......X.....##........########",
    "####################################################",
]

SOLID = set("#%XBdD")


def cell(mp, x, y):
    if y < 0 or y >= len(mp) or x < 0 or x >= len(mp[0]):
        return "#"
    return mp[y][x]


def mask_of(mp, x, y, pred):
    m = 0
    for i, (dx, dy) in enumerate(DIRS):
        if pred(cell(mp, x + dx, y + dy)):
            m |= 1 << i
    return m


def vhash(x, y):
    h = (x * 73856093) ^ (y * 19349663)
    h = (h ^ (h >> 13)) * 1274126177
    return (h >> 7) & 3


def load(path):
    if not os.path.exists(path):
        return None
    return Image.open(path).convert("RGBA")


def tile_of(sheet, idx, cols=16):
    x, y = (idx % cols) * T, (idx // cols) * T
    return sheet.crop((x, y, x + T, y + T))


def sky(w, h):
    rng = np.random.default_rng(5)
    a = np.zeros((h, w, 4), np.uint8)
    ys = np.linspace(0, 1, h)[:, None]
    a[..., 0] = (8 + 10 * ys).astype(np.uint8)
    a[..., 1] = (10 + 14 * ys).astype(np.uint8)
    a[..., 2] = (26 + 30 * ys).astype(np.uint8)
    a[..., 3] = 255
    for _ in range(w * h // 900):
        x, y = rng.integers(0, w), rng.integers(0, h)
        c = rng.integers(120, 255)
        a[y, x, :3] = (c, c, min(255, c + 20))
    return Image.fromarray(a, "RGBA")


def render(theme, frame=0, glow_boost=False):
    d = os.path.join(ROOT, "assets", "tiles", theme)
    ta, tb, bk = load(os.path.join(d, "terrain_a.png")), load(os.path.join(d, "terrain_b.png")), load(
        os.path.join(d, "back.png"))
    pl, bl, lq, dc = (load(os.path.join(d, n + ".png")) for n in ("platform", "blocks", "liquid", "deco"))
    mp = MAP
    H, W = len(mp), len(mp[0])
    img = sky(W * T, H * T)
    rng = np.random.default_rng(11)

    def solid(c):
        return c in SOLID

    def notsky(c):
        return c != " "

    # back wall
    for y in range(H):
        for x in range(W):
            c = mp[y][x]
            if c != " " and bk is not None:
                m = mask_of(mp, x, y, notsky)
                img.alpha_composite(tile_of(bk, vhash(x, y) * 256 + m), (x * T, y * T))
    # deco
    if dc is not None:
        lines = open(os.path.join(d, "deco.txt"), encoding="utf-8").read().split("\n")
        decos = []
        for ln in lines:
            p = ln.split()
            if len(p) >= 7:
                decos.append((p[0], int(p[1]), int(p[2]), int(p[3]), int(p[4]), p[5], float(p[6])))
        by_place = {}
        for dd in decos:
            by_place.setdefault(dd[5], []).append(dd)

        def pick(place):
            lst = by_place.get(place)
            if not lst:
                return None
            w = np.array([q[6] for q in lst])
            return lst[rng.choice(len(lst), p=w / w.sum())]

        used = set()
        for y in range(H):
            for x in range(W):
                if mp[y][x] != ".":
                    continue
                below, above = cell(mp, x, y + 1), cell(mp, x, y - 1)
                r = rng.random()
                dd = None
                if below in "#%" and r < 0.35:
                    dd = pick("floor")
                    if dd:
                        px_, py_ = x * T + T // 2 - dd[3] // 2, (y + 1) * T - dd[4]
                elif above in "#%" and r < 0.3:
                    dd = pick("ceiling")
                    if dd:
                        px_, py_ = x * T + T // 2 - dd[3] // 2, y * T
                elif r < 0.07:
                    dd = pick("wall")
                    if dd:
                        px_, py_ = x * T + T // 2 - dd[3] // 2, y * T + T // 2 - dd[4] // 2
                if dd and (x, y) not in used:
                    used.add((x, y))
                    img.alpha_composite(dc.crop((dd[1], dd[2], dd[1] + dd[3], dd[2] + dd[4])), (px_, py_))
        for y in range(H):
            for x in range(W):
                c = mp[y][x]
                if c != "#" or cell(mp, x, y - 1) in SOLID:
                    continue
                for side in (-1, 1):
                    if cell(mp, x + side, y) in ". " and rng.random() < 0.3:
                        dd = pick("edge")
                        if dd:
                            ex = x * T + (T if side > 0 else 0) - dd[3] // 2
                            img.alpha_composite(dc.crop((dd[1], dd[2], dd[1] + dd[3], dd[2] + dd[4])), (ex, y * T))
    # liquid
    if lq is not None:
        for y in range(H):
            for x in range(W):
                if mp[y][x] == "~":
                    row = 1 if cell(mp, x, y - 1) == "~" else 0
                    img.alpha_composite(lq.crop((frame * T, row * T, frame * T + T, row * T + T)), (x * T, y * T))
    # terrain, blocks, platforms
    for y in range(H):
        for x in range(W):
            c = mp[y][x]
            v = vhash(x, y)
            src = None
            if c in "#X" and ta is not None:
                src = tile_of(ta, v * 256 + mask_of(mp, x, y, solid))
            elif c == "%" and tb is not None:
                src = tile_of(tb, v * 256 + mask_of(mp, x, y, solid))
            elif c == "-" and pl is not None:
                lft, rgt = cell(mp, x - 1, y) == "-", cell(mp, x + 1, y) == "-"
                col = 0 if not lft and not rgt else 1 if not lft else 3 if not rgt else 2
                src = tile_of(pl, v * 4 + col, 4)
            elif bl is not None and c in "B_dDAZc^v<>":
                rc = {"B": (0, v), "_": (1, 0), "d": (2, 0), "D": (3, 0), "A": (4, frame), "Z": (5, frame),
                      "c": (6, frame), "^": (7, 0), "v": (7, 1), "<": (7, 2), ">": (7, 3)}[c]
                src = tile_of(bl, rc[0] * 4 + rc[1], 4)
            if src is not None:
                img.alpha_composite(src, (x * T, y * T))
    return img


def sheet_strip(theme):
    d = os.path.join(ROOT, "assets", "tiles", theme)
    parts = []
    for n in ("blocks", "liquid", "platform"):
        im = load(os.path.join(d, n + ".png"))
        if im is not None:
            parts.append(im.resize((im.width * 2, im.height * 2), Image.NEAREST))
    dc = load(os.path.join(d, "deco.png"))
    if dc is not None:
        parts.append(dc.resize((dc.width * 2, dc.height * 2), Image.NEAREST))
    if not parts:
        return None
    w = sum(p.width for p in parts) + 16 * len(parts)
    h = max(p.height for p in parts)
    out = Image.new("RGBA", (w, h), (40, 40, 46, 255))
    x = 0
    for p in parts:
        bgc = Image.new("RGBA", p.size, (70, 70, 80, 255))
        bgc.alpha_composite(p)
        out.alpha_composite(bgc, (x, 0))
        x += p.width + 16
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("theme")
    ap.add_argument("--frame", type=int, default=0)
    ap.add_argument("--crop", type=int, nargs=5, metavar=("X", "Y", "W", "H", "SCALE"))
    a = ap.parse_args()
    img = render(a.theme, a.frame)
    out = os.path.join(ROOT, "work", "tiles")
    os.makedirs(out, exist_ok=True)
    if a.crop:
        x, y, w, h, s = a.crop
        c = img.crop((x, y, x + w, y + h)).resize((w * s, h * s), Image.NEAREST)
        c.save(os.path.join(out, "%s_crop.png" % a.theme))
        return
    view = img.crop((0, 0, 640, 360)).resize((1280, 720), Image.NEAREST)
    strip = sheet_strip(a.theme)
    W = max(img.width, view.width, strip.width if strip else 0)
    Hh = img.height + 8 + view.height + (8 + strip.height if strip else 0)
    full = Image.new("RGBA", (W, Hh), (24, 24, 30, 255))
    full.alpha_composite(img, (0, 0))
    full.alpha_composite(view, (0, img.height + 8))
    if strip:
        full.alpha_composite(strip, (0, img.height + 16 + view.height))
    full.save(os.path.join(out, "%s_preview.png" % a.theme))
    img.save(os.path.join(out, "%s_map1x.png" % a.theme))
    print("wrote", os.path.join(out, "%s_preview.png" % a.theme))


if __name__ == "__main__":
    main()
