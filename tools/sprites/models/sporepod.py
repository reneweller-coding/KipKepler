"""sporepod -- episode 2 floater (box 22 x 22): a floating spore balloon with dangling tendrils that puffs spores.

64 x 64 frames, anchor (32, 44) = bottom centre of the box; the balloon fills the box, its tendrils hang about
12 px below it. fly = drifting (pulsing, tendrils waving); attack = a puff of spores from the crown vents (the
engine shoots its "spore" shots on its own timer, so attack is optional); hurt = shrivels.
"""
import math

from bake import Box, Cone, Cylinder, Ellipsoid, Paint, Part, RoundCone, Sphere, Union, material
from models._e12_common import anim_jobs, blob, make_sheet, point_of, put, shoot, to_px

SIZE, ANCHOR, RANCHOR = (64, 64), (32, 44), (32, 43)
YAW, PITCH = -20.0, 12.0
CY = 11.6

material("spd_skin", ["brown:2", "tan:3", "tan:4", "tan:5", "tan:6", "tan:7"],
         bands=[-0.55, -0.25, 0.1, 0.45, 0.8], line="brown:1", line_lit="brown:1")
material("spd_rib", ["brown:1", "brown:2", "brown:3", "tan:4"], bands=[-0.3, 0.2, 0.65], line="brown:1")
material("spd_spot", ["purple:2", "violet:3", "violet:4"], bands=[-0.1, 0.5], line="purple:1")
material("spd_sac", ["magenta:4", "magenta:5", "magenta:6", "rose:7"], style="emit", bands=[0.3, 0.6, 0.88], prio=2.5)
material("spd_sac_dim", ["purple:3", "magenta:3", "magenta:4"], style="emit", bands=[0.4, 0.8], prio=2.5)
material("spd_vent", ["purple:1", "purple:2", "violet:3", "violet:4"], bands=[-0.3, 0.2, 0.7], line="purple:0")
material("spd_tendril", ["violet:1", "violet:2", "purple:3", "purple:4"], bands=[-0.3, 0.2, 0.7], line="violet:0")
material("spd_tip", ["teal:4", "cyan:5", "cyan:6"], style="emit", bands=[0.4, 0.8], prio=2.5)

R = (8.8, 8.4, 8.4)


def balloon(pulse, sac, squeeze=0.0):
    rx, ry, rz = R[0] * (1 + pulse - squeeze), R[1] * (1 - pulse * 0.6 - squeeze * 0.6), R[2] * (1 + pulse - squeeze)
    skin = Ellipsoid(rx, ry, rz).m("spd_skin")
    ribs = Union(*[Box(0.45, ry + 1, rz + 2).rot(0, a, 0) for a in range(0, 180, 45)])
    skin = Paint(skin, ribs, "spd_rib")
    spots = Union(*[Sphere(r).at(x, y, z) for x, y, z, r in ((-5.2, 3.6, 5.6, 1.4), (-6.8, -3.4, 4.2, 1.2))])
    skin = Paint(skin, spots, "spd_spot")
    sacs = [Sphere(r).m(sac).at(x, y, z) for x, y, z, r in ((0.8, 2.6, rz - 1.0, 1.75), (-2.6, -3.4, rz - 1.3, 1.6),
                                                          (5.0, -0.6, rz - 3.0, 1.5), (-4.4, 5.0, rz - 3.8, 1.2))]
    crown = []
    for k, (x, z, h) in enumerate(((0.0, 0.0, 2.6), (-3.0, 1.8, 1.8), (2.8, 1.6, 2.0), (-0.6, -2.8, 1.8))):
        y0 = ry * math.sqrt(max(0.0, 1 - (x / rx) ** 2 - (z / rz) ** 2)) - 0.6
        crown.append(Cone(1.5, 0.9, h / 2).m("spd_vent").at(x, y0 + h / 2, z))
        crown.append(Cylinder(0.7, 0.3).m(sac).at(x, y0 + h + 0.05, z))
    return Union(skin, *sacs, *crown)


