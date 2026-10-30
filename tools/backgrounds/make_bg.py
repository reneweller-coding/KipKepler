"""Makes Kip Kepler's parallax backgrounds: assets/bg/<name>/layer0-3.png (+ glow masks) and bg.txt, plus previews
in work/bg/.

    python tools/backgrounds/make_bg.py                 # all 16
    python tools/backgrounds/make_bg.py station_a hull_b
    python tools/backgrounds/make_bg.py --list
    python tools/backgrounds/make_bg.py --no-preview station_a
    python tools/backgrounds/make_bg.py --fore             # only the foreground layers (fore.png + the fore line)
    python tools/backgrounds/make_bg.py --fore ice_a

Every background is a function in scenes_e<N>.py that returns (layers, specs, notes); the seed is fixed per name,
so a run always produces the same pictures. The foreground layer in front of the gameplay comes from fore.py (one
function per theme); a full run makes it too, so bg.txt keeps its fore line.
"""
import argparse
import sys
import time
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bgkit  # noqa: E402
import fore  # noqa: E402
import scenes_e1  # noqa: E402
import scenes_e2  # noqa: E402
import scenes_e3  # noqa: E402
import scenes_e4  # noqa: E402

SCENES = {}
for mod in (scenes_e1, scenes_e2, scenes_e3, scenes_e4):
    SCENES.update(mod.SCENES)


def make(name, previews=True):
    """Builds, checks and writes one background."""
    seed = zlib.crc32(name.encode())
    layers, specs, notes = SCENES[name](seed)
    bgkit.finish(layers)
    out = bgkit.save(name, layers, specs, notes)
    if previews:
        bgkit.preview(name, layers, specs)
        bgkit.seams(name, layers)
        bgkit.layers_sheet(name, layers)
    make_fore(name, previews)
    return out


def make_fore(name, previews=True):
    """Builds, checks and writes one foreground layer (fore.png and the fore line in bg.txt)."""
    out, probs, st = fore.make(name, previews)
    print(f"  fore {name}: {st['verticals']} verticals, top {st['top']:.0%} / bottom {st['bottom']:.0%} covered, "
          f"middle {st['middle']:.2%}" + ("" if not probs else "  PROBLEMS: " + "; ".join(probs)))
    return not probs


def overview(names):
    """work/bg/_overview.png: the first preview view of every background, half size, four per row."""
    import numpy as np
    from PIL import Image
    tiles = []
    for n in names:
        p = bgkit.ROOT / "work" / "bg" / f"{n}_preview.png"
        if p.exists():
            im = Image.open(p).convert("RGB").crop((0, 0, 640, 400)).resize((320, 200), Image.NEAREST)
            tiles.append(np.asarray(im))
    if not tiles:
        return None
    while len(tiles) % 4:
        tiles.append(np.zeros_like(tiles[0]))
    rows = [np.concatenate(tiles[i:i + 4], 1) for i in range(0, len(tiles), 4)]
    out = bgkit.ROOT / "work" / "bg" / "_overview.png"
    Image.fromarray(np.concatenate(rows, 0)).save(out)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("names", nargs="*", help="backgrounds to make (default: all)")
    ap.add_argument("--list", action="store_true", help="list the backgrounds")
    ap.add_argument("--no-preview", action="store_true", help="skip the work/bg previews")
    ap.add_argument("--fore", action="store_true", help="only the foreground layers (fore.png + the fore line)")
    args = ap.parse_args()
    if args.list:
        print("\n".join(SCENES))
        return
    names = args.names or list(SCENES)
    for n in names:
        if n not in SCENES:
            sys.exit(f"unknown background {n!r}; known: {', '.join(SCENES)}")
    if args.fore:
        ok = True
        for n in names:
            ok &= make_fore(n, not args.no_preview)
        if not args.no_preview:
            print(f"overview: {fore.overview(list(SCENES))}")
        sys.exit(0 if ok else 1)
    for n in names:
        t = time.time()
        out = make(n, not args.no_preview)
        print(f"{n}: {out} ({time.time() - t:.1f} s)")
    if not args.no_preview and len(names) > 1:
        print(f"overview: {overview(list(SCENES))}")


if __name__ == "__main__":
    main()
