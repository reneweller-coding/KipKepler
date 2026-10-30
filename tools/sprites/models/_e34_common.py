"""Shared helpers of the episode 3 and 4 enemy sheets.

Episode 3: crystalcrab, icebat, shardling, cryoturret, minerbot, burrower, frostgolem, wisp.
Episode 4: trooper, shieldbot, jetpacker, gloamhound, lasereye, blinker, brute, riftgate.

* `Enemy`     the sheet scaffold: anims -> jobs() / frame() / sheets(), anchor and the ground-line render offset,
              named points, notes, and a preview on the episode's real tile sets (work/sprites/<id>_worlds.png)
* `Biped`     a two-legged rig with foot IK (the androids), after hero.py
* `walk_feet` planted-foot walk cycles
* 2D touches  sparkles, sparks, frost puffs, debris, glitch slices
* `lineup`    every sheet's first frames side by side on the episode backdrops (python models/_e34_common.py)

Materials of these models are prefixed with their sheet id (or "e34_" here) so they never clash with other
models imported into the same process.
"""
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parents[1]
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from bake import (ASSETS, ROOT, WORK, Canvas, Rig, Sheet, col, empty_sprite, ik2, material, pixelize,  # noqa: E402
                  render, rot, smooth, trans)

TAU = 2 * math.pi
THEMES = {3: ("ice", "crystal"), 4: ("foundry", "citadel")}

# ---------------------------------------------------------------------------------------------------------- Gloam look
# Episode 4, the Gloam's machine army: black-violet alloy whose lit edges catch a cold violet sheen (so it reads on
# the dark foundry and citadel backs), lighter armour plates, magenta and cyan neon.
material("e34_alloy", ["violet:0", "slate:1", "violet:1", "violet:2", "slate:3", "violet:4", "violet:6"], style="metal",
         bands=[-0.35, 0.05, 0.42, 0.66, 0.84], spec=0.86, line="outline", line_lit="violet:0")
material("e34_plate", ["violet:1", "slate:2", "violet:3", "slate:4", "violet:5", "slate:6", "white"], style="metal",
         bands=[-0.5, -0.18, 0.12, 0.42, 0.7], spec=0.9, line_lit="violet:0")
material("e34_joint", ["outline", "violet:0", "slate:1", "slate:2"], bands=[-0.3, 0.2, 0.7])
material("e34_magenta", ["magenta:4", "magenta:5", "magenta:6", "white"], style="emit", bands=[0.3, 0.6, 0.85],
         prio=3.0)
material("e34_magenta_dim", ["magenta:2", "magenta:3", "magenta:4"], style="emit", bands=[0.4, 0.8], prio=2.5)
material("e34_cyan", ["cyan:4", "cyan:5", "cyan:6", "white"], style="emit", bands=[0.3, 0.6, 0.85], prio=3.0)
material("e34_cyan_dim", ["blue:3", "cyan:3", "cyan:4"], style="emit", bands=[0.4, 0.8], prio=2.5)
material("e34_off", ["violet:0", "violet:1", "violet:2"], bands=[0.0, 0.6], prio=2.0)
material("e34_flame", ["magenta:4", "rose:5", "rose:6", "white"], style="emit", bands=[0.25, 0.55, 0.85],
         line="magenta:2", line_lit="magenta:2", inner=False)
material("e34_flame_c", ["blue:4", "cyan:5", "cyan:6", "white"], style="emit", bands=[0.25, 0.55, 0.85],
         line="blue:2", line_lit="blue:2", inner=False)


# ---------------------------------------------------------------------------------------------------------- scaffold

