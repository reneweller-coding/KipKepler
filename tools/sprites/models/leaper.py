"""leaper -- episode 2 hopper (box 26 x 24): a frog-like alien with bulging glowing eyes and long hind legs.

64 x 64 frames, anchor (32, 60). idle = crouched on the ground (throat sac pulsing, winding up); attack = in the
air (launch stretch, tuck, legs forward to land; loops while airborne); hurt = flinch.
"""
import math

from bake import Box, Cone, Ellipsoid, Paint, Part, RoundCone, SmoothUnion, Sphere, Union, material
from models._e12_common import A64, S64, anim_jobs, make_sheet, shoot

YAW = -24.0

material("lpr_skin", ["green:1", "green:2", "green:3", "lime:4", "lime:5", "lime:6"],
         bands=[-0.55, -0.25, 0.1, 0.45, 0.8], line="green:0", line_lit="green:0")
material("lpr_stripe", ["violet:1", "violet:2", "purple:3", "purple:4"], bands=[-0.3, 0.2, 0.7], line="violet:0")
material("lpr_belly", ["tan:4", "tan:5", "tan:6", "tan:7"], bands=[-0.3, 0.2, 0.65], line="brown:1")
material("lpr_sac", ["crimson:3", "rose:4", "rose:5", "rose:6"], bands=[-0.3, 0.2, 0.65], line="crimson:1")
material("lpr_eye", ["orange:4", "yellow:5", "yellow:6", "yellow:7"], style="emit", bands=[0.3, 0.6, 0.88], prio=3.0)
material("lpr_pupil", ["outline", "violet:0"], bands=[0.3], prio=3.0)
material("lpr_lid", ["green:2", "green:3", "lime:4"], bands=[0.0, 0.6], prio=3.0)
material("lpr_spot", ["teal:4", "cyan:5", "cyan:6"], style="emit", bands=[0.4, 0.8], prio=2.5)
material("lpr_spine", ["violet:1", "purple:3", "purple:4", "magenta:5"], bands=[-0.3, 0.2, 0.7], line="violet:0")


def body(tilt, sac=1.6, blink=False, mouth=0.0):
    trunk = Ellipsoid(7.0, 4.4, 5.4).rot(0, 0, tilt).at(-1.6, 6.4, 0)
    head = Ellipsoid(4.8, 3.6, 5.0).at(4.4, 8.0 + tilt * 0.06, 0)
    skin = SmoothUnion(trunk, head, k=1.8).m("lpr_skin")
    belly = Ellipsoid(6.2, 2.4, 4.4).rot(0, 0, tilt).at(-0.6, 4.4, 0)
    skin = Paint(skin, belly, "lpr_belly")
    stripes = Union(*[Box(0.7, 6.0, 7.0).rot(0, 0, 20).at(x, 9.0, 0) for x in (-6.0, -3.4, -0.8)])
    skin = Paint(skin, Union(stripes.rot(0, 0, 0)), "lpr_stripe")
    skin = Paint(skin, Box(2.6, 0.32, 6.0).rot(0, 0, -8 - mouth).at(7.0, 6.4, 0), "lpr_stripe")
    sac_s = Ellipsoid(2.4, sac, 3.0).m("lpr_sac").at(5.0, 5.4 - sac * 0.5, 0)
    eyes = []
    for z in (2.6, -2.4):
        eyes.append(Sphere(2.15).m("lpr_lid" if blink else "lpr_eye").at(5.2, 11.0, z))
        if not blink and z > 0:
            eyes.append(Ellipsoid(0.75, 1.15, 0.75).m("lpr_pupil").at(5.2 + 1.55, 11.1, z + 1.25))
        if blink:
            eyes.append(Box(2.4, 0.4, 2.4).m("lpr_stripe").at(5.2, 11.0, z + 0.4))
    spines = [Cone(0.8, 0.1, 1.0).m("lpr_spine").rot(0, 0, 20).at(x, 10.6 - abs(x + 2.6) * 0.25, 0)
              for x in (-6.4, -4.2, -2.0, 0.2)]
    spots = [Sphere(0.85).m("lpr_spot").at(x, y, 4.6) for x, y in ((-5.0, 7.6), (-2.2, 8.6), (0.6, 7.4))]
    return Union(skin, sac_s, *eyes, *spines, *spots)


def hind_leg(H, K, A, T, z):
    return Union(RoundCone((H[0], H[1], z), (K[0], K[1], z * 1.25), 2.1, 1.4),
                 RoundCone((K[0], K[1], z * 1.25), (A[0], A[1], z * 1.3), 1.3, 0.9),
                 RoundCone((A[0], A[1], z * 1.3), (T[0], T[1], z * 1.35), 0.95, 0.7),
                 Sphere(0.9).at(T[0] + 0.3, T[1], z * 1.35)).m("lpr_skin")


