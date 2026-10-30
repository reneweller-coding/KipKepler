# tools/sprites -- the sprite baker

Builds the sprite sheets in `assets/sprites/` (format: `docs/DESIGN.md`, "Sprite sheets"). Models are made from 3D
signed-distance primitives hanging on a small skeleton, ray-traced at 4x (or 6x) the target size, cel-shaded from
the shared palette, reduced to the target size by a majority (mode) filter, cleaned up and outlined. 2D effects use
the same grid and pixelizer. CPU only (numpy), no GPU.

```
python tools/sprites/build.py                  # rebuild every sheet (hero, items, objects, shots, fx + fx_big)
python tools/sprites/build.py hero shots       # only these model modules
python tools/sprites/build.py -j 1 hero        # serial, for debugging (default: 4 worker processes, below-normal priority)
```

Each run validates every sheet it writes (`bake.check_sheet`: frame grid, anim indices, alpha 0/255, every colour in
the palette, glow size) and prints problems. Previews land in `work/sprites/`:

* `<sheet>_dark_<n>.png`, `<sheet>_light_<n>.png` -- contact sheets, every frame enlarged, one row per animation,
  frame index and anchor (magenta tick) marked
* `<sheet>_scene.png` -- the first frame of every animation at game size on mock station / jungle / light
  backdrops, enlarged 3x: the readability check
* `gif/<sheet>_<anim>.gif` -- animated previews

Look at them after every change (the scene preview first).

## Files

| File | What |
|------|------|
| `bake.py` | the library: palette access, materials, SDF shapes, skeleton + IK, keyframe helpers, renderer, 2D canvas, pixelizer, Sheet writer, previews, validator |
| `build.py` | runs model modules in parallel and writes their sheets |
| `models/hero.py` | Kip Kepler (64 x 64, 20 animations) |
| `models/items.py` | pickups (32 x 32) |
| `models/objects.py` | exit gate, checkpoint, teleporter, switch, spring, sign, laser emitter (64 x 96) |
| `models/shots.py` | projectiles (32 x 32) |
| `models/fx.py` | effects (64 x 64) and `fx_big` (96 x 96) |

## Conventions

* World units are target pixels. x right, **y up**, z towards the viewer. The world origin is the frame's anchor
  point (pass a different `anchor` to `render` to move it).
* Light comes from the top left front (`bake.LIGHT`). Sprites face **right**.
* Ground line: walkers/standing objects are rendered with their render anchor one row above the sheet anchor
  (`RENDER_ANCHOR = (32, 59)` for a sheet anchor `(32, 60)`), so the 1 px outline under the feet is the row just above
  the anchor line and nothing pokes into the floor. If you do this, subtract the row in your point offsets too
  (see `hero.muzzle_px`).
* Leave at least 1 px free around the drawing for the outline; beams and tiling segments may touch the border.
* Colours only from the palette: `"ramp:shade"` (e.g. `"orange:4"`, shade 0 = darkest .. 7), `"outline"`, `"white"`.

## Adding a model (e.g. an enemy)

Create `models/<sheet>.py` with three functions and add its name to `MODELS` in `build.py`:

* `jobs()` -- a list of picklable job keys, one per frame (usually `(anim, index)`)
* `frame(job)` -- renders one frame and returns a `bake.Sprite` (runs in a worker process, so it must be a module
  level function and the module must register its materials at import time)
* `sheets(frames)` -- gets `{job: Sprite}` and returns a list of `bake.Sheet` (usually one)

Minimal working example (a hovering drone; copy and grow it):

```python
import math
from bake import (Box, Capsule, Cylinder, Part, Rig, Sheet, Sphere, Union, keys, material, pixelize, render)

SIZE, ANCHOR = (48, 48), (24, 24)            # fliers: anchor at the centre
material("dr_body", ["slate:2", "steel:3", "steel:5", "steel:6"], bands=[-0.4, 0.05, 0.7])
material("dr_eye", ["red:4", "red:6", "white"], style="emit", bands=[0.4, 0.8], prio=3.0)

RIG = Rig()
RIG.joint("body", None, (0, 0, 0))
RIG.joint("rotor", "body", (0, 7, 0))

def parts(pose):
    W = RIG.solve(pose)
    body = Union(Sphere(7).m("dr_body"), Sphere(2.2).m("dr_eye").at(5.6, 0.5, 2.5))
    rotor = Union(Cylinder(1, 2).m("dr_body"), Box(9, 0.4, 1.2, r=0.3).m("dr_body").rot(0, pose["spin"], 0))
    return [Part(body.xform(W["body"])), Part(rotor.xform(W["rotor"]))]

ANIMS = [("fly", 12, "loop", 4), ("hurt", 12, "once", 2)]

def frame(job):
    name, i = job
    tilt = keys([(0, -6), (2, 6), (4, -6)], i)          # keyframed body tilt
    pose = {"body": (0, -30, tilt), "spin": 45 * i}
    spr = pixelize(render(parts(pose), SIZE, ANCHOR))
    return spr

def jobs():
    return [(n, i) for n, fps, mode, count in ANIMS for i in range(count)]

def sheets(frames):
    sh = Sheet("drone", SIZE, ANCHOR, cols=8, title="example drone")
    for n, fps, mode, count in ANIMS:
        sh.anim(n, fps, mode, [frames[(n, i)] for i in range(count)])
    return [sh]
```

### Shapes (`bake.py`)