class Enemy:
    """One enemy sheet. Register animations with `anim(name, fps, mode, count, fn)`: fn(i) returns frame i (a
    Sprite); `order` (optional) is the playback list of local frame indices (repeats allowed)."""

    def __init__(self, name, size, anchor, title, episode, ground=True, ss=4):
        self.name, self.size, self.anchor, self.title, self.episode = name, size, anchor, title, episode
        self.ss = ss
        # walkers: world y = 0 one row above the sheet anchor, so the outline under the feet is that row
        self.ranchor = (anchor[0], anchor[1] - 1) if ground else anchor
        self.dy = anchor[1] - self.ranchor[1]
        self.anims = []
        self.fns = {}
        self.points = []
        self.notes = []
        # world preview context per anim: "floor", "air" or ("ceiling", row of the ceiling's lower edge)
        self.context = {}
        self.default_context = "floor" if ground else "air"

    # registration
    def anim(self, name, fps, mode, count, fn, note="", order=None):
        self.anims.append((name, fps, mode, count, note, order))
        self.fns[name] = fn

    def point(self, name, wx, wy, note=""):
        """A named point from world coordinates (x right, y up, origin = render anchor)."""
        self.points.append((name, wx, -wy - self.dy, note))

    def note(self, text):
        self.notes.append(text)

    # build.py interface
    def jobs(self):
        return [(a[0], i) for a in self.anims for i in range(a[3])]

    def frame(self, job):
        name, i = job
        return self.fns[name](i)

    def sheets(self, frames):
        sh = Sheet(self.name, self.size, self.anchor, cols=16, title=self.title)
        for name, dx, dy, note in self.points:
            sh.point(name, dx, dy, note)
        for n in self.notes:
            sh.note(n)
        for name, fps, mode, count, note, order in self.anims:
            idx = sh.anim(name, fps, mode, [frames[(name, i)] for i in range(count)], note=note)
            if order is not None:
                sh.anims[-1] = (name, fps, mode, [idx[k] for k in order], note)
        try:
            ctx = [self.context.get(a[0], self.default_context) for a in self.anims]
            world_preview(sh, THEMES[self.episode], ctx)
        except Exception as ex:  # previews must never break a build
            print(f"{self.name}: world preview failed: {ex}")
        return [sh]

    # rendering
    def canvas(self, ss=None):
        return Canvas(self.size, self.ranchor, ss=ss or self.ss)

    def raster(self, parts, squash=(1.0, 1.0), pivot=(0.0, 0.0), ss=None):
        return render(parts, self.size, self.ranchor, ss=ss or self.ss, squash=squash, pivot=pivot)

    def draw(self, parts, squash=(1.0, 1.0), pivot=(0.0, 0.0), canvas=None, under=None, cov=7, inner=True, ss=None,
             post=None):
        """Renders parts (+ optional canvas overlay: under = canvas behind the 3D parts) and pixelizes.
        post(raster) may edit the raster before pixelizing (erase below the ground, ...)."""
        r = self.raster(parts, squash, pivot, ss)
        for cv, below in _canvases(canvas, under):
            if below:
                cv.z[cv.col >= 0] = -1e6
                r.overlay(cv, zmode=True)
            else:
                r.overlay(cv)
        if post is not None:
            post(r)
        return pixelize(r, cov=cov, inner=inner)

    def px(self, wx, wy):
        """Frame pixel of a world point."""
        return int(round(self.ranchor[0] + wx)), int(round(self.ranchor[1] - wy))


def _canvases(canvas, under):
    if canvas is None:
        return []
    if isinstance(canvas, (list, tuple)):
        unders = under if isinstance(under, (list, tuple)) else [bool(under)] * len(canvas)
        return list(zip(canvas, unders))
    return [(canvas, bool(under))]


def below_ground(r, y=0.0):
    """Raster post step: erases everything below world height y (things half in the ground)."""
    X, Y = r.grid()
    r.erase(Y < y)


# ---------------------------------------------------------------------------------------------------------- biped

