"""Spreads the enemy kinds across the levels and places the four kinds of the third round (one-off: the levels are
hand-maintained; run it once, then check with KeplerTool checkall and the autopilot).

    python tools/levels/spread_enemies.py [--dry]

Per level (boss levels left alone): the kinds of its episode it lacks join it by turning some of the placements of
its most frequent kind of the same movement class (ground, air, ceiling, fixed) into them, until the level has 4-6
kinds by its stage; spawners only where there is room; in episode 4 every third trooper of a crowded level becomes a
gloamhound, shieldbot or brute. New: mirror bots (episode 1 from level 3), shard snipers (episode 3 from level 2),
brine eels above the pools of episode 2, deck guards on the moving platforms of episode 4. Only enemy placements and
empty cells change, never terrain; placements with flags (ambush, elite, ceiling) are kept as they are.
"""
import argparse
import collections
import glob
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FIXED = set(" .#%-_BX^v<>~*$+H&kKdD?PEC")
EMPTY = set(" .")
SPARE = "abcdefghijlmnopqrstuwxyzAFGIJLMNOQRSTUVWYZ0123456789!=;:,"

CLASS = {}
for k in ("sweeper sentry rammer springbot beetle leaper stalker crystalcrab shardling minerbot frostgolem burrower trooper "
          "shieldbot gloamhound brute mirrorbot shardsniper").split():
    CLASS[k] = "ground"
for k in "hoverdrone sparkmine mothling sporepod wisp jetpacker blinker".split():
    CLASS[k] = "air"
for k in "icebat snapvine".split():
    CLASS[k] = "ceiling"
for k in "turret cryoturret lasereye spitter".split():
    CLASS[k] = "fixed"
for k in "fabricator hivenest riftgate".split():
    CLASS[k] = "spawner"

POOL = {1: "sweeper sentry hoverdrone turret sparkmine rammer springbot fabricator".split(),
        2: "beetle spitter mothling leaper snapvine sporepod stalker hivenest".split(),
        3: "crystalcrab icebat shardling cryoturret minerbot burrower frostgolem wisp".split(),
        4: "trooper shieldbot jetpacker gloamhound lasereye blinker brute riftgate".split()}
TARGET = {1: 3, 2: 4, 3: 5, 4: 5, 5: 5, 6: 6, 7: 6, 8: 6, 10: 6}


class Lvl:
    def __init__(self, path):
        self.path = path
        raw = open(path, "rb").read().decode("utf-8")
        self.crlf = "\r\n" in raw
        lines = raw.replace("\r\n", "\n").split("\n")
        m = lines.index("map")
        end = lines.index("end", m) if "end" in lines[m:] else len(lines)
        self.head, self.rows, self.tail = lines[:m + 1], [list(r) for r in lines[m + 1:end]], lines[end:]
        while self.rows and not self.rows[-1]:
            self.rows.pop()
            self.tail.insert(0, "")
        self.legend = {}   # char -> words after the char
        for l in self.head:
            w = l.split()
            if len(w) >= 3 and w[0] == "legend":
                self.legend[w[1]] = w[2:]
        self.added = []

    def at(self, x, y):
        return self.rows[y][x] if 0 <= y < len(self.rows) and 0 <= x < len(self.rows[y]) else "#"

    def put(self, x, y, ch):
        while len(self.rows[y]) <= x:
            self.rows[y].append(" ")
        self.rows[y][x] = ch

    def plain_enemy(self, ch):
        """The kind of a plain enemy legend (no flags but 'left'), else None."""
        w = self.legend.get(ch)
        if not w or w[0] != "enemy" or len(w) < 2:
            return None
        return w[1] if all(f == "left" for f in w[2:]) else None

    def kind_of(self, ch):
        w = self.legend.get(ch)
        return w[1] if w and w[0] == "enemy" and len(w) >= 2 else None

    def placements(self):
        """kind -> [(x, y, char)] of every enemy placement."""
        out = collections.defaultdict(list)
        for y, r in enumerate(self.rows):
            for x, ch in enumerate(r):
                k = self.kind_of(ch)
                if k:
                    out[k].append((x, y, ch))
        return out

    def char_for(self, kind):
        """A legend char for a plain enemy of this kind (an existing one, else a new one)."""
        for ch, w in self.legend.items():
            if w == ["enemy", kind]:
                return ch
        used = set(self.legend) | {c for r in self.rows for c in r} | FIXED
        for ch in SPARE:
            if ch not in used:
                self.legend[ch] = ["enemy", kind]
                self.added.append("legend %s  enemy %s" % (ch, kind))
                return ch
        raise RuntimeError("no free char in " + self.path)

    def movers(self):
        """[(x0, y, width)] of every mover run in the map."""
        out = []
        for y, r in enumerate(self.rows):
            x = 0
            while x < len(r):
                w = self.legend.get(r[x])
                if w and w[0] == "mover":
                    x0, ch = x, r[x]
                    while x < len(r) and r[x] == ch:
                        x += 1
                    out.append((x0, y, x - x0))
                else:
                    x += 1
        return out

    def write(self):
        head = list(self.head)
        m = head.index("map")
        last = max([i for i, l in enumerate(head[:m]) if l.startswith("legend")] or [m - 1])
        head[last + 1:last + 1] = self.added
        text = "\n".join(head + ["".join(r) for r in self.rows] + self.tail)
        if self.crlf:
            text = text.replace("\n", "\r\n")
        open(self.path, "wb").write(text.encode("utf-8"))


# Kinds that knock the hero about (charges, grenades): never next to a pit of liquid or spikes.
PUSHERS = {"brute", "gloamhound", "rammer", "stalker", "frostgolem"}


