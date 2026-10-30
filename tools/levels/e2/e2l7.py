"""e2l7 Amber Tunnels -- deep in the hive: vertical shafts, movers, snapvines.

Five tunnel levels (floors 13, 31, 49, 67, 79) on both sides of the Amber Well, a huge open shaft over a lake of resin.
Route: the top tunnel (west) -> elevator down the west shaft -> tunnel 1: movers across the well -> tunnel 1 east ->
log ladder down the east shaft -> tunnel 2 east (checkpoint) -> log hops across the well -> tunnel 2 west -> elevator
down -> tunnel 3: crumble bridge and the amber pillar across the well -> tunnel 3 east -> ladder down -> the bottom
tunnel (checkpoint) -> movers over the resin to the bottom west tunnel and its elevator, or east to the exit.
Every level links up and down both ways (elevators, ladders, movers), so the whole hive can be walked again.
Secrets: a cell behind a fake wall at the top tunnel's west end, a niche behind breakable comb in tunnel 2 west,
an alcove in the well's wall above the bottom movers.
"""
from lvl import Map, run, stats, ladder

W, H = 160, 84
m = Map(W, H, "#")


def log(x0, x1, y):
    m.hline(x0, x1, y, "-")


def crumble(x0, x1, y):
    m.hline(x0, x1, y, "_")


FLOORS = [13, 31, 49, 67, 79]
# ---------------------------------------------------------------- tunnels (rows floor-7 .. floor-1)
for f in FLOORS:
    top = f - 7 if f != 79 else f - 6
    m.rect(3, top, 59, f - 1, ".")
    m.rect(101, top, 156, f - 1, ".")
# rock teeth along the tunnel roofs (x0, x1, rows)
teeth = {
    13: ((8, 11, 2), (40, 43, 1), (56, 59, 2), (104, 108, 2), (118, 121, 1), (134, 137, 2), (150, 153, 1)),
    31: ((16, 19, 1), (32, 35, 2), (48, 51, 1), (106, 109, 2), (128, 131, 1), (148, 151, 2)),
    49: ((8, 11, 2), (24, 27, 1), (42, 45, 2), (114, 117, 2), (126, 129, 1), (144, 147, 2)),
    67: ((14, 17, 2), (30, 33, 1), (54, 57, 2), (106, 109, 1), (122, 125, 2), (136, 139, 1)),
    79: ((20, 23, 1), (38, 41, 2), (54, 57, 1), (108, 111, 2), (130, 133, 1), (148, 151, 1)),
}
for f, row in teeth.items():
    top = f - 7 if f != 79 else f - 6
    for x0, x1, n in row:
        m.rect(x0, top, x1, top + n - 1, "#")
# comb patches in the rock between the tunnels
for x0, y0, x1, y1 in ((3, 14, 30, 17), (40, 32, 59, 35), (101, 50, 125, 53), (130, 14, 156, 17), (3, 68, 25, 71),
                       (110, 32, 140, 34), (30, 50, 50, 53), (120, 68, 150, 71), (3, 81, 156, 83)):
    m.rect(x0, y0, x1, y1, "%")

# ---------------------------------------------------------------- the Amber Well (open shaft, resin rows 79-80)
m.rect(60, 3, 100, 78, " ")
m.rect(60, 79, 100, 80, "~")
# top: a log bridge with a crumble stretch
log(60, 70, 13)
crumble(71, 76, 13)
log(77, 89, 13)
crumble(90, 93, 13)
log(94, 100, 13)
# tunnel 1: two movers and an island
m.rect(78, 31, 82, 32, "%")
m.put(61, 31, "===")                        # mover A
m.put(83, 31, ";;;")                        # mover B
# tunnel 2: log hops
for x0, x1, y in ((60, 64, 49), (67, 71, 46), (74, 78, 49), (81, 85, 46), (88, 92, 49), (94, 97, 46), (98, 100, 49)):
    log(x0, x1, y)
# tunnel 3: crumble bridges and the amber pillar
crumble(60, 69, 67)
m.rect(70, 64, 76, 65, "%")
crumble(77, 86, 67)
m.rect(87, 64, 90, 65, "%")
crumble(91, 100, 67)
# bottom: movers over the resin, an island
m.rect(78, 79, 82, 80, "%")
m.put(61, 79, "[[[")                        # mover C
m.put(83, 79, "]]]")                        # mover D
# hanging comb in the well
for x0, x1, y0, y1 in ((66, 72, 3, 6), (86, 94, 3, 5), (60, 62, 20, 26), (98, 100, 36, 41), (60, 61, 54, 58)):
    m.rect(x0, y0, x1, y1, "%")