class Biped:
    """Two legs with foot IK, two arms, spine and head (after hero.py). Lengths in target pixels.
    Model space: x forward, y up, z towards the viewer (the right side "r" is the near side)."""

    def __init__(self, thigh, shin, ankle_h, upper, fore, hip_w, sh_w, sh_y, neck_y, hip_drop=0.6, sh_x=0.0,
                 sole=(-2.4, 3.6)):
        self.L_THIGH, self.L_SHIN, self.ANKLE_H = thigh, shin, ankle_h
        self.L_UPPER, self.L_FORE = upper, fore
        self.HIP_DROP = hip_drop
        self.PELVIS_Y = ankle_h + shin + thigh + hip_drop
        self.SOLE = ((sole[0], -ankle_h), (sole[1], -ankle_h))
        R = Rig()
        R.joint("pelvis", None, (0, self.PELVIS_Y, 0))
        R.joint("spine", "pelvis", (0, 1.0, 0))
        R.joint("head", "spine", (0, neck_y, 0))
        for side, z in (("r", 1), ("l", -1)):
            R.joint(f"sh_{side}", "spine", (sh_x, sh_y, sh_w * z))
            R.joint(f"el_{side}", f"sh_{side}", (0, -upper, 0))
            R.joint(f"wr_{side}", f"el_{side}", (0, -fore, 0))
            R.joint(f"hip_{side}", "pelvis", (0, -hip_drop, hip_w * z))
            R.joint(f"kn_{side}", f"hip_{side}", (0, -thigh, 0))
            R.joint(f"an_{side}", f"kn_{side}", (0, -shin, 0))
        self.rig = R

    def pose(self, **kw):
        p = dict(root=(0.0, 0.0), body_rot=0.0, yaw=-30.0, leg_ry=12.0, pelvis_x=0.0, pelvis_y=self.PELVIS_Y - 0.2,
                 pelvis=(0, 0, 0), spine=(0, 0, 0), head=(0, 0, 0),
                 sh_r=(-6, 0, 8), el_r=(0, 0, 30), wr_r=(0, 0, 0), sh_l=(6, 0, -8), el_l=(0, 0, 30),
                 wr_l=(0, 0, 0), foot_r=(2.0, 0.0, 0.0), foot_l=(-2.0, 0.0, 0.0), arm_ry=0.0)
        p.update(kw)
        return p

    def _leg_ik(self, pose, P, side):
        fx, fy, pitch = pose[f"foot_{side}"]
        sp, cp = math.sin(math.radians(pitch)), math.cos(math.radians(pitch))
        low = min(x * sp + y * cp for x, y in self.SOLE)
        fy = max(fy, -low - self.ANKLE_H)
        hip = P[f"hip_{side}"][:3, 3]
        a1, a2 = ik2((hip[0], hip[1]), (fx, fy + self.ANKLE_H), self.L_THIGH, self.L_SHIN, bend=1.0)
        parent = pose["pelvis"][2]
        pose[f"hip_{side}"] = (0, 0, a1 - parent)
        pose[f"kn_{side}"] = (0, 0, a2)
        pose[f"an_{side}"] = (0, 0, pitch - (a1 + a2))

    def solve(self, pose):
        pose = dict(pose)
        if pose.get("arm_ry"):
            for s in ("sh_r", "sh_l"):
                rx, ry, rz = pose[s]
                pose[s] = (rx, ry + pose["arm_ry"], rz)
        self.rig.joints["pelvis"] = (None, np.array([pose["pelvis_x"], pose["pelvis_y"], 0.0]))
        P0 = self.rig.solve(pose)
        for side in ("r", "l"):
            if pose.get(f"foot_{side}") is not None and f"hip_{side}" not in pose:
                self._leg_ik(pose, P0, side)
        lr = pose["leg_ry"]
        if lr:
            px, py, pz = pose["pelvis"]
            sx, sy, sz = pose["spine"]
            pose["pelvis"] = (px, py + lr, pz)
            pose["spine"] = (sx, sy - lr, sz)
        base = trans(pose["root"][0], pose["root"][1], 0) @ rot(0, 0, pose["body_rot"]) @ rot(0, pose["yaw"], 0)
        return self.rig.solve(pose, base), pose

    def point(self, pose, joint, local):
        W, _ = self.solve(pose)
        q = W[joint] @ np.array([*local, 1.0])
        return q[0], q[1]


def walk_feet(n, stride, lift, duty=0.55, toe=-28.0, heel=12.0):
    """One foot's (x, y, pitch) over an n-frame walk loop: planted and sliding back for `duty` of the cycle, then
    an arcing swing forward. The other foot is the same list shifted by n / 2."""
    out = []
    for i in range(n):
        ph = i / n
        if ph < duty:
            u = ph / duty
            x = stride / 2 - stride * u
            out.append((x, 0.0, heel * max(0.0, 1 - u * 4) + toe * 0.6 * max(0.0, u * 4 - 3)))
        else:
            u = (ph - duty) / (1 - duty)
            x = -stride / 2 + stride * smooth(u)
            out.append((x, lift * math.sin(math.pi * u), toe * (1 - u) + heel * u * u))
    return out


# ---------------------------------------------------------------------------------------------------------- 2D touches

def sparkle(spr, x, y, size, c1="white", c2="cyan:6"):
    spr.put(x, y, c1, glow=True)
    for k in range(1, size + 1):
        c = c1 if k < size else c2
        for dx, dy in ((k, 0), (-k, 0), (0, k), (0, -k)):
            spr.put(x + dx, y + dy, c, glow=True)


def spark(spr, x, y, size, hot="yellow:5", cold="orange:4"):
    spr.put(x, y, "white", glow=True)
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        spr.put(x + dx, y + dy, hot, glow=True)
    if size > 1:
        for dx, dy in ((2, -2), (-2, -2), (2, 2), (-2, 2)):
            spr.put(x + dx, y + dy, cold, glow=True)