def near_hazard(lv, x, y):
    return any(lv.at(x + dx, y + dy) in "~^v" for dx in range(-8, 9) for dy in range(-1, 4))


def convert(lv, kind, to, n, log, only_plain=True):
    """Turns n of the plain placements of kind (spread over the level) into to."""
    places = [p for p in lv.placements().get(kind, []) if ( not only_plain or lv.plain_enemy(p[2]) ) and
              not ( to in PUSHERS and near_hazard(lv, p[0], p[1]) )]
    if not places:
        return 0
    n = min(n, len(places))
    picks = [places[int((i + 0.5) * len(places) / n)] for i in range(n)]
    ch = lv.char_for(to)
    for x, y, _ in picks:
        lv.put(x, y, ch)
    log.append("%s %d->%s" % (kind, n, to))
    return n


def room(lv, x, y):
    """Room for a spawner (2 x 2 cells empty around the placement)."""
    return all(lv.at(x + dx, y + dy) in EMPTY or (dx == 0 and dy == 0) for dx in (-1, 0, 1) for dy in (-1, 0))


def spread(lv, ep, stage, levels_with):
    log = []
    target = TARGET.get(stage, 5)
    pool = POOL[ep]
    for _ in range(12):
        pl = lv.placements()
        present = set(pl)
        if len(present & set(pool)) >= target:
            break
        missing = sorted((k for k in pool if k not in present), key=lambda k: len(levels_with[k]))
        done = False
        for cand in missing:
            c = CLASS[cand]
            if c == "spawner":
                if stage < 4 or any(CLASS[k] == "spawner" for k in present):
                    continue
                donors = [(len(v), k) for k, v in pl.items() if CLASS.get(k) == "ground" and len(v) >= 3]
                for _, k in sorted(donors, reverse=True):
                    spots = [p for p in pl[k] if lv.plain_enemy(p[2]) and room(lv, p[0], p[1])]
                    if spots:
                        x, y, _ = spots[len(spots) // 2]
                        lv.put(x, y, lv.char_for(cand))
                        log.append("%s 1->%s" % (k, cand))
                        done = True
                        break
            else:
                donors = sorted(((len(v), k) for k, v in pl.items() if CLASS.get(k) == c and len(v) >= 2), reverse=True)
                for cnt, k in donors:
                    if convert(lv, k, cand, max(1, min(3, cnt // 3)), log):
                        done = True
                        break
            if done:
                levels_with[cand].add(lv.path)
                break
        if not done:
            break
    if ep == 4:
        tr = [p for p in lv.placements().get("trooper", []) if lv.plain_enemy(p[2])]
        if len(tr) > 6:
            subs = ["gloamhound", "shieldbot", "brute"]
            for i, (x, y, _) in enumerate(tr[1::3]):
                sub = subs[i % 3]
                lv.put(x, y, lv.char_for("shieldbot" if sub in PUSHERS and near_hazard(lv, x, y) else sub))
            log.append("trooper %d->hound/shieldbot/brute" % len(tr[1::3]))
    return log


def place_new(lv, ep, stage, log):
    pl = lv.placements()
    if ep == 1 and stage >= 3:
        donor = "sentry" if len(pl.get("sentry", [])) >= 2 else "sweeper"
        convert(lv, donor, "mirrorbot", 2, log)
    if ep == 3 and stage >= 2:
        donor = "minerbot" if len(pl.get("minerbot", [])) >= 2 else "crystalcrab"
        convert(lv, donor, "shardsniper", 2 if stage < 6 else 3, log)
    if ep == 2:
        # Above the pools: the middle of each run of surface cells at least 3 wide (at most 3 eels).
        runs = []
        for y in range(1, len(lv.rows)):
            x = 0
            row = lv.rows[y]
            while x < len(row):
                if row[x] == "~" and lv.at(x, y - 1) in EMPTY:
                    x0 = x
                    while x < len(row) and row[x] == "~" and lv.at(x, y - 1) in EMPTY:
                        x += 1
                    if x - x0 >= 3:
                        runs.append((x - x0, x0, y))
                else:
                    x += 1
        runs.sort(reverse=True)
        n = 0
        for w, x0, y in runs[:3]:
            lv.put(x0 + w // 2, y - 1, lv.char_for("brineeel"))
            n += 1
        if n:
            log.append("brineeel +%d" % n)
    if ep == 4:
        n = 0
        for x0, y, w in lv.movers():
            if n >= 3 or y < 1 or w < 2:
                continue
            x = x0 + w // 2
            if lv.at(x, y - 1) in EMPTY:
                lv.put(x, y - 1, lv.char_for("deckguard"))
                n += 1
        if n:
            log.append("deckguard +%d" % n)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()
    paths = sorted(glob.glob(os.path.join(ROOT, "assets", "levels", "e[1-4]*.txt")))
    levels = {p: Lvl(p) for p in paths}
    levels_with = collections.defaultdict(set)
    for p, lv in levels.items():
        for k in lv.placements():
            levels_with[k].add(p)
    for p, lv in levels.items():
        lid = os.path.basename(p)[:-4]
        ep = int(lid[1])
        stage = 10 if lid.endswith("s") else int(lid[3:])
        if stage == 9:
            continue
        before = sorted(lv.placements())
        log = spread(lv, ep, stage, levels_with)
        place_new(lv, ep, stage, log)
        after = sorted(lv.placements())
        print("%-5s %d -> %d kinds  %s" % (lid, len(before), len(after), "; ".join(log)))
        if not a.dry:
            lv.write()


if __name__ == "__main__":
    main()
