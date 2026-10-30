"""spitter -- episode 2 lobber (box 26 x 34): a carnivorous plant bulb on a stem that lobs acid arcs.

64 x 64 frames, anchor (32, 60). A rosette of leaves on the ground, a curved stem, a violet bulb with glowing spots
and a hinged mouth lined with teeth, lime acid inside. idle sways and drools; attack rears back, swells and spits
(the acid leaves at the muzzle point); hurt recoils.
"""
import math

import numpy as np

from bake import Box, Cone, Ellipsoid, Intersect, Paint, Part, RoundCone, Sphere, Union, material, rot
from models._e12_common import A64, S64, anim_jobs, blob, make_sheet, point_of, put, shoot, to_px

YAW = -22.0

material("spt_bulb", ["purple:1", "purple:2", "magenta:2", "magenta:3", "magenta:4", "magenta:5"],
         bands=[-0.55, -0.25, 0.1, 0.45, 0.82], line="purple:0", line_lit="purple:0")
material("spt_lip", ["crimson:2", "crimson:3", "rose:4", "rose:5"], bands=[-0.3, 0.2, 0.65], line="purple:0")
material("spt_throat", ["purple:0", "purple:1", "crimson:2"], bands=[0.0, 0.6], line="purple:0")
material("spt_tooth", ["tan:5", "tan:7", "white"], bands=[0.0, 0.5], prio=2.0, line="purple:0")
material("spt_acid", ["green:3", "lime:4", "lime:5", "lime:6"], style="emit", bands=[0.3, 0.6, 0.88], prio=2.5,
         line="green:2", line_lit="green:2")
material("spt_spot", ["lime:4", "lime:6", "lime:7"], style="emit", bands=[0.4, 0.8], prio=2.5)
material("spt_spot_dim", ["green:3", "lime:4", "lime:5"], style="emit", bands=[0.4, 0.8], prio=2.5)
material("spt_stem", ["purple:1", "crimson:2", "crimson:3", "rose:4", "rose:5"], bands=[-0.45, -0.1, 0.3, 0.72],
         line="purple:0", line_lit="purple:0")
material("spt_leaf", ["green:1", "teal:2", "teal:3", "teal:4", "teal:5", "teal:6"],
         bands=[-0.5, -0.2, 0.15, 0.5, 0.82], line="green:0", line_lit="green:0")
material("spt_vein", ["green:1", "green:2", "green:2"], bands=[0.0, 0.6])

BULB_R = (8.2, 7.6, 7.2)
HINGE = (-4.6, 0.6)          # bulb local: the jaw hinge at the back


def bulb(open_deg, swell=0.0, spots="spt_spot"):
    """Bulb in local coordinates (centre at 0), mouth facing +x. Returns (upper, lower) shapes."""
    rx, ry, rz = (r * (1 + swell) for r in BULB_R)
    ell = Ellipsoid(rx, ry, rz)
    cut = Box(12, 12, 12)
    upper = Intersect(ell, cut.at(0, 12 + 0.4, 0)).m("spt_bulb")
    lower = Intersect(ell, cut.at(0, -12 + 0.4, 0)).m("spt_bulb")
    lip_u = Intersect(Ellipsoid(rx + 0.2, 1.2, rz + 0.2).at(0, 0.9, 0), Box(6, 2, 12).at(rx - 4.0, 0.9, 0)).m("spt_lip")
    lip_l = Intersect(Ellipsoid(rx + 0.2, 1.2, rz + 0.2).at(0, -0.1, 0), Box(6, 2, 12).at(rx - 4.0, -0.1, 0)).m("spt_lip")
    teeth_u, teeth_l = [], []
    for k, a in enumerate((-48, -24, 0, 24, 48)):
        c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
        x, z = (rx - 0.9) * c, (rz - 0.9) * s
        if x < 1.5:
            continue
        teeth_u.append(Cone(0.75, 0.1, 1.0).m("spt_tooth").rot(180, 0, 0).at(x, -0.4, z))
        teeth_l.append(Cone(0.75, 0.1, 1.0).m("spt_tooth").at(x - 0.4, 1.0, z * 0.95))
    sp_u = [Sphere(0.95).m(spots).at(*p) for p in ((-2.0, 5.6, 4.4), (2.6, 5.2, 4.2), (-4.8, 3.0, 4.8), (0.4, 7.0, 0.8))]
    sp_l = [Sphere(0.9).m(spots).at(*p) for p in ((-1.0, -4.6, 5.0), (3.4, -3.6, 4.6))]
    hx, hy = HINGE
    up = Union(upper, lip_u, *teeth_u, *sp_u).at(-hx, -hy, 0).rot(0, 0, open_deg * 0.7).at(hx, hy, 0)
    lo = Union(lower, lip_l, *teeth_l, *sp_l).at(-hx, -hy, 0).rot(0, 0, -open_deg * 0.3).at(hx, hy, 0)
    throat = Ellipsoid(rx * 0.78, ry * 0.5, rz * 0.7).m("spt_throat").at(-1.2, 0.4, 0)
    acid = Sphere(2.3 + 4.0 * swell).m("spt_acid").at(rx * 0.58, 0.3 + open_deg * 0.035, 0)
    return Union(up, lo, throat, acid)