def chip(spr, x, y, kind=0, colours=("ice:6", "ice:4", "blue:2")):
    """A small debris chip (2 x 2 with a dark edge) where the frame is empty."""
    pats = [((0, 0, 0), (1, 0, 1), (0, 1, 1), (1, 1, 2)), ((0, 0, 0), (1, 0, 1), (1, 1, 2)),
            ((0, 0, 0), (0, 1, 1), (1, 1, 2))]
    for dx, dy, c in pats[kind % len(pats)]:
        if spr.get(x + dx, y + dy) < 0:
            spr.put(x + dx, y + dy, colours[c])


def puff(spr, x, y, r, colours=("ice:7", "ice:6", "ice:5"), glow=False):
    """A soft vapour puff (rings of colour) into empty pixels only."""
    for yy in range(y - r, y + r + 1):
        for xx in range(x - r, x + r + 1):
            d = math.hypot(xx - x, (yy - y) * 1.2)
            if d <= r and spr.get(xx, yy) < 0:
                k = 0 if d < r * 0.4 else (1 if d < r * 0.75 else 2)
                spr.put(xx, yy, colours[k], glow=glow)


def glitch(spr, rows, shift):
    """Phasing: moves the given pixel rows sideways by shift (wraps nothing; pixels pushed out are lost)."""
    for y in rows:
        if not 0 <= y < spr.h:
            continue
        c, m, e = spr.col[y].copy(), spr.mat[y].copy(), spr.emit[y].copy()
        spr.col[y], spr.mat[y], spr.emit[y] = -1, -1, False
        for x in range(spr.w):
            tx = x + shift
            if 0 <= tx < spr.w and c[x] >= 0:
                spr.col[y, tx], spr.mat[y, tx], spr.emit[y, tx] = c[x], m[x], e[x]


def recolor(spr, mapping, glow=None):
    """Replaces palette colours: mapping {spec: spec}."""
    for a, b in mapping.items():
        sel = spr.col == col(a)
        spr.col[sel] = col(b)
        if glow is not None:
            spr.emit[sel] = glow


def flash(spr, amount=1):
    """A hurt flash: every colour one step lighter on its ramp (white stays white, outline stays)."""
    m = spr.col >= 2
    c = spr.col[m] - 2
    ramp, shade = c // 8, c % 8
    shade = np.minimum(shade + amount, 7)
    spr.col[m] = (2 + ramp * 8 + shade).astype(np.int16)
    return spr


# ---------------------------------------------------------------------------------------------------------- previews

_TILE_CACHE = {}


def _theme_imgs(theme):
    if theme not in _TILE_CACHE:
        tiles = ROOT / "assets" / "tiles" / theme
        bgd = ROOT / "assets" / "bg" / f"{theme}_a"
        back = Image.open(tiles / "back.png").convert("RGBA")
        ter = Image.open(tiles / "terrain_a.png").convert("RGBA")
        layers = [Image.open(bgd / f"layer{k}.png").convert("RGBA") for k in range(4)]
        _TILE_CACHE[theme] = (back, ter, layers)
    return _TILE_CACHE[theme]


def _tile(img, idx):
    c, r = idx % 16, idx // 16
    return img.crop((c * 32, r * 32, c * 32 + 32, r * 32 + 32))


