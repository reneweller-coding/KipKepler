"""mothling -- episode 2 flier (box 26 x 20): a glowing jungle moth with eye-spotted amber wings.

64 x 64 frames, anchor (32, 50) = bottom centre of the box; the body hangs about 9 px above it, the wings sweep up
beyond the box top on the upstroke. Seen a little from above so the wing pattern reads. Spawned by the hivenest.
"""
import math

from bake import Box, Capsule, Ellipsoid, Extrude, Paint, Part, RoundCone, Sphere, Union, material
from models._e12_common import anim_jobs, make_sheet, put, shoot, to_px

SIZE, ANCHOR, RANCHOR = (64, 64), (32, 50), (32, 49)
YAW, PITCH = -12.0, 14.0
SCALE = 1.1
BODY_Y = 8.5

material("mth_wing", ["brown:2", "orange:3", "orange:4", "yellow:4", "yellow:5", "yellow:6"],
         bands=[-0.55, -0.25, 0.1, 0.45, 0.8], line="brown:1", line_lit="brown:1")
material("mth_wing_hind", ["brown:2", "brown:3", "orange:3", "orange:4", "yellow:4"], bands=[-0.5, -0.15, 0.25, 0.7],
         line="brown:1", line_lit="brown:1")
material("mth_edge", ["violet:1", "violet:2", "purple:3", "purple:4"], bands=[-0.3, 0.2, 0.7], line="violet:0")
material("mth_ring", ["teal:3", "teal:4", "cyan:5"], style="emit", bands=[0.3, 0.7], prio=2.0)
material("mth_core", ["cyan:6", "white"], style="emit", bands=[0.5], prio=2.5)
material("mth_ring_dim", ["teal:2", "teal:3", "teal:4"], style="emit", bands=[0.3, 0.7], prio=2.0)
material("mth_body", ["violet:1", "violet:2", "purple:3", "purple:4", "purple:5"], bands=[-0.45, -0.1, 0.3, 0.72],
         line="violet:0", line_lit="violet:0")
material("mth_fur", ["tan:3", "tan:5", "tan:6", "tan:7"], bands=[-0.3, 0.2, 0.65], line="brown:1")
material("mth_eye", ["orange:4", "yellow:6", "white"], style="emit", bands=[0.4, 0.8], prio=3.0)
material("mth_tail", ["teal:4", "cyan:5", "cyan:6", "white"], style="emit", bands=[0.3, 0.6, 0.85], prio=2.0)
material("mth_leg", ["violet:0", "violet:1", "purple:2"], bands=[0.0, 0.6], line="outline")

FORE = [(2.4, 0.0), (4.4, 4.6), (4.2, 10.4), (1.4, 15.2), (-3.0, 16.0), (-5.4, 12.4), (-4.2, 4.6), (-1.4, 0.0)]
HIND = [(-0.8, 0.0), (-2.0, 4.2), (-4.2, 9.4), (-7.8, 10.2), (-9.8, 6.8), (-8.8, 2.2), (-4.6, 0.0)]


def wing(poly, mat, spots, glow=True):
    w = Extrude(poly, 0.35, r=0.12).m(mat)
    w = Paint(w, Union(*[Sphere(2.0).at(x, y, 0) for x, y in poly[2:-2]]), "mth_edge")
    for (x, y, r) in spots:
        w = Paint(w, Sphere(r).at(x, y, 0), "mth_ring" if glow else "mth_ring_dim")
        w = Paint(w, Sphere(r * 0.45).at(x, y, 0), "mth_core")
    return w.rot(90, 0, 0)          # polygon y (span) -> world z


def wings(phi_n, phi_f, glow=True):
    """Near pair hinged along the body axis at z = +1.2, far pair mirrored at z = -1.2; phi > 0 raises a wing."""
    near = Union(wing(FORE, "mth_wing", [(-0.6, 9.8, 2.5)], glow),
                 wing(HIND, "mth_wing_hind", [(-6.0, 6.4, 1.8)], glow)).at(0, 0.6, 1.2).rot(-phi_n, 0, 0)
    fore_m = wing([(x, -y) for x, y in FORE][::-1], "mth_wing", [(-0.6, -9.8, 2.5)], glow)
    hind_m = wing([(x, -y) for x, y in HIND][::-1], "mth_wing_hind", [(-6.0, -6.4, 1.8)], glow)
    far = Union(fore_m, hind_m).at(0, 0.6, -1.2).rot(phi_f, 0, 0)
    return near, far


