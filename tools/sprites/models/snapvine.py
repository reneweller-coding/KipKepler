"""snapvine -- episode 2 dropper (box 24 x 30): a flytrap pod hanging from the ceiling on a vine stalk.

64 x 64 frames, anchor (32, 60) = bottom centre of the box; the box top (30 px up) touches the ceiling. The jaws
open downwards (front and back halves hinged at the stalk).
idle = hanging (swaying, jaws twitching, lure glowing; also shown for 0.7 s on the ground after a drop);
attack = falling with the jaws wide, snapping, a torn stalk end whipping above;
move = climbing back: a taut vine runs from the pod up to the frame top (it pulls itself up);
hurt = recoil.
"""
import math

from bake import Box, Capsule, Cone, Ellipsoid, Intersect, Paint, Part, RoundCone, Sphere, Union, material
from models._e12_common import A64, S64, anim_jobs, line, make_sheet, put, shoot, to_px

YAW = -20.0
POD_TOP = 20.0          # the hinge where the stalk meets the pod
BOX_TOP = 29.0

material("snv_pod", ["purple:1", "crimson:2", "crimson:3", "red:3", "red:4", "rose:5"],
         bands=[-0.55, -0.25, 0.1, 0.45, 0.8], line="purple:0", line_lit="purple:0")
material("snv_inner", ["crimson:2", "magenta:3", "rose:4", "rose:5"], bands=[-0.3, 0.2, 0.65], line="purple:0")
material("snv_vein", ["purple:1", "purple:2", "crimson:2"], bands=[0.0, 0.6])
material("snv_tooth", ["tan:5", "tan:7", "white"], bands=[0.0, 0.5], prio=2.0, line="purple:0")
material("snv_stalk", ["green:1", "green:2", "olive:3", "olive:4", "olive:5"], bands=[-0.45, -0.1, 0.3, 0.72],
         line="green:0", line_lit="green:0")
material("snv_leaf", ["green:1", "teal:2", "teal:3", "teal:4", "teal:5"], bands=[-0.45, -0.1, 0.3, 0.72],
         line="green:0", line_lit="green:0")
material("snv_lure", ["orange:4", "yellow:6", "yellow:7"], style="emit", bands=[0.4, 0.8], prio=3.0)
material("snv_lure_dim", ["orange:3", "orange:4", "yellow:5"], style="emit", bands=[0.4, 0.8], prio=3.0)
material("snv_spot", ["lime:4", "lime:6", "lime:7"], style="emit", bands=[0.4, 0.8], prio=2.5)

POD_R = (8.4, 9.0, 7.2)


SPLIT = -1.6            # pod local: the mouth plane (y)


def pod(open_deg, lure):
    """Pod in local coordinates (centre 0, hung from its top at y = POD_R[1] - 1.4): the upper head and the lower
    jaw hinged at the back; the mouth line runs across the whole pod so both rows of teeth read from the side."""
    rx, ry, rz = POD_R
    ell = Ellipsoid(rx, ry, rz)
    upper = Intersect(ell, Box(rx + 1, ry, rz + 1).at(0, SPLIT + ry, 0)).m("snv_pod")
    lower = Intersect(ell, Box(rx + 1, ry, rz + 1).at(0, SPLIT - ry, 0)).m("snv_pod")
    upper = Paint(upper, Box(rx + 1, 0.7, rz + 1).at(0, SPLIT + 0.2, 0), "snv_inner")
    lower = Paint(lower, Box(rx + 1, 0.7, rz + 1).at(0, SPLIT - 0.2, 0), "snv_inner")
    # the rim ellipse at the split height
    k = math.sqrt(max(0.0, 1 - (SPLIT / ry) ** 2))
    rrx, rrz = rx * k, rz * k
    tu, tl = [], []
    for j in range(9):
        t = math.radians(8 + 164 * j / 8)
        x, z = rrx * math.cos(t) * 0.96, rrz * math.sin(t) * 0.96
        tu.append(Cone(0.8, 0.08, 1.3).m("snv_tooth").rot(180, 0, 0).at(x, SPLIT - 1.0, z))
        t2 = math.radians(8 + 164 * (j + 0.5) / 8)
        if j < 8:
            x2, z2 = rrx * math.cos(t2) * 0.96, rrz * math.sin(t2) * 0.96
            tl.append(Cone(0.75, 0.08, 1.2).m("snv_tooth").at(x2, SPLIT + 0.9, z2))
    spots = [Sphere(1.1).m("snv_spot").at(x, y, z) for x, y, z in ((-3.4, 3.4, 6.0), (2.0, 5.6, 5.4), (-0.6, -5.2, 6.0))]
    hx = -rx * 0.86
    jaw = Union(lower, *tl, spots[2]).at(-hx, -SPLIT, 0).rot(0, 0, -open_deg).at(hx, SPLIT, 0)
    throat = Ellipsoid(rx * 0.8, 2.0, rz * 0.8).m("snv_inner").at(-0.6, SPLIT - 0.6, 0)
    lure_s = Sphere(1.3).m(lure).at(2.0, SPLIT - 1.2, 0)
    head = Union(upper, *tu, spots[0], spots[1], throat, lure_s)
    knob = Sphere(2.4).m("snv_stalk").at(0, ry - 1.0, 0)
    off = -(ry - 1.4)
    return [Union(head, knob).rot(0, 0, -16).at(0, off, 0), jaw.rot(0, 0, -16).at(0, off, 0)]