# ---------------------------------------------------------------- shafts between the levels
# west shaft 1 (top <-> 1): an elevator
m.rect(20, 13, 24, 31, ".")
m.put(21, 31, "|||")
# east shaft (1 <-> 2): a log ladder
m.rect(120, 31, 124, 41, ".")
ladder(m, 120, 122, 49, 31, 3)
# west shaft 2 (2 <-> 3): an elevator
m.rect(36, 49, 40, 67, ".")
m.put(37, 67, "{{{")
# east shaft 2 (3 <-> bottom): a log ladder
m.rect(140, 67, 144, 72, ".")
ladder(m, 140, 142, 79, 67, 3)
# west shaft 3 (3 <-> bottom): an elevator
m.rect(10, 67, 14, 72, ".")
m.put(11, 79, "(((")
m.rect(10, 79, 14, 79, "(")
m.rect(10, 79, 10, 79, ".")
m.rect(14, 79, 14, 79, ".")

# ---------------------------------------------------------------- inside the tunnels: pits, pockets, blocks
# top tunnel
m.rect(30, 13, 33, 14, "~")
log(28, 35, 10)
m.rect(44, 10, 46, 12, "%")
m.rect(110, 13, 113, 14, "~")
m.rect(128, 11, 130, 12, "%")
log(140, 145, 10)
# tunnel 1
m.rect(40, 31, 43, 32, "~")
crumble(40, 43, 31)
m.rect(8, 22, 14, 23, ".")
log(9, 13, 28)
m.rect(132, 31, 135, 32, "~")
m.rect(145, 29, 147, 30, "%")
log(140, 143, 27)
# tunnel 2
m.rect(18, 49, 21, 50, "~")
m.rect(46, 47, 48, 48, "%")
m.rect(106, 40, 112, 41, ".")
log(107, 111, 45)
m.rect(140, 49, 143, 50, "~")
crumble(140, 143, 49)
# tunnel 3
m.rect(26, 67, 29, 68, "~")
m.rect(48, 65, 50, 66, "%")
m.rect(112, 67, 116, 68, "^")
m.rect(112, 67, 116, 67, ".")
crumble(112, 116, 66)
m.rect(150, 58, 156, 59, ".")
log(150, 154, 63)
# bottom tunnel
m.rect(30, 79, 33, 80, "~")
m.rect(46, 77, 48, 78, "%")
m.rect(120, 79, 124, 80, "~")
log(119, 125, 76)
# secret 1: a cell behind a fake wall at the top tunnel's west end
m.rect(3, 6, 3, 12, "#")
m.rect(3, 11, 3, 12, "X")
m.rect(1, 8, 2, 12, "?")
# secret 3: a cell behind a fake wall at the east end of tunnel 3
m.rect(157, 65, 157, 66, "X")
m.rect(158, 61, 159, 66, "?")
# secret 2: a niche behind breakable comb in tunnel 2 west
m.rect(3, 47, 3, 48, "B")
m.rect(3, 42, 3, 46, "#")
m.rect(1, 44, 2, 48, "?")

# ---------------------------------------------------------------- items
crystals = [
    (52, 12), (115, 12), (150, 12), (80, 12),
    (11, 27), (48, 30), (80, 30), (108, 30), (146, 28),
    (25, 48), (50, 48), (83, 45), (109, 44), (152, 48),
    (8, 66), (49, 64), (73, 63), (88, 63), (130, 66), (152, 62),
    (22, 78), (52, 78), (80, 78), (110, 78),
]
for x, y in crystals:
    m.set(x, y, "*")
treasure = [
    (10, 12), (12, 12), (29, 9), (31, 9), (33, 9), (38, 12), (62, 12), (66, 12), (73, 12), (85, 12), (96, 12),
    (106, 12), (118, 12), (122, 12), (141, 9), (143, 9), (154, 12),
    (6, 30), (16, 30), (10, 21), (12, 21), (30, 30), (41, 30), (42, 30), (54, 30), (65, 28), (70, 28), (88, 28),
    (93, 28), (104, 30), (116, 30), (133, 30), (134, 30), (141, 26), (142, 26), (152, 30),
    (8, 48), (14, 48), (30, 48), (44, 48), (56, 48), (62, 48), (69, 45), (76, 48), (90, 48), (96, 45), (108, 39),
    (110, 39), (116, 48), (130, 48), (141, 48), (142, 48),
    (16, 66), (20, 66), (34, 66), (44, 66), (56, 66), (64, 66), (66, 66), (72, 63), (80, 66), (82, 66),
    (94, 66), (96, 66), (106, 66), (114, 65), (122, 66), (138, 66), (151, 62), (153, 57), (154, 57),
    (6, 78), (18, 78), (40, 78), (56, 78), (64, 76), (70, 76), (90, 76), (96, 76), (106, 78), (121, 75),
    (123, 75), (132, 78), (146, 78),
]
for x, y in treasure:
    if m.get(x, y) in ". ":
        m.set(x, y, "$")
