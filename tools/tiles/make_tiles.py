"""Generates the tile sets of Kip Kepler into assets/tiles/<theme>/.

    python tools/tiles/make_tiles.py                 # all eight themes
    python tools/tiles/make_tiles.py station ice     # just these
    python tools/tiles/make_tiles.py station --only terrain_a back

Per theme: terrain_a.png, terrain_b.png, back.png (16 x 64 autotiles, index = variant * 256 + mask), platform.png,
blocks.png, liquid.png, deco.png + deco.txt, tints.txt, and <sheet>_glow.png for every sheet with emissive pixels.
Everything is deterministic (fixed seeds), CPU only.
"""
import argparse
import importlib
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tilelib import ROOT, autotile_sheet, grid_sheet, pack_atlas, save_sheet  # noqa: E402

THEMES = ["station", "hull", "jungle", "hive", "ice", "crystal", "foundry", "citadel"]
PARTS = ["terrain_a", "terrain_b", "back", "platform", "blocks", "liquid", "deco", "tints"]


def build(theme, only=None):
    mod = importlib.import_module("theme_" + theme)
    out = os.path.join(ROOT, "assets", "tiles", theme)
    os.makedirs(out, exist_ok=True)
    done = []
    for part in PARTS:
        if only and part not in only:
            continue
        t0 = time.time()
        if part in ("terrain_a", "terrain_b", "back"):
            fn = getattr(mod, part, None)
            if fn is None:
                continue
            sheet = autotile_sheet(fn)
            g = save_sheet(sheet, os.path.join(out, part + ".png"))
        elif part in ("platform", "blocks", "liquid"):
            fn = getattr(mod, part, None)
            if fn is None:
                continue
            rows = fn()
            sheet = grid_sheet(rows, 4)
            g = save_sheet(sheet, os.path.join(out, part + ".png"))
        elif part == "deco":
            fn = getattr(mod, "deco", None)
            if fn is None:
                continue
            items = fn()
            sheet, lines = pack_atlas(items)
            g = save_sheet(sheet, os.path.join(out, "deco.png"))
            with open(os.path.join(out, "deco.txt"), "w", encoding="utf-8", newline="\n") as f:
                f.write("\n".join(lines) + "\n")
        else:
            tints = getattr(mod, "TINTS", None)
            if tints is None:
                continue
            with open(os.path.join(out, "tints.txt"), "w", encoding="utf-8", newline="\n") as f:
                for tn in tints:
                    f.write("%d %d %d %d %d %s\n" % tn)
            g = False
        done.append("%s%s (%.1fs)" % (part, "+glow" if g else "", time.time() - t0))
    print(theme + ": " + ", ".join(done))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("themes", nargs="*", help="themes to build (default: all)")
    ap.add_argument("--only", nargs="*", help="only these parts: " + " ".join(PARTS))
    a = ap.parse_args()
    themes = a.themes or THEMES
    for th in themes:
        if th not in THEMES:
            sys.exit("unknown theme %s (themes: %s)" % (th, " ".join(THEMES)))
    for th in themes:
        build(th, a.only)


if __name__ == "__main__":
    main()
