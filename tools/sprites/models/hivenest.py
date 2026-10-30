"""hivenest -- episode 2 spawner (box 48 x 48): a living hive mound with glowing openings that releases mothlings.

96 x 96 frames, anchor (48, 92) = bottom centre of the box. Layered mud-and-wax mound, amber light inside the
openings, violet veins, lime spots, roots gripping the ground.
idle = pulsing (breathing squash, openings throb, motes drift out); attack = the openings flare and the crown
bursts (releasing a mothling); hurt = shudders, the glow dims.
"""
import math

from bake import Lathe, Part, RoundCone, Sphere, Subtract, Torus, Union, material
from models._e12_common import A96, R96, S96, anim_jobs, blob, make_sheet, put, shoot, to_px

YAW = -15.0

material("hve_mud", ["brown:1", "brown:2", "brown:3", "tan:3", "tan:4", "tan:5", "tan:6"],
         bands=[-0.6, -0.35, -0.1, 0.2, 0.5, 0.82], line="brown:0", line_lit="brown:0")
material("hve_ridge", ["brown:2", "brown:3", "tan:4", "tan:5", "tan:6", "tan:7"], bands=[-0.5, -0.2, 0.15, 0.5, 0.82],
         line="brown:0", line_lit="brown:0")
material("hve_vein", ["violet:1", "purple:2", "purple:3"], bands=[-0.1, 0.5], line="brown:0")
material("hve_glow", ["orange:2", "orange:3", "orange:4", "yellow:5"], style="emit", bands=[0.2, 0.5, 0.8], prio=2.0,
         line="brown:1", line_lit="brown:1")
material("hve_glow_hi", ["orange:3", "orange:4", "yellow:5", "yellow:6"], style="emit", bands=[0.2, 0.5, 0.8], prio=2.0,
         line="brown:1", line_lit="brown:1")
material("hve_glow_flare", ["yellow:6", "yellow:7", "white"], style="emit", bands=[0.3, 0.7], prio=2.0,
         line="orange:2", line_lit="orange:2")
material("hve_glow_dim", ["brown:2", "orange:2", "orange:3"], style="emit", bands=[0.3, 0.7], prio=2.0,
         line="brown:1", line_lit="brown:1")
material("hve_lip", ["brown:1", "brown:2", "brown:3", "tan:4"], bands=[-0.3, 0.2, 0.6], line="brown:0")
material("hve_spot", ["lime:4", "lime:6", "lime:7"], style="emit", bands=[0.4, 0.8], prio=2.5)
material("hve_root", ["brown:1", "brown:2", "brown:3", "tan:4"], bands=[-0.3, 0.2, 0.65], line="brown:0")

PROFILE = [(23.0, 0.0), (23.4, 3.0), (22.4, 8.0), (20.6, 14.0), (18.6, 20.0), (16.0, 27.0), (13.0, 33.0),
           (9.6, 39.0), (6.4, 43.4), (3.4, 46.4), (0.5, 47.4)]
RIDGES = [(22.6, 7.0, 1.6), (19.6, 16.6, 1.5), (16.4, 25.6, 1.4), (12.6, 33.6, 1.3), (8.2, 40.6, 1.1)]


def radius_at(y):
    for (r0, y0), (r1, y1) in zip(PROFILE, PROFILE[1:]):
        if y0 <= y <= y1:
            return r0 + (r1 - r0) * (y - y0) / (y1 - y0)
    return 0.5


# openings: (angle around y from +z towards +x in degrees, height, radius)
HOLES = [(-26.0, 11.0, 4.2), (38.0, 12.0, 3.6), (4.0, 21.6, 4.0), (-46.0, 27.0, 3.2), (40.0, 30.4, 3.0),
         (-6.0, 38.6, 2.8)]


def mound(glows):
    body = Lathe(PROFILE).m("hve_mud")
    rid = [Torus(r, t).m("hve_ridge").at(0, y, 0) for r, y, t in RIDGES]
    shape = Union(body, *rid)
    lips, cuts = [], []
    for k, (a, y, r) in enumerate(HOLES):
        R = radius_at(y) + 0.6
        ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
        cx, cz = R * sa, R * ca
        cuts.append(Sphere(r).at(cx * 0.97, y, cz * 0.97).m(glows[k % len(glows)]))
        lips.append(Torus(r + 0.7, 0.65).m("hve_lip").rot(90, 0, 0).rot(0, a, 0).at(cx * 0.985, y, cz * 0.985))
    for c in cuts:
        shape = Subtract(shape, c)
    spots = []
    for (a, y) in ((12.0, 15.0), (-40.0, 19.0), (60.0, 21.0), (-18.0, 31.0), (24.0, 42.0), (-70.0, 9.0)):
        R = radius_at(y)
        spots.append(Sphere(0.95).m("hve_spot").at(R * math.sin(math.radians(a)), y, R * math.cos(math.radians(a))))
    crown = Union(*[RoundCone((0, 45.0, 0), (3.0 * math.cos(math.radians(t)), 50.0, 3.0 * math.sin(math.radians(t))),
                              1.4, 0.6).m("hve_ridge") for t in (20, 140, 260)])
    return Union(shape, *lips, *spots, crown)


