"""Paints the story's stills: tools/story/stills.json -> FLUX.2 locally in WSL (flux_wsl.py, GPU) -> work/story/<name>.png
-> pixelated to 320 x 180 in the game's palette -> assets/story/<name>.png (the story page story.<name with .>
shows it, e.g. e1_intro_2 above story.e1.intro.2).

    python tools/story/make_stills.py paint      # FLUX (GPU; respects G:/Tools/Games/GPU_BELEGT.txt)
    python tools/story/make_stills.py pixel      # CPU: the pixel versions from work/story
    python tools/story/make_stills.py sheet      # a contact sheet into work/story/sheet.png
"""
import json
import os
import subprocess
import sys

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from common.palette import palette  # noqa: E402

WORK = os.path.join(ROOT, "work", "story")
OUT = os.path.join(ROOT, "assets", "story")
STYLE = ("Detailed 2D pixel art illustration for a cheerful retro science fiction video game cutscene, crisp pixels, "
         "vibrant limited palette, clean readable shapes, cinematic wide composition, no text, no letters, no logos. ")


def linux(path):
    path = path.replace("\\", "/")
    return "/mnt/%s/%s" % (path[0].lower(), path[3:]) if len(path) > 2 and path[1] == ":" else path


def paint():
    spec = json.load(open(os.path.join(ROOT, "tools", "story", "stills.json"), encoding="utf-8"))
    os.makedirs(WORK, exist_ok=True)
    tasks = []
    for i, (name, prompt) in enumerate(spec.items()):
        tasks.append({"prompt": STYLE + prompt, "out": os.path.join(WORK, name + ".png").replace("\\", "/"),
                      "width": 1344, "height": 768, "seed": 4100 + i})
    path = os.path.join(WORK, "tasks.json")
    json.dump(tasks, open(path, "w", encoding="utf-8"), indent=1)
    script = linux(os.path.join(ROOT, "tools", "story", "flux_wsl.py"))
    cmd = ["wsl", "-d", "Ubuntu-22.04", "--", "/home/rene/miniconda3/envs/flux/bin/python", script, linux(path)]
    print(" ".join(cmd))
    subprocess.run(cmd, check=True)


def pixel():
    """Box-downsample to 320 x 180, then every pixel to the nearest palette colour (no dithering), then lone pixels
    folded into their neighbours: the painting becomes pixel art in the game's colours."""
    os.makedirs(OUT, exist_ok=True)
    pal = palette().astype(np.float32)
    w8 = np.array([0.30, 0.59, 0.11], dtype=np.float32) * 3
    for f in sorted(os.listdir(WORK)):
        if not f.endswith(".png") or f == "sheet.png":
            continue
        img = Image.open(os.path.join(WORK, f)).convert("RGB")
        w, h = img.size
        th = int(w * 9 / 16)
        img = img.crop((0, (h - th) // 2, w, (h - th) // 2 + th)).resize((320, 180), Image.BOX)
        a = np.asarray(img).astype(np.float32).reshape(-1, 3)
        d = (((a[:, None, :] - pal[None, :, :]) ** 2) * w8).sum(-1)
        idx = d.argmin(1).reshape(180, 320)
        # Lone pixels take the colour most of their neighbours have.
        for y in range(1, 179):
            for x in range(1, 319):
                c = idx[y, x]
                n = [idx[y - 1, x], idx[y + 1, x], idx[y, x - 1], idx[y, x + 1]]
                if c not in n:
                    idx[y, x] = max(set(n), key=n.count)
        out = pal[idx].astype(np.uint8)
        Image.fromarray(out, "RGB").save(os.path.join(OUT, f))
        print("pixel", f)


def sheet():
    files = sorted(f for f in os.listdir(OUT) if f.endswith(".png"))
    cols = 4
    rows = (len(files) + cols - 1) // cols
    s = Image.new("RGB", (cols * 330, rows * 190), (20, 20, 30))
    for i, f in enumerate(files):
        s.paste(Image.open(os.path.join(OUT, f)), ((i % cols) * 330 + 5, (i // cols) * 190 + 5))
    s.save(os.path.join(WORK, "sheet.png"))


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "pixel"
    {"paint": paint, "pixel": pixel, "sheet": sheet}[what]()
