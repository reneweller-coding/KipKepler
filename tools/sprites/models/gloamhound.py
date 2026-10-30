"""gloamhound -- episode 4 charger (box 36 x 26): a lean robotic hound of black-violet alloy, a long wedge head with a
magenta eye slit and a glowing jaw line, dorsal blade fins, digitigrade hind legs, a whip tail with a light.

64 x 64 frames, anchor (32, 60). move = trot, attack = wind-up (crouch, fins up, jaws open) then a bounding gallop,
hurt = dazed after hitting a wall.
Model space: x forward, y up, z towards the viewer; legs IK'd to planted paws.
"""
import math

import numpy as np

from bake import Box, Capsule, Chamfer, Cone, Extrude, Part, RoundCone, Sphere, Union, ik2, material, rot, trans
from models._e34_common import TAU, Enemy, flash, puff, spark, sparkle

E = Enemy("gloamhound", (64, 64), (32, 60), "Gloam hound (episode 4 charger, faces right)", 4)

YAW = -16.0
U1, U2 = 5.4, 5.6           # front leg: upper, lower (wrist to paw is fixed)
T1, T2 = 5.6, 6.0           # hind leg: thigh, shin (the hock to paw is fixed)
SHOULDER = (6.4, 13.6)      # body space, front leg root
HIP = (-7.6, 13.8)          # hind leg root
SIDES = ((2.8, 0), (-2.8, -1))


def body(fins=0.0, breathe=0.0):
    chest = Chamfer(5.6, 4.0, 3.8, 1.4).m("e34_alloy").rot(0, 0, 8).at(4.6, 14.4 + breathe, 0)
    keel = Extrude([(1.0, 11.0), (8.6, 12.0), (9.6, 15.6), (2.0, 13.8)], 3.0, r=0.5).m("e34_plate")
    waist = Chamfer(4.4, 2.4, 2.6, 0.9).m("e34_joint").at(-2.4, 14.6, 0)
    hips = Chamfer(4.2, 3.4, 3.4, 1.2).m("e34_alloy").rot(0, 0, -6).at(-7.6, 14.8, 0)
    flank = Extrude([(-11.0, 13.0), (-4.6, 12.6), (-3.8, 16.4), (-9.6, 18.0)], 3.5, r=0.5).m("e34_plate")
    lights = Union(*[Box(0.8, 0.3, 0.3).m("e34_magenta_dim").at(-1.0 - 2.0 * k, 13.2, 2.7) for k in range(3)])
    fin_h = 1.0 + 1.6 * fins
    fl = []
    for k, (x, h) in enumerate(((5.6, 3.4), (2.0, 2.8), (-1.6, 2.2), (-5.4, 2.6))):
        fl.append(Extrude([(x - 1.6, 0), (x + 1.0, 0), (x - 2.4, h * fin_h)], 0.5, r=0.15).m("e34_plate")
                  .at(0, 17.2 + (0.6 if k == 0 else 0), 0))
    return Union(chest, keel, waist, hips, flank, lights, *fl)


def head(jaw=0.0, eye="e34_magenta"):
    """Head in neck space: the snout points along +x."""
    skull = Extrude([(-2.4, -1.4), (3.2, -1.2), (8.0, -0.6), (8.6, 0.6), (3.6, 2.6), (-1.6, 3.0)], 2.3, r=0.5) \
        .m("e34_alloy")
    plate = Extrude([(0.6, 1.6), (6.0, 0.6), (7.0, 1.2), (2.4, 3.2)], 2.5, r=0.3).m("e34_plate")
    slit = Box(1.6, 0.4, 2.5, r=0.12).m(eye).rot(0, 0, -8).at(3.4, 1.2, 0)
    a = jaw * 26
    jaw_s = Extrude([(-1.0, -0.6), (6.6, -0.4), (6.2, -1.6), (-0.6, -2.4)], 1.9, r=0.4).m("e34_alloy") \
        .rot(0, 0, -a).at(0.6, -0.6, 0)
    jaw_l = Box(2.6, 0.25, 2.0).m("e34_magenta_dim" if jaw < 0.3 else "e34_magenta").rot(0, 0, -a * 0.5) \
        .at(4.0, -1.3, 0)
    ears = [Extrude([(-1.4, 2.2), (0.4, 2.6), (-3.8, 5.6)], 0.4, r=0.15).m("e34_plate").at(0, 0, z)
            for z in (1.6, -1.6)]
    return Union(skull, plate, slit, jaw_s, jaw_l, *ears)