def body(tail=True):
    thorax = Sphere(2.7).m("mth_fur").at(0.8, 0.4, 0)
    abdomen = Ellipsoid(4.8, 2.4, 2.4).m("mth_body").rot(0, 0, 12).at(-4.0, -0.4, 0)
    abdomen = Paint(abdomen, Union(*[Box(0.45, 3, 3).rot(0, 0, 12).at(x, -0.4 + (x + 4.0) * 0.21, 0)
                                     for x in (-2.6, -4.6, -6.6)]), "mth_fur")
    tip = Sphere(1.5).m("mth_tail" if tail else "mth_body").at(-8.4, -1.4, 0)
    head = Sphere(2.0).m("mth_body").at(3.9, 0.9, 0)
    eyes = Union(Sphere(1.25).m("mth_eye").at(4.8, 1.3, 1.3), Sphere(1.1).m("mth_eye").at(4.9, 1.3, -1.1))
    ants = []
    for z in (1.0, -1.0):
        a, b = (4.6, 2.6, z), (6.4, 6.8, z * 2.6)
        ants.append(Capsule(a, b, 0.3))
        for t in (0.5, 0.85):
            p = tuple(a[k] + (b[k] - a[k]) * t for k in range(3))
            ants.append(Capsule(p, (p[0] + 1.1, p[1] - 0.1, p[2]), 0.25))
    legs = [RoundCone((1.6 + dx, -1.6, z), (2.6 + dx * 1.4, -4.4, z * 1.6), 0.4, 0.25) for dx in (-1.2, 0.2, 1.4)
            for z in (0.8, -0.8)]
    return Union(thorax, abdomen, tip, head, eyes, Union(*ants).m("mth_leg"), Union(*legs).m("mth_leg"))


def parts(phi, bob=0.0, roll=0.0, tilt=0.0, glow=True, tail=True, phi_f=None):
    near, far = wings(phi, phi if phi_f is None else phi_f, glow)

    def place(s):
        return s.rot(roll, 0, tilt).scale(SCALE).rot(0, YAW, 0).rot(PITCH, 0, 0).at(2.0, BODY_Y + bob, 0)
    return [Part(place(body(tail)), name="body"), Part(place(near), name="wing_n"),
            Part(place(far), name="wing_f", shade=-1)]


ANIMS = [
    ("fly", 16, "loop", 8, "flapping; wing eye spots and tail glow"),
    ("hurt", 14, "loop", 3, "tumbles, scales fall"),
]


def frame(job):
    name, i = job
    if name == "fly":
        c = math.cos(2 * math.pi * i / 8)
        phi = 22 + 70 * c
        bob = -1.4 * c
        phi_f = 22 + 70 * math.cos(2 * math.pi * (i - 0.7) / 8)
        spr = shoot(parts(phi, bob=bob, tilt=-6 + 3 * c, glow=i % 4 != 3, tail=i % 4 != 2, phi_f=phi_f), size=SIZE,
                    ranchor=RANCHOR, cov=6)
        return spr
    spr = shoot(parts([-30, 10, 40][i], phi_f=[50, 70, 20][i], bob=-1, roll=[20, -15, 8][i], tilt=[18, 10, 4][i],
                      glow=False, tail=i == 2), size=SIZE, ranchor=RANCHOR, cov=6)
    x, y = to_px(0, BODY_Y, RANCHOR)
    for k, (dx, dy) in enumerate(((-6, 5), (5, 7), (-2, 9), (7, 3), (-8, 1))):
        if (k + i) % 2 == 0:
            put(spr, x + dx, y + dy + 2 * i, "tan:6" if k % 2 else "yellow:5", glow=False)
    return spr


def jobs():
    return anim_jobs(ANIMS)


def sheets(frames):
    return make_sheet("mothling", SIZE, ANCHOR, "mothling (episode 2 flier, box 26 x 20, faces right)", ANIMS, frames,
                      notes=["anchor = bottom centre of the box; wings sweep above the box top on the upstroke",
                             "glow: wing eye spots, amber eyes, tail light"])