Primitives are centred at the origin: `Sphere(r)`, `Ellipsoid(rx, ry, rz)`, `Box(hx, hy, hz, r=bevel)`,
`Chamfer(hx, hy, hz, c)`, `RoundCone(a, b, r1, r2)` / `Capsule(a, b, r)` (between two points), `Cylinder(r, h, rr)`
(along y, half height h), `Cone(r1, r2, h)` (along y), `Torus(R, r)` (in xz), `Lathe([(r, y), ...])` (profile around
y), `Extrude([(x, y), ...], hz, r)` (2D polygon, depth along z), `Poly(planes, extent)` (convex polyhedron;
`prism(...)` and `bipyramid(...)` make crystals).

Transforms and booleans: `.at(x, y, z)`, `.rot(rx, ry, rz)` (degrees, applied z, then x, then y), `.scale(s)`
(uniform only), `.xform(M)`, `a | b` (union), `a - b` (subtract; the cut takes `b`'s material if it has one),
`a & b` (intersect), `SmoothUnion(..., k)`, `Round(s, r)`, `Shell(s, t)`, `Paint(shape, region, "mat")` (paints a
material wherever the surface lies inside `region`: visors, stripes, printed icons, moving glints).
`.m("name")` sets the material; inner shapes keep their own.

### Materials

`material(name, colours, style=..., bands=..., ...)` -- `colours` are palette specs dark to light, `bands` the N.L
thresholds between them (len(colours) - 1; for `metal`/`glass` one less, the last colour is the specular).
Styles: `cel`, `metal` (specular band), `glass` (specular + horizon band; visors, orbs), `emit` (bands on facing,
glows), `flat`. Options: `glow=True` (into the _glow mask), `prio` (weight in the majority filter: small important
details such as eyes, lights, a muzzle use 2-3 so they survive the 4x reduction), `line` / `line_lit` (outline colour
on the shadow / lit side), `inner=False` (no dark inner lines on it), `outline=False` (beams, holograms).

Pick 3-5 colours per material; put the base colour where most of the surface faces (sides facing the viewer have
N.L around 0.7 with the default light). Keep shadows hue-shifted (the palette already does) and avoid pure black.

### Skeleton and animation

`Rig.joint(name, parent, offset)`; a pose maps joint names to `(rx, ry, rz)` degrees; `Rig.solve(pose, base)` returns
4x4 matrices; attach parts with `shape.xform(W[joint])`. Swinging a limb in the side view is `rz` (positive = forward
for a limb pointing down). `ik2(base, target, l1, l2, bend)` solves two-bone legs/arms in the xy plane (plant feet
with it so they do not slide). `keys([(t, value), ...], t)` interpolates numbers, tuples or dicts with smoothstep.
Squash and stretch: `render(..., squash=(sx, sy), pivot=(x, y))`.

### Render and pixelize

`render(parts, size, anchor, ss=4)` returns a `Raster` (supersampled colour, material, part, depth, normal, glow
buffers). You can edit it before `pixelize`: `Raster.erase(mask)`, `Raster.overlay(other, zmode)`.
`Part(shape, shade=-1)` darkens a far limb one step; `Part(..., zbias=30)` draws a part in front of parts it really
lies behind (an arm raised in front of a big head); `Part(..., inner=False)` skips inner lines on it.

`pixelize(raster, cov=7, clean=True, inner=True, outline=True, keep_single=False)`: `cov` = how many of 16 samples
must be covered for a pixel to be opaque (lower keeps thin parts), `inner` = dark lines where a nearer part overlaps
a farther one, `keep_single=True` keeps lone pixels (sparks, embers). The result is a `Sprite`: `put(x, y, colour,
glow)` for hand touches (glints, sparkles, icons), `paste`, `shifted`, `bbox`, `rgba()`, `glow_rgba()`.
`outline_sprite(spr, colour)` outlines hand-drawn frames.

For 32 px sprites render at `ss=6` (more samples per pixel, cleaner small shapes).

### 2D effects

`Canvas(size, anchor, ss=4)` has world coordinate grids `X`, `Y` (y up) and distance helpers (`circle`, `ellipse`,
`capsule`, `rect`, `polygon`, `star`, `polar`); `fill(mask, colour, glow=..., line=False)` paints in order (later on
top). Use stepped bands (one fill per colour, outer to inner), never blends. `vnoise` / `fbm` give value noise for
ragged edges and dissolving smoke. Overlay a canvas on a 3D render with `raster.overlay(canvas)`; put it behind with
`canvas.z[canvas.col >= 0] = -1e6; raster.overlay(canvas, zmode=True)`.

### Sheet

`Sheet(name, (w, h), anchor, cols=16, title=...)`, `sh.point(name, dx, dy, note)` (offset from the anchor, y down,
facing right), `sh.note(text)` (comment line in the .txt), `sh.anim(name, fps, "loop"|"once", [Sprite or index...],
note=...)` (indices may repeat to hold a frame), `sh.write()` (PNG, .txt, _glow.png only if something glows,
previews, validation).

## Lessons from the existing sheets

* Judge everything at 1x on the scene preview. Contact sheets at 3-5x hide readability problems.
* A 3/4 side view (the hero is yawed -38 degrees) shows faces and visors but foreshortens forward motion: the hero
  counter-turns his hips (`leg_ry`) so leg swings stay wide, and turns the cannon arm side-on (`gun_ry`).
* Big round heads hide anything raised in front of them: raise arms over the side of the head that has no face
  detail, and use `zbias` to draw them on top.
* Anything that must glow at 1x (muzzles, lights) must be at least 2 px wide **from the side** and have `prio` >= 2,
  or the majority filter drops it.
* Effects drawn into a canvas get an outline unless `line=False`; light beams and sparks should not have one, solid
  projectiles should.
* Same-colour neighbours merge: give touching parts different materials (white arm against orange torso) instead of
  relying on inner lines.