def roots():
    out = []
    for k, a in enumerate((-160, -110, -60, -20, 20, 60, 110, 160)):
        ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
        p0 = (21.0 * sa, 3.0, 21.0 * ca)
        p1 = (27.0 * sa, 0.9, 27.0 * ca)
        out.append(RoundCone(p0, p1, 2.0, 0.8))
    return Union(*out).m("hve_root")


def crown_px():
    return to_px(0.0, 50.0, R96)


def hole_px(k):
    a, y, r = HOLES[k]
    R = radius_at(y)
    x = R * math.sin(math.radians(a))
    z = R * math.cos(math.radians(a))
    ya = math.radians(YAW)
    return to_px(x * math.cos(ya) + z * math.sin(ya), y, R96)


def parts(glows, sq=0.0):
    return [Part(mound(glows).rot(0, YAW, 0), name="mound"), Part(roots().rot(0, YAW, 0), name="roots")]


ANIMS = [
    ("idle", 8, "loop", 8, "breathing: the mound swells, openings throb in turn, glowing motes drift out"),
    ("attack", 12, "loop", 8, "release: openings flare (0-3), the crown bursts (3-6), settles (7)"),
    ("hurt", 14, "loop", 3, "shudders, glow dims"),
]

GL = ["hve_glow", "hve_glow_hi"]


def frame(job):
    name, i = job
    if name == "idle":
        ph = 2 * math.pi * i / 8
        s = 0.02 * math.sin(ph)
        glows = [GL[(k + i // 2) % 2] for k in range(len(HOLES))]
        spr = shoot(parts(glows), size=S96, ranchor=R96, squash=(1 + s, 1 - s * 1.2))
        for k, (hk, d) in enumerate(((0, i), (2, (i + 3) % 8), (4, (i + 6) % 8))):
            x, y = hole_px(hk)
            put(spr, x + (1 if k % 2 else -1) * (d // 3), y - 2 - d, "yellow:6" if d < 5 else "orange:4")
        return spr
    if name == "attack":
        glows = ["hve_glow_flare" if i in (2, 3, 4, 5) else "hve_glow_hi"] * len(HOLES)
        sq = [0.02, 0.035, 0.05, -0.03, -0.02, 0.0, 0.01, 0.0][i]
        spr = shoot(parts(glows), size=S96, ranchor=R96, squash=(1 + sq, 1 - sq * 1.4))
        cx, cy = crown_px()
        if 3 <= i <= 6:
            k = i - 3
            for j in range(6):
                a = math.radians(60 * j + 30 * k)
                d = 4 + 4 * k
                x, y = int(cx + d * math.cos(a)), int(cy - 2 - d * 0.7 * abs(math.sin(a)) - 2 * k)
                blob(spr, x, y, 1.6 - 0.3 * k, "yellow:6" if j % 2 else "orange:4", glow=True)
            if k < 2:
                blob(spr, cx, cy - 3, 3.0 - k, "yellow:7", glow=True)
                blob(spr, cx, cy - 3, 1.6 - 0.5 * k, "white", glow=True)
        return spr
    glows = ["hve_glow_dim"] * len(HOLES)
    sq = [0.05, -0.03, 0.015][i]
    spr = shoot(parts(glows), size=S96, ranchor=R96, squash=(1 + sq, 1 - sq * 1.3))
    for k in range(3):
        x, y = hole_px(k * 2)
        put(spr, x, y + 3 + i, "orange:4")
    return spr


def jobs():
    return anim_jobs(ANIMS)


def sheets(frames):
    return make_sheet("hivenest", S96, A96, "hive nest (episode 2 spawner of mothlings, box 48 x 48)", ANIMS, frames,
                      notes=["anchor = bottom centre of the box (the mound and its roots on the ground line)",
                             "glow: amber openings, lime spots, motes and the crown burst"])