def leaves(sway):
    out = []
    for k, (ang, ln, tilt) in enumerate(((-160, 12.0, 26), (-20, 12.5, 24), (-90, 9.5, 36), (160, 11.0, 30),
                                         (20, 11.5, 30), (90, 8.0, 40))):
        leaf = Ellipsoid(ln / 2, 1.0, 3.0).m("spt_leaf")
        leaf = Paint(leaf, Box(ln, 0.6, 0.35), "spt_vein")
        a = math.radians(ang)
        t = tilt + sway * (1 if k % 2 else -1)
        out.append(leaf.rot(0, 0, t).at(ln / 2 * 0.9, 0, 0).rot(0, -ang, 0).at(0, 3.4, 0))
    return Union(*out)


def stem_points(bend):
    # base (0, 1), up to the bulb neck, curving back then forward
    return [(0.0, 3.5), (-2.4 + bend * 0.3, 8.0), (-2.2 + bend * 0.7, 13.0), (0.2 + bend, 18.0)]


def stem(bend):
    pts = stem_points(bend)
    segs = [RoundCone((a[0], a[1], 0), (b[0], b[1], 0), r1, r2) for (a, b), (r1, r2) in
            zip(zip(pts, pts[1:]), ((3.0, 2.4), (2.4, 2.1), (2.1, 2.3)))]
    nodes = [Sphere(2.5).at(pts[1][0], pts[1][1], 0)]
    thorn = [RoundCone((pts[2][0] - 1.6, pts[2][1], 0.8), (pts[2][0] - 4.0, pts[2][1] + 1.6, 0.8), 0.6, 0.15)]
    return Union(*segs, *nodes, *thorn).m("spt_stem")


def parts(open_deg=6.0, bend=0.0, tilt=0.0, swell=0.0, sway=0.0, spots="spt_spot", lift=0.0):
    pts = stem_points(bend)
    top = pts[-1]
    b = bulb(open_deg, swell, spots).rot(0, 0, 14 + tilt).at(top[0] + 1.0, top[1] + 6.8 + lift, 0)
    return [Part(b.rot(0, YAW, 0), name="bulb"), Part(stem(bend).rot(0, YAW, 0), name="stem"),
            Part(leaves(sway).rot(0, YAW, 0), name="leaves")]


def mouth_world(open_deg=6.0, bend=0.0, tilt=0.0, swell=0.0, lift=0.0):
    pts = stem_points(bend)
    top = pts[-1]
    rx = BULB_R[0] * (1 + swell)
    M = rot(0, YAW, 0) @ np.array([[1, 0, 0, top[0] + 1.0], [0, 1, 0, top[1] + 6.8 + lift], [0, 0, 1, 0],
                                   [0, 0, 0, 1.0]]) @ rot(0, 0, 14 + tilt)
    p = M @ np.array([rx + 0.6, 0.6, 0, 1.0])
    return p[0], p[1]


ANIMS = [
    ("idle", 8, "loop", 8, "swaying, mouth breathing, acid drool, spots pulse"),
    ("attack", 15, "loop", 6, "rear back and swell (0-2), lunge and spit (3-4), recover (5)"),
    ("hurt", 14, "loop", 3, "recoils"),
]

ATTACK = [  # open, bend, tilt, swell
    (8.0, -1.4, 10, 0.03), (0.0, -2.4, 16, 0.07), (0.0, -2.8, 20, 0.09), (58.0, 2.0, -8, 0.0), (50.0, 2.4, -10, -0.02),
    (26.0, 0.6, -2, 0.0)]


def frame(job):
    name, i = job
    if name == "idle":
        ph = 2 * math.pi * i / 8
        op = 22 + 8 * math.sin(ph)
        bend = 0.9 * math.sin(ph)
        spr = shoot(parts(open_deg=op, bend=bend, tilt=3 * math.sin(ph), sway=4 * math.sin(ph),
                          spots="spt_spot" if i % 4 < 2 else "spt_spot_dim"))
        mx, my = mouth_world(op, bend, 3 * math.sin(ph))
        px, py = to_px(mx - 1.5, my - 1.5)
        k = i % 4
        for d in range(k + 1):
            put(spr, px, py + d, "lime:6" if d < k else "lime:5")
        return spr
    if name == "attack":
        op, bend, tilt, sw = ATTACK[i]
        spr = shoot(parts(open_deg=op, bend=bend, tilt=tilt, swell=sw, sway=-3 if i < 3 else 3))
        if i in (3, 4):
            mx, my = mouth_world(op, bend, tilt, sw)
            px, py = to_px(mx, my)
            r = 2.4 if i == 3 else 1.6
            blob(spr, px + 2, py - 1, r + 0.8, "green:4", glow=True)
            blob(spr, px + 2, py - 1, r, "lime:6", glow=True)
            put(spr, px + 1, py - 2, "lime:7")
            if i == 3:
                for dx, dy in ((5, -4), (6, 1), (4, 3)):
                    put(spr, px + dx, py + dy, "lime:6")
        return spr
    spr = shoot(parts(open_deg=[40, 30, 24][i], bend=[-2.4, -1.8, -0.8][i], tilt=[22, 16, 8][i], sway=-5,
                      spots="spt_spot_dim"))
    return spr


def jobs():
    return anim_jobs(ANIMS)


def sheets(frames):
    op, bend, tilt, sw = ATTACK[3]
    mx, my = mouth_world(op, bend, tilt, sw)
    dx, dy = point_of(mx + 1.0, my)
    return make_sheet("spitter", S64, A64, "spitter plant (episode 2 lobber, box 26 x 34, faces right)", ANIMS, frames,
                      points=[("muzzle", dx, dy, "the mouth in the spit frames (acid)")],
                      notes=["anchor = bottom centre of the box (the leaf rosette on the ground line)",
                             "glow: lime acid in the mouth, lime spots on the bulb"])
