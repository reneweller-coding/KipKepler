"""Dialogue portraits for the radio messages: assets/ui/portrait_<name>.png, portrait_<name>_talk.png and
portrait_<name>_glow.png (96 x 96, binary alpha, palette colours only, busts facing right).

The forms (head, hair, helmet, shoulders, uniform) are baked like the sprites (bake.py: SDF shapes, cel shading,
majority filter, outline); the face is then drawn by hand on top, per pixel, at points projected from the 3D head
so it sits on the turned head: eyes, brows, mouth, lines. The _talk frame changes the mouth (and Kip's visor glint);
the _glow mask holds what shines (the Commodore's lighthouse badge lamp, Kip's chest light and antenna light).

    python tools/sprites/portraits.py            # writes assets/ui/portrait_*.png and work/sprites/portraits.png
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from bake import (MATS, PAL, Box, Capsule, Cylinder, Ellipsoid, Extrude, Part, RoundCone,  # noqa: E402
                  SmoothUnion, Sphere, Subtract, Torus, Union, apply, col, material, pixelize, render, rot,
                  scaling, trans)

ROOT = HERE.parents[1]
UI = ROOT / "assets" / "ui"
WORK = ROOT / "work" / "sprites"
SIZE = (96, 96)
ANCHOR = (48, 96)        # world origin at the bottom centre, y up
SS = 4

# ---------------------------------------------------------------------------------------------------------- materials
material("pt_skin", ["skin:3", "skin:4", "skin:5", "skin:6", "rose:7"], bands=[-0.6, -0.28, 0.5, 0.88],
         line="skin:1", line_lit="skin:2")
material("pt_hair", ["slate:2", "slate:3", "steel:4", "steel:5", "steel:6"], bands=[-0.45, -0.1, 0.3, 0.7],
         line="slate:1", line_lit="slate:2")
material("pt_skin_neck", ["skin:3", "skin:4", "skin:5"], bands=[-0.2, 0.5], line="skin:1", line_lit="skin:2")
material("pt_navy", ["blue:1", "slate:2", "blue:2", "blue:3"], bands=[-0.25, 0.3, 0.86], line="outline")
material("pt_navy_dark", ["outline", "blue:1", "slate:2"], bands=[-0.2, 0.4], line="outline")
material("pt_gold", ["brown:2", "orange:3", "yellow:3", "yellow:4", "yellow:5", "white"], style="metal",
         bands=[-0.45, -0.05, 0.35, 0.72], spec=0.9, line="brown:1", line_lit="brown:1")
material("pt_shirt", ["slate:4", "slate:5", "steel:6", "steel:7"], bands=[-0.4, 0.05, 0.6], line="slate:2")
material("pt_k_white", ["slate:4", "slate:5", "steel:6", "steel:7", "white"], bands=[-0.5, -0.1, 0.45, 0.86],
         line_lit="slate:2")
material("pt_k_orange", ["orange:2", "orange:3", "orange:4", "orange:5"], bands=[-0.42, 0.02, 0.8],
         line_lit="orange:1")
material("pt_k_dark", ["slate:1", "slate:2", "slate:3", "slate:4"], bands=[-0.4, 0.1, 0.75])
material("pt_k_visor", ["blue:2", "cyan:2", "cyan:3", "cyan:4", "cyan:5", "white"], style="glass",
         bands=[-0.45, -0.05, 0.45, 0.8], spec=0.95, line="outline")
material("pt_k_inner", ["outline", "slate:1", "blue:1"], bands=[-0.2, 0.4], line="outline")
material("pt_k_light", ["red:4", "orange:5"], style="emit", bands=[0.6], prio=3.0)
material("pt_k_chest", ["cyan:5", "cyan:6"], style="emit", bands=[0.6], prio=3.0)


class Pix:
    """Per-pixel drawing on a Sprite (frame pixel coordinates, y down), with a world -> pixel projection."""

    def __init__(self, spr):
        self.s = spr

    @staticmethod
    def px(p):
        x, y = p[0], p[1]
        return int(round(ANCHOR[0] + x - 0.5)), int(round(ANCHOR[1] - y - 0.5))

    def put(self, x, y, c, glow=False):
        self.s.put(int(x), int(y), c, glow)

    def rows(self, x0, y0, rows, cmap, glow=()):
        """Hand pixels: rows of characters, cmap char -> colour ('.' and ' ' leave the pixel)."""
        for j, r in enumerate(rows):
            for i, ch in enumerate(r):
                if ch in cmap:
                    self.put(x0 + i, y0 + j, cmap[ch], ch in glow)


def project(M, p):
    """World position of a point given in a part's local frame (M = the part's transform)."""
    return apply(M, np.array([p], float))[0]


# ---------------------------------------------------------------------------------------------------------- Commodore

C_BODY_YAW = -38.0
C_HEAD_YAW = -50.0
C_HEAD = (1.0, 60.0, 0.0)          # head centre (world, before the body yaw)
C_HS = 1.4                         # head scale (the head is modelled about 22 units tall)
C_FRONT = 13.0                     # jacket front (torso x) at the chest


def commodore_head_M():
    return (trans(*project(rot(0, C_BODY_YAW, 0), np.array(C_HEAD))) @ rot(0, C_HEAD_YAW, 0) @ rot(0, 0, 5)
            @ scaling(C_HS))


def commodore_parts():
    B = rot(0, C_BODY_YAW, 0)
    jacket = Union(Box(C_FRONT, 22.0, 29.0, r=11.0).at(-1.0, 14.0, 0),
                   Sphere(12.0).at(-2.0, 27.0, 26.0), Sphere(12.0).at(-2.0, 27.0, -26.0)).m("pt_navy")
    collar = Subtract(Cylinder(8.6, 3.6, rr=1.4), Cylinder(6.4, 6.0)).m("pt_navy").at(1.0, 39.5, 0)
    trim = Torus(8.4, 1.0).m("pt_gold").at(1.0, 42.8, 0)
    neck = Capsule((0.8, 36.0, 0), (1.2, 52.0, 0), 5.4).m("pt_skin_neck")
    epaul = []
    for z in (1, -1):
        epaul.append(Box(8.0, 1.8, 8.0, r=1.5).m("pt_gold").rot(z * 12, 0, 0).at(-2.0, 38.2, z * 25.0))
        for k in range(6):
            epaul.append(Capsule((-8.0 + k * 3.0, 36.6, z * 32.6), (-8.0 + k * 3.0, 31.0, z * 33.6), 0.85)
                         .m("pt_gold"))
    torso = Union(jacket, collar, trim, *epaul).xform(B)
    skull = SmoothUnion(Ellipsoid(9.6, 11.0, 8.8).at(-1.2, 3.2, 0),
                        Ellipsoid(7.4, 8.2, 7.0).at(2.2, -3.6, 0),
                        Ellipsoid(2.8, 2.4, 3.0).at(6.0, -10.4, 0), k=3.4).m("pt_skin")
    nose = Union(RoundCone((7.8, 2.8, 0), (11.1, -2.2, 0), 0.9, 1.45),
                 Sphere(1.15).at(10.2, -2.9, 1.3), Sphere(1.15).at(10.2, -2.9, -1.3)).m("pt_skin")
    lips = Ellipsoid(1.2, 1.0, 2.6).at(8.0, -6.4, 0).m("pt_skin")
    ears = [Ellipsoid(1.5, 3.0, 1.1).at(-1.0, -0.4, z * 8.7).m("pt_skin") for z in (1, -1)]
    # short silver hair: swept up and back, volume at the crown, cut above the ears and at the nape
    cap = Ellipsoid(10.8, 11.8, 9.8).at(-1.8, 4.6, 0)
    face_cut = Box(9.0, 8.0, 13.0).rot(0, 0, -22).at(10.4, -0.8, 0)
    side_cut = Box(5.0, 6.0, 13.0).rot(0, 0, 12).at(2.6, -9.4, 0)
    nape_cut = Box(6.0, 5.0, 13.0).rot(0, 0, 28).at(-7.4, -10.6, 0)
    hair = Subtract(Subtract(Subtract(cap, face_cut), side_cut), nape_cut)
    swoop = Ellipsoid(6.6, 3.6, 6.4).rot(0, 0, -14).at(4.6, 10.2, 1.6)
    crown = Ellipsoid(5.0, 3.0, 5.6).rot(0, 0, 18).at(-4.6, 12.6, 0.0)
    fringe = Ellipsoid(3.2, 2.0, 5.4).rot(-24, 0, -30).at(7.0, 8.8, -2.2)
    hair = Union(hair, swoop, crown, fringe).m("pt_hair")
    H = commodore_head_M()
    head = Union(skull, nose, lips, *ears).xform(H)
    return [Part(torso), Part(neck.xform(B), inner=False), Part(head), Part(hair.xform(H), zbias=0.3)]


LIGHTHOUSE = [  # the Beacon Corps badge: g gold, d dark gold, l the lamp (glows), r red band
    "..l..",
    ".gwg.",
    "..g..",
    ".rgr.",
    ".ggd.",
    ".rgd.",
    "gggdd",
]

EYE_NEAR = [   # o lid line, W white, b iris, p pupil, c catchlight, l lower lid, k crease
    "..kkkk..",
    ".oooooo.",
    "oWWbcpo.",
    ".lWbbpl.",
    "..llll..",
]
EYE_FAR = [
    "kkk.",
    "oooo",
    "Wbcp",
    "lbpl",
    ".ll.",
]


def hair_strands(spr):
    """Strands in the silver hair: darker lines swept up and back, a few bright ones on the lit side."""
    hid = MATS["pt_hair"].id
    m = spr.mat == hid
    rng = np.random.default_rng(5)
    ys, xs = np.nonzero(m)
    order = rng.permutation(len(xs))
    used = np.zeros_like(m)
    dark = {col("steel:4"): "slate:3", col("steel:5"): "steel:4", col("steel:6"): "steel:5"}
    for k in order[: len(xs) // 9]:
        x, y = int(xs[k]), int(ys[k])
        if used[max(0, y - 2):y + 3, max(0, x - 2):x + 3].any():
            continue
        bright = spr.col[y, x] == col("steel:6") and rng.random() < 0.35
        # a dash of 3-4 px swept up and back (towards the upper left), slightly curved
        n = int(rng.integers(3, 5))
        for j in range(n):
            xx, yy = x - j, y - (j + (j > 1)) // 2
            if 0 <= xx < 96 and 0 <= yy < 96 and m[yy, xx]:
                if 0 < yy < 95 and m[yy - 1, xx] and m[yy + 1, xx]:
                    c = int(spr.col[yy, xx])
                    if bright:
                        spr.col[yy, xx] = col("grey:7")
                    elif c in dark:
                        spr.col[yy, xx] = col(dark[c])
                used[yy, xx] = True


def commodore(talk):
    spr = pixelize(render(commodore_parts(), SIZE, ANCHOR, ss=SS), cov=7)
    hair_strands(spr)
    P = Pix(spr)
    H = commodore_head_M()

    def at(p):
        return P.px(project(H, np.array(p, float)))

    eye_cols = {"o": "brown:1", "W": "rose:7", "b": "blue:3", "p": "outline", "c": "white", "l": "skin:4",
                "k": "skin:3"}
    ex, ey = at((7.9, 1.0, 3.8))
    P.rows(ex - 4, ey - 2, EYE_NEAR, eye_cols)
    fx, fy = at((8.6, 1.0, -3.6))
    P.rows(fx - 2, fy - 2, EYE_FAR, eye_cols)
    # a lash flick at the outer corner of the near eye
    P.put(ex - 4, ey - 1, "brown:1")
    # brows: silver, straight, the inner ends a touch lower -- strict
    bx, by = at((8.0, 3.5, 3.8))
    P.rows(bx - 4, by - 2, ["hssss...", ".hhhsss."], {"s": "slate:4", "h": "slate:3"})
    bx2, by2 = at((8.8, 3.5, -3.6))
    P.rows(bx2 - 2, by2 - 2, ["sss.", "hhh."], {"s": "slate:4", "h": "slate:3"})
    # nose: a lit ridge, the shadow on its far side, the tip, a nostril and the shadow beneath
    done = set()
    for k in range(13):
        t = k / 12.0
        x, y = at((8.4 + 2.6 * t, 2.6 - 5.0 * t, 0.0))
        if (x, y) in done:
            continue
        done.add((x, y))
        if t < 0.8:
            P.put(x - 1, y, "skin:6")
        if t > 0.3:
            P.put(x + 1, y, "skin:4")
    cx_, cy_ = at((6.6, -2.8, 4.6))
    P.rows(cx_ - 1, cy_, ["rr"], {"r": "rose:6"})
    tx, ty = at((11.0, -2.4, 0.0))
    P.rows(tx - 2, ty, ["..55", "3344", ".44."], {"5": "skin:5", "4": "skin:4", "3": "skin:3"})
    mx, my = at((8.9, -6.4, 0.6))
    if not talk:   # a kind, firm mouth with the corners turned up a little
        P.rows(mx - 4, my - 1, [
            "k.....k.",
            ".kllll..",
            "..ssss..",
        ], {"k": "skin:4", "l": "rose:3", "s": "rose:4"})
    else:
        P.rows(mx - 4, my - 1, [
            "k.....k.",
            ".kllll..",
            "..dttd..",
            "..dddd..",
            "...ss...",
        ], {"k": "skin:4", "l": "rose:3", "d": "crimson:1", "t": "steel:7", "s": "rose:4"})
    ox, oy = at((-1.0, -3.8, 9.0))
    P.put(ox, oy, "yellow:6")
    P.put(ox, oy + 1, "yellow:4")
    # the jacket front: gold piping down the closing, two rows of buttons
    B = rot(0, C_BODY_YAW, 0)
    for k in range(0, 40):
        y = 36.0 - k
        x, yy = P.px(project(B, np.array((C_FRONT + 0.5, y, 2.0 - 0.06 * k))))
        if 0 <= yy < 96:
            P.put(x, yy, "yellow:4" if k % 9 else "yellow:5")
            P.put(x + 1, yy, "blue:1")
    for y in (28.0, 19.0, 10.0, 1.0):
        for z in (-5.0, 9.0):
            x, yy = P.px(project(B, np.array((C_FRONT, y, z))))
            P.rows(x - 1, yy - 1, ["gy", "dg"], {"g": "yellow:4", "y": "yellow:6", "d": "orange:3"})
    # the badge on the near side of her chest, its lamp glowing
    bx, by = P.px(project(B, np.array((C_FRONT - 1.0, 25.0, 15.0))))
    P.rows(bx - 1, by - 4, ["ooooooo"] + ["o.....o"] * 7 + ["ooooooo"], {"o": "blue:1", ".": "slate:2"})
    P.rows(bx, by - 3, LIGHTHOUSE, {"g": "yellow:5", "d": "orange:3", "r": "red:4", "l": "white", "w": "yellow:6"},
           glow=("l", "w"))
    P.put(bx - 1, by - 3, "yellow:6", glow=True)
    P.put(bx + 5, by - 3, "yellow:6", glow=True)
    # ribbon bars on the far side
    rx, ry = P.px(project(B, np.array((C_FRONT - 0.5, 27.0, -11.0))))
    P.rows(rx - 4, ry, ["rrrcccgg", "rrrcccgg"], {"r": "red:4", "c": "cyan:4", "g": "yellow:5"})
    return spr


# ---------------------------------------------------------------------------------------------------------- Kip

K_YAW = -46.0
K_BODY_YAW = -38.0
K_HEAD = (3.0, 57.0, 0.0)
K_R = 21.0                       # helmet radius
K_S = K_R / 19.0
VISOR = (13.6 * K_S, 10.4 * K_S, 19.0 * K_S, 13.6 * K_S, -1.2 * K_S)   # cut box half extents x, y, z; centre x, y


def kip_head_M():
    return trans(*K_HEAD) @ rot(0, K_YAW, 0) @ rot(0, 0, 7)


def kip_parts():
    R = K_R
    B = rot(0, K_BODY_YAW, 0)
    body = Box(12.0, 21.0, 26.0, r=11.0).m("pt_k_orange").at(0.0, 12.0, 0)
    collar = Torus(9.6, 2.8).m("pt_k_dark").at(1.0, 33.5, 0)
    pads = []
    for z in (1, -1):
        pads.append(Sphere(11.0).m("pt_k_white").at(-1.0, 26.0, z * 25.0))
        pads.append(Torus(9.8, 1.6).rot(90, 0, 0).rot(0, 90, 0).m("pt_k_orange").at(-1.0, 25.0, z * 27.0))
    straps = [Capsule((10.0, 31.0, z * 11.0), (12.6, 4.0, z * 9.0), 1.7).m("pt_k_dark") for z in (1, -1)]
    panel = Box(1.0, 4.4, 6.0, r=0.8).m("pt_k_dark").at(12.2, 17.0, 2.0)
    light = Sphere(1.9).m("pt_k_chest").at(12.6, 18.0, 4.2)
    pack = Box(6.0, 16.0, 15.0, r=4.5).m("pt_k_white").at(-15.0, 20.0, 0)
    torso = Union(body, collar, *pads, *straps, panel, light, pack).xform(B)
    shell = Sphere(R).m("pt_k_white")
    cut = Box(VISOR[0], VISOR[1], VISOR[2], r=7.5).at(VISOR[3], VISOR[4], 0)
    shell = Subtract(shell, cut)
    ear = Cylinder(4.6, 1.7, rr=1.0).m("pt_k_orange").rot(90, 0, 0)
    hub = Cylinder(2.2, 1.0, rr=0.6).m("pt_k_dark").rot(90, 0, 0)
    fin = Extrude([(-18.0, 10.0), (-12.0, 23.0), (-1.0, 25.6), (8.0, 21.6), (12.0, 16.0), (3.0, 18.6)], 1.4,
                  r=0.8).m("pt_k_orange")
    antenna = Union(Capsule((0, 0, 0), (-7.0, 12.0, 0), 0.95).m("pt_k_dark"),
                    Sphere(2.1).m("pt_k_light").at(-7.1, 12.6, 0)).at(-7.5, -0.6, R - 1.4)
    inner = Sphere(R - 2.4).m("pt_k_inner")
    helmet = Union(shell, ear.at(-7.5, -3.6, R - 1.3), ear.at(-7.5, -3.6, -(R - 1.3)),
                   hub.at(-7.5, -3.6, R + 0.6), fin, antenna)
    visor = Sphere(R - 2.0).m("pt_k_visor")
    Hm = kip_head_M()
    return [Part(torso), Part(helmet.xform(Hm)), Part(inner.xform(Hm)), Part(visor.xform(Hm))]


def kip(talk):
    spr = pixelize(render(kip_parts(), SIZE, ANCHOR, ss=SS), cov=7)
    P = Pix(spr)
    Hm = kip_head_M()
    vis = spr.mat == MATS["pt_k_visor"].id
    ys, xs = np.nonzero(vis)
    face = set()

    def F(x, y, c, glow=False):
        if 0 <= y < 96 and 0 <= x < 96 and vis[y, x]:
            spr.put(x, y, c, glow)
            face.add((x, y))

    def at(p):
        return P.px(project(Hm, np.array(p, float)))
    cx, cy = at((14.0, -1.6, 0.6))
    # the face behind the glass: round, lit from the upper left
    for yy in range(cy - 11, cy + 12):
        for xx in range(cx - 13, cx + 12):
            dx, dy = (xx - cx + 1) / 12.0, (yy - cy) / 11.0
            if dx * dx + dy * dy <= 1.0:
                c = "skin:5"
                if dx > 0.55 or dy > 0.62 or (dx * dx + dy * dy > 0.8 and dx > 0):
                    c = "skin:4"
                if dx < -0.2 and dy < -0.1:
                    c = "skin:6"
                F(xx, yy, c)
    # hair: a fringe of brown tufts under the helmet rim
    for k in range(16):
        x = cx - 12 + k
        h = 2 + (k % 3 == 1) + (k % 5 == 0)
        for j in range(h):
            F(x, cy - 11 + j, "brown:3" if j < h - 1 else "brown:2")
    for k in range(0, 14, 3):
        F(cx - 11 + k, cy - 10, "brown:5")
    # eyes: big, bright, looking right; brows up -- cheerful
    eyes = ((cx - 5, 4, "near"), (cx + 4, 3, "far"))
    for ex, w, kind in eyes:
        for dy in range(5):
            for dx in range(w):
                if (dy in (0, 4)) and dx in (0, w - 1):
                    continue
                F(ex + dx, cy - 4 + dy, "blue:1")
        F(ex + w - 2, cy - 3, "white")
        F(ex + w - 1, cy - 3, "white") if w == 4 else None
        F(ex + 1, cy - 1 + 1, "blue:3")
        for dx in range(-1, w):
            F(ex + dx, cy - 7 + (1 if dx < 0 else 0), "brown:2")
    # cheeks and nose
    for x, y, c in ((cx - 9, cy + 2, "rose:5"), (cx - 8, cy + 2, "rose:5"), (cx - 8, cy + 3, "rose:4"),
                    (cx + 8, cy + 2, "rose:4"), (cx + 9, cy + 2, "rose:4"), (cx + 1, cy + 2, "skin:3"),
                    (cx + 2, cy + 2, "skin:3"), (cx + 2, cy + 1, "skin:4")):
        F(x, y, c)
    # mouth: a big grin; talking: open wider
    if not talk:
        rows = ["k........k", ".kddddddk.", "..kttttk..", "...kkkk..."]
        cmap = {"k": "skin:2", "d": "crimson:1", "t": "white"}
    else:
        rows = ["k........k", ".kddddddk.", ".kdttttdk.", "..kdrrdk..", "...kkkk..."]
        cmap = {"k": "skin:2", "d": "crimson:1", "t": "white", "r": "rose:4"}
    for j, r in enumerate(rows):
        for i, ch in enumerate(r):
            if ch in cmap:
                F(cx - 5 + i, cy + 5 + j, cmap[ch])
    # the glass back over the face: a glint band across the upper left, its edge in shadow
    top, left = ys.min(), xs.min()
    g0 = 8 if not talk else 11
    for (x, y) in zip(xs, ys):
        u = (x - left) + (y - top) * 1.2
        if g0 <= u < g0 + 3:
            spr.put(x, y, "cyan:6" if u < g0 + 2 else "cyan:5")
        elif g0 + 5 <= u < g0 + 6:
            spr.put(x, y, "cyan:5")
        elif u < 3:
            spr.put(x, y, "white")
    for (x, y) in zip(xs, ys):
        if (x, y) in face and (not vis[min(95, y + 2), x] or not vis[y, min(95, x + 2)]):
            spr.put(x, y, "cyan:3")
    return spr


# ---------------------------------------------------------------------------------------------------------- output

def save(name, spr_a, spr_b):
    UI.mkdir(parents=True, exist_ok=True)
    Image.fromarray(spr_a.rgba(), "RGBA").save(UI / f"portrait_{name}.png", optimize=True)
    Image.fromarray(spr_b.rgba(), "RGBA").save(UI / f"portrait_{name}_talk.png", optimize=True)
    g = spr_a.glow_rgba()
    gb = spr_b.glow_rgba()
    # one glow mask for both frames (the glowing parts do not move between them)
    m = (g[..., 3] > 0) | (gb[..., 3] > 0)
    out = np.where(m[..., None], np.where(g[..., 3:] > 0, g, gb), 0).astype(np.uint8)
    gp = UI / f"portrait_{name}_glow.png"
    if m.any():
        Image.fromarray(out, "RGBA").save(gp, optimize=True)
    elif gp.exists():
        gp.unlink()


def check(path):
    im = np.asarray(Image.open(path).convert("RGBA"))
    pal = {tuple(int(v) for v in c) for c in PAL}
    al = im[..., 3]
    cols = {tuple(int(v) for v in c) for c in im[al == 255][:, :3]}
    probs = []
    if not np.isin(al, (0, 255)).all():
        probs.append("alpha not binary")
    if cols - pal:
        probs.append(f"{len(cols - pal)} colours outside the palette")
    if im.shape[:2] != (96, 96):
        probs.append(f"size {im.shape[:2]}")
    return probs


def preview(sprites, path):
    """Every portrait on a dark and a light panel at 1x and 4x."""
    tiles = []
    for bg in ((22, 26, 44), (196, 204, 214)):
        row = []
        for s in sprites:
            im = Image.new("RGB", (100, 100), bg)
            a = Image.fromarray(s.rgba(), "RGBA")
            im.paste(a, (2, 2), a)
            row.append(im)
        tiles.append(row)
    W = len(sprites) * 100
    one = Image.new("RGB", (W, 200), (0, 0, 0))
    for j, row in enumerate(tiles):
        for i, im in enumerate(row):
            one.paste(im, (i * 100, j * 100))
    big = one.crop((0, 0, W, 100)).resize((W * 4, 400), Image.NEAREST)
    out = Image.new("RGB", (W * 4, 400 + 200 + 8), (40, 40, 40))
    out.paste(big, (0, 0))
    out.paste(one, (0, 408))
    path.parent.mkdir(parents=True, exist_ok=True)
    out.save(path)
    return path


def main():
    c0, c1 = commodore(False), commodore(True)
    k0, k1 = kip(False), kip(True)
    save("commodore", c0, c1)
    save("kip", k0, k1)
    ok = True
    for p in sorted(UI.glob("portrait_*.png")):
        probs = check(p)
        ok &= not probs
        print(p.name, "ok" if not probs else "PROBLEMS: " + "; ".join(probs))
    print(preview([c0, c1, k0, k1], WORK / "portraits.png"))
    return ok


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