def stalk(top_y, sway, whip=0.0, leaves=True):
    """From the pod hinge (0, POD_TOP) up to (x, top_y); bends with sway."""
    pts = [(0.0, POD_TOP), (sway * 0.5 + whip, POD_TOP + (top_y - POD_TOP) * 0.45),
           (sway * 0.15 - whip * 0.5, POD_TOP + (top_y - POD_TOP) * 0.8), (0.0, top_y)]
    segs = [RoundCone((a[0], a[1], 0), (b[0], b[1], 0), 1.5, 1.3) for a, b in zip(pts, pts[1:])]
    out = segs
    if leaves:
        mid = pts[1]
        for s, ang in ((1, 35), (-1, -40)):
            leaf = Ellipsoid(3.4, 0.8, 1.8).m("snv_leaf").rot(0, 0, ang + sway * 3).at(mid[0] + s * 3.0,
                                                                                        mid[1] + 1.4, s * 0.8)
            out.append(leaf)
    return Union(*out).m("snv_stalk")


def roots():
    """The knot where the stalk grips the ceiling (above the box top)."""
    knot = Ellipsoid(3.6, 1.8, 3.0).m("snv_stalk").at(0, BOX_TOP + 1.2, 0)
    tendrils = [Capsule((0, BOX_TOP + 1.6, 0), (x, BOX_TOP + 3.4, z), 0.55).m("snv_stalk")
                for x, z in ((-5.0, 1.0), (4.6, -0.6), (2.4, 2.4), (-2.6, -2.2))]
    return Union(knot, *tendrils)


def parts(open_deg=6.0, sway=0.0, swing=0.0, lure="snv_lure", mode="hang", drop=0.0, whip=0.0):
    def place(s):
        s = s.at(0, -BOX_TOP, 0).rot(0, 0, swing).at(0, BOX_TOP, 0) if swing else s
        return s.rot(0, YAW, 0)
    head, jaw = pod(open_deg, lure)
    out = [Part(place(head.at(0, POD_TOP + drop, 0)), name="head"), Part(place(jaw.at(0, POD_TOP + drop, 0)),
                                                                         name="jaw")]
    if mode == "hang":
        out.append(Part(place(stalk(BOX_TOP + 1.0, sway)), name="stalk"))
        out.append(Part(place(roots()), name="roots"))
    elif mode == "fall":
        out.append(Part(place(stalk(POD_TOP + drop + 9.0, sway, whip, leaves=True).at(0, drop, 0)), name="stalk"))
    return out


ANIMS = [
    ("idle", 6, "loop", 8, "hanging: sways, jaws twitch, the lure glows"),
    ("attack", 12, "loop", 6, "falling: jaws wide and snapping, torn stalk whipping"),
    ("move", 10, "loop", 6, "climbing back up a taut vine (drawn to the frame top)"),
    ("hurt", 14, "loop", 3, "recoils"),
]


def frame(job):
    name, i = job
    if name == "idle":
        ph = 2 * math.pi * i / 8
        op = 6 + 6 * max(0.0, math.sin(2 * ph))
        return shoot(parts(open_deg=op, sway=1.6 * math.sin(ph), swing=3.0 * math.sin(ph),
                           lure="snv_lure" if i % 4 < 2 else "snv_lure_dim"))
    if name == "attack":
        op = [34, 44, 8, 40, 46, 14][i]
        return shoot(parts(open_deg=op, sway=0, mode="fall", whip=[2.5, -2.0, 1.5, -2.5, 2.0, -1.0][i],
                           drop=[0.0, -0.5, 0.0, -0.4, 0.0, -0.3][i]))
    if name == "move":
        ph = 2 * math.pi * i / 6
        spr = shoot(parts(open_deg=2.0, mode="climb", swing=4.0 * math.sin(ph), drop=0.6 * math.sin(2 * ph),
                          lure="snv_lure_dim"))
        x0, y0 = to_px(0.0, POD_TOP + 2.0 + 0.6 * math.sin(2 * ph))
        wob = int(round(1.2 * math.sin(ph)))
        line(spr, x0, y0, x0 + wob, 0, "olive:4", glow=False)
        line(spr, x0 + 1, y0, x0 + 1 + wob, 0, "green:2", glow=False)
        for y in range(y0 - 4, 2, -7):
            put(spr, x0 + wob + (1 if (y // 7) % 2 else -1) * 2, y, "teal:4", glow=False)
            put(spr, x0 + wob + (1 if (y // 7) % 2 else -1) * 1, y, "teal:3", glow=False)
        return spr
    return shoot(parts(open_deg=[26, 18, 10][i], sway=2.0, swing=[10, 7, 3][i], lure="snv_lure_dim"))


def jobs():
    return anim_jobs(ANIMS)


def sheets(frames):
    return make_sheet("snapvine", S64, A64, "snapvine flytrap pod (episode 2 dropper, box 24 x 30, faces right)", ANIMS,
                      frames, notes=["anchor = bottom centre of the box; the box top (30 px up) touches the ceiling",
                                     "idle: the stalk ends in a root knot just above the box top (on the ceiling)",
                                     "move: a taut vine runs to the frame top; the engine may draw a vine line "
                                     "from the home point down to the sprite while it is away from home",
                                     "glow: amber lure inside the jaws, lime spots on the pod"])