def backdrop(theme, W, H, gy, wall, floor=True):
    """A W x H backdrop at 1x: the theme's back wall tiles (wall=True) or its parallax sky, a floor of terrain tiles
    whose top edge is row gy."""
    back, ter, layers = _theme_imgs(theme)
    im = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    if wall:
        for x in range(0, W, 32):
            for y in range(gy - 32 * ((gy + 31) // 32), H, 32):
                im.alpha_composite(_tile(back, 255 + 256 * ((x // 32 + y // 32) % 4)), (x, y))
    else:
        for L in layers:
            y0 = max(0, L.height - gy - 70)
            for x in range(0, W, L.width):
                im.alpha_composite(L.crop((0, y0, min(L.width, W - x), y0 + H)), (x, 0))
    if floor:
        for x in range(0, W, 32):
            im.alpha_composite(_tile(ter, 124 + 256 * ((x // 32) % 4)), (x, gy))
            im.alpha_composite(_tile(ter, 255 + 256 * ((x // 32) % 4)), (x, gy + 32))
    return im


def compose(sprites, anchor, theme, wall, ctx, gap=8):
    fw, fh = sprites[0].w, sprites[0].h
    W = len(sprites) * (fw + gap) + gap
    H = fh + 14
    gy = 6 + anchor[1]
    im = backdrop(theme, W, H, gy, wall, floor=False)
    _, ter, _ = _theme_imgs(theme)
    for i, (s, c) in enumerate(zip(sprites, ctx)):
        x0 = gap + i * (fw + gap)
        if c == "floor":
            seg = Image.new("RGBA", (fw + gap, 40))
            for x in range(-((x0 - gap // 2) % 32), fw + gap, 32):
                seg.alpha_composite(_tile(ter, 124 + 256 * (((x0 + x) // 32) % 4)), (x, 0))
            im.alpha_composite(seg.crop((0, 0, fw + gap, H - gy)), (x0 - gap // 2, gy))
        elif isinstance(c, tuple) and c[0] == "ceiling":
            cy = 6 + c[1]
            seg = Image.new("RGBA", (fw + gap, 32))
            for x in range(-((x0 - gap // 2) % 32), fw + gap, 32):
                seg.alpha_composite(_tile(ter, 199 + 256 * (((x0 + x) // 32) % 4)), (x, 0))
            im.alpha_composite(seg.crop((0, max(0, 32 - cy), fw + gap, 32)), (x0 - gap // 2, max(0, cy - 32)))
        a = Image.fromarray(s.rgba(), "RGBA")
        im.alpha_composite(a, (x0, 6))
    return im.convert("RGB")


def world_preview(sh, themes, ctx=None, scale=3):
    """work/sprites/<id>_worlds.png: the first frame of every animation at 1x on each theme's back wall and sky
    (ctx per anim: "floor", "air" or ("ceiling", row))."""
    picks = [idx[0] for _, _, _, idx, _ in sh.anims]
    sl = [sh.frames[i] for i in picks]
    ctx = ctx or ["floor"] * len(sl)
    rows = []
    for th in themes:
        for wall in (True, False):
            rows.append(compose(sl, sh.anchor, th, wall, ctx))
    W = max(r.width for r in rows)
    out = Image.new("RGB", (W, sum(r.height for r in rows)), (0, 0, 0))
    y = 0
    for r in rows:
        out.paste(r, (0, y))
        y += r.height
    WORK.mkdir(parents=True, exist_ok=True)
    out.resize((out.width * scale, out.height * scale), Image.NEAREST).save(WORK / f"{sh.name}_worlds.png")


def _read_sheet(name):
    txt = (ASSETS / f"{name}.txt").read_text(encoding="utf-8")
    fw = fh = None
    anchor = None
    anims = {}
    for ln in txt.splitlines():
        s = ln.split("#")[0].split()
        if not s:
            continue
        if s[0] == "frame":
            fw, fh = int(s[1]), int(s[2])
        elif s[0] == "anchor":
            anchor = (int(s[1]), int(s[2]))
        elif s[0] == "anim":
            anims[s[1]] = [int(v) for v in s[4:]]
    img = np.asarray(Image.open(ASSETS / f"{name}.png").convert("RGBA"))
    cols = img.shape[1] // fw

    def get(i):
        r, c = divmod(i, cols)
        return img[r * fh:(r + 1) * fh, c * fw:(c + 1) * fw]
    return fw, fh, anchor, anims, get


def lineup(names, out, anim=None, scale=3, frame_k=0):
    """All sheets side by side at 1x, feet on one floor line, on every episode backdrop (a readability check)."""
    sheets = [_read_sheet(n) for n in names]
    gap = 6
    W = sum(s[0] for s in sheets) + gap * (len(sheets) + 1)
    top = max(s[2][1] for s in sheets)
    H = top + 16
    rows = []
    for th in ("ice", "crystal", "foundry", "citadel"):
        for wall in (True, False):
            gy = 6 + top
            im = backdrop(th, W, H, gy, wall)
            x = gap
            for (fw, fh, anchor, anims, get), n in zip(sheets, names):
                a = anim if anim in anims else next(iter(anims))
                idx = anims[a]
                f = get(idx[min(frame_k, len(idx) - 1)])
                ai = Image.fromarray(f, "RGBA")
                im.alpha_composite(ai, (x, gy - anchor[1]))
                x += fw + gap
            rows.append(im.convert("RGB"))
    img = Image.new("RGB", (W, sum(r.height for r in rows)))
    y = 0
    for r in rows:
        img.paste(r, (0, y))
        y += r.height
    img.resize((W * scale, img.height * scale), Image.NEAREST).save(out)


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="lineup of enemy sheets on the episode backdrops")
    ap.add_argument("out")
    ap.add_argument("names", nargs="+")
    ap.add_argument("--anim", default=None)
    ap.add_argument("--k", type=int, default=0)
    ap.add_argument("--scale", type=int, default=3)
    a = ap.parse_args()
    lineup(a.names, a.out, a.anim, a.scale, a.k)