for x, y in [(1, 12), (2, 12)]:                                            # secret 1
    m.set(x, y, "$")
m.set(1, 10, "&")
for x, y in [(1, 48), (2, 48)]:                                            # secret 2
    m.set(x, y, "$")
m.set(2, 47, "H")
m.set(2, 46, "w")                                                          # overdrive
for x, y in [(158, 66), (159, 65)]:                                        # secret 3
    m.set(x, y, "$")
m.set(159, 66, "i")
m.set(159, 64, "q")                                                        # shield

for x, y in [(18, 12), (100, 12), (24, 30), (58, 30), (102, 30), (102, 48), (58, 48), (6, 66), (102, 66),
             (58, 78), (104, 78), (138, 78)]:
    if m.get(x, y) in ". ":
        m.set(x, y, "+")
for x, y in [(14, 12), (56, 12), (126, 12), (34, 30), (128, 30), (12, 48), (128, 48), (42, 66), (126, 66),
             (8, 78), (128, 78), (150, 78)]:
    if m.get(x, y) in ". ":
        m.set(x, y, "&")

# ---------------------------------------------------------------- objects
m.set(6, 12, "P")
m.set(17, 12, "t")       # sign: elevators
m.set(104, 48, "C")      # checkpoint in tunnel 2 east
m.set(146, 78, "C")      # checkpoint in the bottom tunnel east
m.set(153, 78, "E")

# ---------------------------------------------------------------- enemies
for x, y in [(38, 6), (52, 6), (122, 6), (12, 24), (30, 24), (46, 24), (112, 24), (138, 24), (16, 42),
             (28, 42), (118, 42), (148, 42), (20, 60), (40, 60), (132, 60), (146, 60), (36, 73), (112, 73),
             (130, 73)]:
    if m.get(x, y) == ".":
        m.set(x, y, "n")     # snapvines from the tunnel roofs
for x, y in [(75, 20), (88, 24), (70, 38), (92, 40), (66, 56), (94, 58), (78, 72)]:
    if m.get(x, y) == " ":
        m.set(x, y, "m")     # mothlings in the well
for i, (x, y) in enumerate([(48, 12), (136, 12), (52, 30), (150, 30), (22, 48), (132, 48), (18, 66), (140, 66),
                            (26, 78), (116, 78), (8, 30), (154, 48)]):
    if m.get(x, y) in ". ":
        m.set(x, y, "b" if i % 2 == 0 else "j")    # beetles and leapers in the tunnels
for x, y in [(80, 30), (95, 45), (149, 62), (75, 63)]:
    if m.get(x, y) in ". ":
        m.set(x, y, "y")     # spitters on islands and ledges
for x, y in [(30, 12), (112, 30), (60, 66)]:
    if m.get(x, y) in ". ":
        m.set(x, y, "J")

legend = [
    ("n", "enemy snapvine"),
    ("m", "enemy mothling"),
    ("b", "enemy beetle"),
    ("j", "enemy leaper"),
    ("J", "enemy leaper ambush"),
    ("y", "enemy spitter"),
    ("=", "mover 13 0 80"),
    (";", "mover 14 0 80"),
    ("[", "mover 14 0 70"),
    ("]", "mover 14 0 70"),
    ("|", "mover 0 -18 90 1.0"),
    ("{", "mover 0 -18 90 1.0"),
    ("(", "mover 0 -12 80 1.0"),
    ("w", "power overdrive"),
    ("q", "power shield"),
    ("i", "treasure idol"),
    ("t", "sign sign.e2l7.elevator"),
]
header = [
    "# e2l7 Amber Tunnels -- built by tools/levels/e2/e2l7.py",
    "name      Amber Tunnels",
    "name.de   Bernsteintunnel",
    "theme     hive",
    "tint      1",
    "bg        hive_b",
    "music     e2_hive",
    "dark      0.3",
    "par       480",
]
m.save("e2l7", header, legend)
print(stats(m, legend))
run("e2l7", parts=[(0, 2, 60, 32), (56, 2, 48, 82), (100, 2, 60, 50), (0, 40, 60, 44), (100, 40, 60, 44)])