def front_leg(S, E, W, z):
    return Union(RoundCone((S[0], S[1], z), (E[0], E[1], z * 1.1), 1.1, 0.8),
                 RoundCone((E[0], E[1], z * 1.1), (W[0], W[1], z * 1.15), 0.8, 0.6),
                 Sphere(0.8).at(W[0] + 0.2, W[1], z * 1.15)).m("lpr_skin")


CROUCH = dict(tilt=14, H=(-5.0, 5.6), K=(0.6, 3.6), A=(-6.0, 1.4), T=(-1.2, 0.7), S=(4.0, 4.6), E=(5.4, 2.6),
              W=(6.8, 0.8))


def pose(**kw):
    p = dict(CROUCH)
    p.update(kw)
    return p


def parts(p, lift=0.0, sac=1.6, blink=False, mouth=0.0, roll=0.0):
    def place(s):
        if roll:
            s = s.at(0, -6, 0).rot(0, 0, roll).at(0, 6, 0)
        return s.at(0, lift, 0).scale(1.3).rot(0, YAW, 0)
    out = [Part(place(body(p["tilt"], sac, blink, mouth)), name="body")]
    for z, sh, nm in ((3.4, 0, "n"), (-3.4, -1, "f")):
        out.append(Part(place(hind_leg(p["H"], p["K"], p["A"], p["T"], z)), name="hind_" + nm, shade=sh))
        out.append(Part(place(front_leg(p["S"], p["E"], p["W"], z * 0.9)), name="front_" + nm, shade=sh))
    return out


AIR = [
    pose(tilt=-6, H=(-5.0, 6.4), K=(-8.6, 3.6), A=(-13.0, 1.6), T=(-16.0, 0.4), S=(4.0, 4.8), E=(7.4, 4.0),
         W=(10.4, 4.6)),
    pose(tilt=-4, H=(-5.0, 6.4), K=(-8.2, 3.2), A=(-12.4, 1.8), T=(-15.4, 1.2), S=(4.0, 4.8), E=(7.6, 4.4),
         W=(10.6, 5.6)),
    pose(tilt=2, H=(-5.0, 6.0), K=(-3.4, 2.4), A=(-8.6, 2.0), T=(-6.4, 0.2), S=(4.0, 4.6), E=(7.0, 3.4),
         W=(9.6, 3.4)),
    pose(tilt=8, H=(-5.0, 5.6), K=(0.2, 3.2), A=(-5.0, 1.2), T=(-1.4, -0.4), S=(4.0, 4.4), E=(6.2, 2.2),
         W=(8.0, 0.6)),
    pose(tilt=12, H=(-5.0, 5.4), K=(1.4, 3.0), A=(-3.2, -0.6), T=(1.2, -1.4), S=(4.0, 4.4), E=(6.0, 2.0),
         W=(7.4, -0.6)),
    pose(tilt=4, H=(-5.0, 6.0), K=(-2.0, 2.6), A=(-7.0, 1.4), T=(-4.4, -0.4), S=(4.0, 4.6), E=(6.8, 3.0),
         W=(9.4, 2.4)),
]

ANIMS = [
    ("idle", 8, "loop", 8, "crouched: throat sac pulses, blinks, shifts its weight"),
    ("attack", 10, "loop", 6, "airborne: stretch (0-1), tuck (2-3), legs forward to land (4), loops while in the air"),
    ("hurt", 14, "loop", 3, "flinch"),
]


def frame(job):
    name, i = job
    if name == "idle":
        ph = 2 * math.pi * i / 8
        sac = 1.4 + 1.2 * max(0.0, math.sin(2 * ph))
        p = pose(tilt=14 + 2 * math.sin(ph), H=(-5.0, 5.6 - 0.3 * math.sin(ph)))
        return shoot(parts(p, sac=sac, blink=i == 6))
    if name == "attack":
        return shoot(parts(AIR[i], lift=4.0, sac=1.0, mouth=8 if i < 2 else 0))
    p = pose(tilt=[26, 22, 16][i], H=(-5.0, 6.4), S=(4.0, 5.4), E=(6.8, 7.0), W=(8.6, 9.0))
    spr = shoot(parts(p, sac=2.2, blink=i == 1, roll=[10, 6, 2][i], mouth=12))
    return spr


def jobs():
    return anim_jobs(ANIMS)


def sheets(frames):
    return make_sheet("leaper", S64, A64, "leaper frog-alien (episode 2 hopper, box 26 x 24, faces right)", ANIMS,
                      frames, notes=["anchor = bottom centre of the box (feet on the ground line)",
                                     "attack frames are lifted 4 px (legs dangle below the body in the air)",
                                     "glow: amber eyes, teal back spots"])