def neck():
    return Union(Capsule((0, 0, 0), (3.6, 2.6, 0), 1.9).m("e34_joint"),
                 Extrude([(-0.6, 1.2), (3.4, 3.6), (2.6, 4.6), (-1.6, 2.6)], 1.6, r=0.3).m("e34_plate"))


def leg_front(paw):
    """Front leg from the shoulder to a paw position (body space), elbow bent back."""
    wx, wy = paw[0] + 0.4, paw[1] + 2.4
    a1, a2 = ik2(SHOULDER, (wx, wy), U1, U2, bend=-1.0)
    s = np.array(SHOULDER)
    r1 = math.radians(a1)
    el = s + U1 * np.array([math.sin(r1), -math.cos(r1)])
    r2 = math.radians(a1 + a2)
    wr = el + U2 * np.array([math.sin(r2), -math.cos(r2)])
    P = lambda v: (v[0], v[1], 0.0)  # noqa: E731
    return Union(Capsule(P(s), P(el), 1.6).m("e34_alloy"),
                 Chamfer(1.3, U2 / 2, 1.2, 0.4).m("e34_plate").rot(0, 0, a1 + a2).at(*P((el + wr) / 2)),
                 Sphere(1.1).m("e34_joint").at(*P(el)),
                 RoundCone(P(wr), (paw[0], paw[1] + 0.6, 0), 0.9, 0.7).m("e34_joint"),
                 Extrude([(-1.0, -0.6), (2.4, -0.6), (1.4, 0.6), (-0.6, 0.8)], 1.0, r=0.2).m("e34_alloy")
                 .at(paw[0], paw[1] + 0.6, 0))


def leg_hind(paw):
    """Hind leg: hip -> knee (forward) -> hock (behind the paw) -> paw."""
    hx, hy = paw[0] - 1.6, paw[1] + 4.2
    a1, a2 = ik2(HIP, (hx, hy), T1, T2, bend=1.0)
    s = np.array(HIP)
    r1 = math.radians(a1)
    kn = s + T1 * np.array([math.sin(r1), -math.cos(r1)])
    hk = np.array([hx, hy])
    P = lambda v: (v[0], v[1], 0.0)  # noqa: E731
    return Union(Chamfer(2.2, T1 / 2 + 0.6, 1.8, 0.7).m("e34_alloy").rot(0, 0, a1).at(*P((s + kn) / 2)),
                 Capsule(P(kn), P(hk), 1.15).m("e34_plate"),
                 Sphere(1.2).m("e34_joint").at(*P(hk)),
                 RoundCone(P(hk), (paw[0], paw[1] + 0.6, 0), 0.9, 0.6).m("e34_joint"),
                 Extrude([(-0.8, -0.6), (2.2, -0.6), (1.2, 0.6), (-0.6, 0.8)], 1.0, r=0.2).m("e34_alloy")
                 .at(paw[0], paw[1] + 0.6, 0))


def tail(sway, lift=0.0):
    pts = [(-11.2, 15.6)]
    a = math.radians(150 - 18 * lift)
    for k in range(4):
        a += math.radians(sway * (k + 1) * 0.5 - 6)
        x, y = pts[-1]
        pts.append((x + 2.6 * math.cos(a), y + 2.6 * math.sin(a)))
    segs = [Capsule((*pts[k], 0), (*pts[k + 1], 0), 0.75 - 0.08 * k).m("e34_alloy" if k % 2 else "e34_plate")
            for k in range(4)]
    tip = Sphere(0.9).m("e34_magenta").at(*pts[-1], 0)
    return Union(*segs, tip)