def tendrils(ph, curl=0.0):
    out = []
    for k, (a, ln) in enumerate(((0, 13.0), (72, 10.5), (144, 12.0), (216, 11.0), (288, 9.5))):
        ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
        base = (4.0 * ca, -R[1] * 0.78, 4.0 * sa)
        pts = [base]
        n = 4
        for j in range(1, n + 1):
            t = j / n
            sway = 1.6 * math.sin(ph + k * 1.3 + j * 0.9) * t + curl * t * t * 3 * ca
            pts.append((base[0] * (1 + 0.25 * t) + sway, base[1] - ln * t, base[2] * (1 + 0.25 * t)))
        for j, (p, q) in enumerate(zip(pts, pts[1:])):
            out.append(RoundCone(p, q, 0.9 - 0.15 * j, 0.75 - 0.15 * j).m("spd_tendril"))
        out.append(Sphere(0.75).m("spd_tip").at(*pts[-1]))
    return Union(*out)


def parts(ph=0.0, pulse=0.0, sac="spd_sac", bob=0.0, squeeze=0.0, curl=0.0, tilt=0.0):
    def place(s):
        return s.rot(0, 0, tilt).rot(0, YAW, 0).rot(PITCH, 0, 0).at(0, CY + bob, 0)
    return [Part(place(balloon(pulse, sac, squeeze)), name="balloon"), Part(place(tendrils(ph, curl)), name="tendrils")]


def crown_px(bob=0.0):
    return to_px(0.0, CY + bob + R[1] + 2.0, RANCHOR)


ANIMS = [
    ("fly", 10, "loop", 8, "drifting: the balloon pulses, tendrils wave, spore sacs glow"),
    ("attack", 12, "loop", 6, "puff: contracts (0-1), spores burst from the crown (2-4), refills (5)"),
    ("hurt", 14, "loop", 3, "shrivels"),
]


def frame(job):
    name, i = job
    if name == "fly":
        ph = 2 * math.pi * i / 8
        return shoot(parts(ph, pulse=0.035 * math.sin(ph), sac="spd_sac" if i % 4 < 2 else "spd_sac_dim",
                           bob=0.8 * math.sin(ph + 1.0)), size=SIZE, ranchor=RANCHOR)
    if name == "attack":
        sq = [0.04, 0.09, -0.04, -0.02, 0.0, 0.02][i]
        spr = shoot(parts(i * 0.8, pulse=0.0, squeeze=sq, sac="spd_sac", curl=0.4 if i in (1, 2) else 0.0),
                    size=SIZE, ranchor=RANCHOR)
        cx, cy = crown_px()
        if i >= 2:
            k = i - 2
            for j, (dx, dy) in enumerate(((0, -3), (-4, -2), (4, -2), (-2, -6), (3, -7))):
                if j > 1 + 2 * k:
                    continue
                r = [2.4, 1.8, 1.8, 1.6, 1.4][j] - 0.3 * k
                d = 1 + k * 0.8
                x, y = int(cx + dx * d), int(cy + dy * d)
                blob(spr, x, y, r + 0.7, "purple:3", glow=True, empty_only=True)
                blob(spr, x, y, r, "magenta:5" if j % 2 == 0 else "violet:5", glow=True)
                put(spr, x - 1, y - 1, "rose:7")
        return spr
    return shoot(parts(i * 1.2, squeeze=[0.14, 0.1, 0.05][i], sac="spd_sac_dim", curl=0.8, tilt=[12, -8, 4][i]),
                 size=SIZE, ranchor=RANCHOR)


def jobs():
    return anim_jobs(ANIMS)


def sheets(frames):
    dx, dy = point_of(0.0, CY + R[1] + 2.0, ANCHOR, RANCHOR)
    return make_sheet("sporepod", SIZE, ANCHOR, "spore pod (episode 2 floater, box 22 x 22, faces right)", ANIMS, frames,
                      points=[("muzzle", dx, dy, "the crown vents (spores; the engine currently shoots from the box "
                                                 "centre)")],
                      notes=["anchor = bottom centre of the box; tendrils hang about 12 px below it",
                             "glow: magenta spore sacs and vent mouths, teal tendril tips, the spore puff"])