def parts(paws, root=(0.0, 0.0), pitch=0.0, head_a=0.0, neck_a=30.0, jaw=0.0, fins=0.0, sway=0.0, tail_lift=0.0,
          eye="e34_magenta", breathe=0.0):
    """paws: {('f'|'h', z): (x, y)} in body space (y = 0 the ground). pitch tilts the body about its middle."""
    B = trans(root[0], root[1], 0) @ rot(0, YAW, 0)
    pivot = np.array([0.0, 14.0])
    Bp = B @ trans(*pivot, 0) @ rot(0, 0, pitch) @ trans(*-pivot, 0)
    out = [Part(body(fins, breathe).xform(Bp), name="body"), Part(tail(sway, tail_lift).xform(Bp), name="tail")]
    N = Bp @ trans(8.6, 16.4, 0) @ rot(0, 0, neck_a)
    out.append(Part(neck().xform(N), name="neck"))
    H = N @ trans(3.6, 2.6, 0) @ rot(0, 0, head_a - neck_a)
    out.append(Part(head(jaw, eye).xform(H), name="head"))
    # legs are posed in the unpitched body space, their roots follow the pitch approximately
    c, s = math.cos(math.radians(pitch)), math.sin(math.radians(pitch))

    def piv(pt):
        d = np.array(pt) - pivot
        return pivot + np.array([c * d[0] - s * d[1], s * d[0] + c * d[1]])
    global SHOULDER, HIP
    sh0, hp0 = SHOULDER, HIP
    SHOULDER, HIP = tuple(piv(sh0)), tuple(piv(hp0))
    try:
        for z, shade in SIDES:
            # paws are given relative to the ground: undo the body offset for them
            fp = paws[("f", z)]
            hp = paws[("h", z)]
            fp = (fp[0] - root[0], fp[1] - root[1])
            hp = (hp[0] - root[0], hp[1] - root[1])
            out.append(Part(leg_front(fp).at(0, 0, z).xform(B), name=f"front{z}", shade=shade))
            out.append(Part(leg_hind(hp).at(0, 0, z).xform(B), name=f"hind{z}", shade=shade))
    finally:
        SHOULDER, HIP = sh0, hp0
    return out


def stand():
    return {("f", 2.8): (8.0, 0.0), ("f", -2.8): (6.2, 0.0), ("h", 2.8): (-7.2, 0.0), ("h", -2.8): (-9.0, 0.0)}


# ---------------------------------------------------------------------------------------------------------- gaits

def foot_cycle(ph, stride, lift, duty=0.55):
    ph %= 1.0
    if ph < duty:
        u = ph / duty
        return stride / 2 - stride * u, 0.0
    u = (ph - duty) / (1 - duty)
    return -stride / 2 + stride * (u * u * (3 - 2 * u)), lift * math.sin(math.pi * u)


HOME = {("f", 2.8): 7.6, ("f", -2.8): 7.0, ("h", 2.8): -7.8, ("h", -2.8): -8.4}


def trot(i, n=8):
    paws = {}
    for (kind, z), x0 in HOME.items():
        off = 0.0 if (kind == "f") == (z > 0) else 0.5          # diagonal pairs
        dx, y = foot_cycle(i / n + off, 7.0, 2.6)
        paws[(kind, z)] = (x0 + dx, y)
    return paws


def gallop(i, n=6):
    paws = {}
    for (kind, z), x0 in HOME.items():
        off = (0.0 if kind == "f" else 0.5) + (0.06 if z < 0 else 0.0)   # bound: front pair, hind pair
        dx, y = foot_cycle(i / n + off, 12.0, 4.0, duty=0.4)
        paws[(kind, z)] = (x0 + dx * 1.0, y)
    return paws


# ---------------------------------------------------------------------------------------------------------- animations

def move(i):
    n = 8
    ph = TAU * i / n
    bob = 0.5 * math.cos(2 * ph)
    return E.draw(parts(trot(i, n), root=(0, bob - 0.4), pitch=1.5 * math.sin(ph), neck_a=28 + 3 * math.cos(2 * ph),
                        head_a=-6, sway=8 * math.sin(ph), jaw=0.1))


def idle(i):
    n = 8
    t = i / n
    sniff = [0, 0, -14, -18, -14, 0, 0, 0][i]
    return E.draw(parts(stand(), neck_a=24 + sniff, head_a=-8 + sniff * 0.6, sway=10 * math.sin(TAU * t),
                        breathe=0.25 * math.sin(TAU * t), jaw=0.15 if i in (3,) else 0.0))


def windup(i):
    """Crouch with the rear up, head low, fins raised, jaws open: a snarl before the charge."""
    k = [0.3, 0.7, 1.0, 1.0, 1.0, 0.6][i]
    paws = {("f", 2.8): (9.4, 0.0), ("f", -2.8): (8.0, 0.0), ("h", 2.8): (-8.6, 0.0), ("h", -2.8): (-10.0, 0.0)}
    spr = E.draw(parts(paws, root=(-1.0 * k, -2.4 * k), pitch=-10 * k, neck_a=10 - 8 * k, head_a=-4 * k,
                       jaw=0.2 + 0.8 * k * (1 if i in (2, 3) else 0.6), fins=k, sway=-18 * k, tail_lift=k))
    if i in (2, 3):
        x, y = E.px(18, 13)
        spark(spr, x + (i - 2), y - 2, 1, hot="magenta:6", cold="magenta:4")
    return spr


def charge(i):
    n = 6
    ph = TAU * i / n
    spr = E.draw(parts(gallop(i, n), root=(0, 1.2 + 1.4 * max(0.0, math.sin(ph))), pitch=6 * math.sin(ph),
                       neck_a=6, head_a=-6, jaw=0.6, fins=0.6, sway=-24, tail_lift=0.4))
    for k in range(2):
        x, y = E.px(-16 - 4 * k - (i % 2) * 2, 1 + (k * 2 + i) % 3)
        puff(spr, x, y, 1, ("violet:5", "violet:4", "violet:3"))
    return spr


def hurt(i):
    n = 6
    ph = TAU * i / n
    spr = E.draw(parts(stand(), root=(-0.6, -0.6), pitch=4, neck_a=36 + 10 * math.sin(ph), head_a=10 * math.sin(2 * ph),
                       jaw=0.3, sway=-6, eye="e34_magenta_dim"))
    hx, hy = E.px(16, 24)
    for k in range(2):
        a = ph + k * math.pi
        sparkle(spr, int(round(hx + 5 * math.cos(a))), int(round(hy + 1.6 * math.sin(a))), 1, c1="white",
                c2="magenta:5")
    if i % 3 == 0:
        spark(spr, hx - 6, hy + 3, 1, hot="magenta:6", cold="violet:5")
    return spr


N_WIND, N_RUN = 6, 6
E.anim("move", 12, "loop", 8, move, "trot (diagonal pairs)")
E.anim("attack", 12, "loop", N_WIND + N_RUN, lambda i: windup(i) if i < N_WIND else charge(i - N_WIND),
       "wind-up snarl (0-5, 0.5 s) then the bounding gallop (6-11 repeated); 2.5 s before it wraps",
       order=list(range(N_WIND)) + list(range(N_WIND, N_WIND + N_RUN)) * 4)
E.anim("hurt", 10, "loop", 6, hurt, "dazed after hitting a wall")
E.anim("idle", 8, "loop", 8, idle, "sniffing, tail sway")
E.note("glow: eye slit, jaw line, tail light, flank lights")

jobs, frame, sheets = E.jobs, E.frame, E.sheets
