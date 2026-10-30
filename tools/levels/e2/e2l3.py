"""e2l3 Canopy Bridges -- high in the canopy of Thessa: one-way bridges, bounce pods (springs), mothlings, a deadly fall.

Three tiers of canopy masses held up by roots: the middle tier (rows ~18-23) carries the route, bounce pods launch to
the high tier (crystals), the low tier (treasure, a few crystals) catches missed jumps and has pods back up. Pods are
placed for targets 4-6 rows above them; every step also works westward, so all of the level can be walked again.
Route: the cliff (fall sign) -> the bounce lesson (a pod is the only way on, missing it is harmless) -> first
mothlings -> the Great Tree (pods up its west branches to the crown: checkpoint) -> down the east branches -> the long
bridges (crumble bridge, mothlings, the second checkpoint) -> the exit tree.
Secrets: a hollow in the Great Tree's trunk (fake wall), a hidden ledge below the long bridges (leap of faith marked
by gems), a vault in the exit tree (fake wall).
"""
from lvl import Map, run, stats

W, H = 212, 46
m = Map(W, H, " ")


def mass(x0, top, x1, bottom, ch="#"):
    """A canopy mass: earth with a mossy top, its lowest row a little narrower (hanging roots)."""
    m.rect(x0, top, x1, bottom, ch)
    if x1 - x0 >= 4:
        m.set(x0, bottom, " ")
        m.set(x1, bottom, " ")


def log(x0, x1, y):
    m.hline(x0, x1, y, "-")


pods = []

# ---------------------------------------------------------------- zone A: the cliff and the bounce lesson
m.rect(0, 22, 12, H - 1, "#")               # the cliff
log(13, 18, 22)
mass(19, 22, 28, 26)
m.rect(24, 16, 28, 21, "#")                 # the tier: only a bounce pod gets you up
m.rect(25, 16, 28, 16, "%")
pods.append((22, 21))
log(29, 34, 18)
mass(35, 18, 43, 22)
m.rect(37, 17, 38, 17, "%")
mass(47, 20, 55, 24)                        # a 3-wide gap before it, 2 rows lower
mass(38, 26, 46, 28)                        # low: catches a short jump
pods.append((45, 25))
log(54, 61, 14)                             # high: a branch of the Great Tree
log(56, 60, 11)                             # and logs up to the crown
log(57, 61, 8)
pods.append((52, 19))

# ---------------------------------------------------------------- zone B: the Great Tree
m.rect(70, 10, 77, H - 1, "#")              # the trunk down into the abyss
m.rect(62, 7, 86, 9, "#")                   # the crown
m.rect(64, 6, 84, 6, "#")
m.set(62, 9, " ")
m.set(86, 9, " ")
log(60, 69, 20)                             # west branch (a gap of 4 before it: fall short and land below)
pods.append((60, 19))
mass(56, 26, 66, 28)                        # low: under the west branch
pods.append((65, 25))
# secret 1: a hollow in the trunk behind a fake wall at the west branch
m.rect(72, 16, 76, 19, "?")
m.rect(70, 18, 71, 19, "X")
# east branches: a ladder of logs down to the long bridges (and back up)
log(87, 90, 9)
log(86, 90, 12)
log(80, 85, 15)
log(87, 91, 18)
log(79, 86, 21)
mass(88, 22, 96, 26)

# ---------------------------------------------------------------- zone C: the long bridges
log(100, 107, 22)                           # gap 97-99 before it
mass(108, 21, 114, 25)
m.hline(115, 119, 21, "_")                  # crumble bridge
mass(120, 21, 127, 25)
log(131, 136, 23)                           # gap 128-130 before it
mass(137, 23, 145, 27)
log(111, 118, 15)                           # high
pods.append((113, 20))
log(124, 131, 15)
pods.append((126, 20))
mass(96, 28, 104, 30)                       # low, pod back up to the bridge
pods.append((102, 27))
mass(126, 29, 135, 31)                      # low, pod back up to the bridge
pods.append((134, 28))
# secret 2: a hidden ledge far below the long bridges, a gem trail shows the leap; a pod back up
mass(106, 34, 111, 36)
m.rect(107, 32, 110, 33, "?")
pods.append((106, 33))

# ---------------------------------------------------------------- zone D: to the exit tree
log(146, 149, 21)
mass(150, 19, 157, 23)
mass(157, 13, 163, 15)                      # high
pods.append((154, 18))
log(160, 165, 20)                           # gap 158-159 before it
mass(166, 20, 172, 24)
m.hline(173, 177, 20, "_")
mass(178, 19, 183, 23)
mass(157, 26, 165, 28)                      # low
pods.append((163, 25))
m.rect(187, 17, 194, H - 1, "#")            # the exit tree
m.rect(184, 16, 197, 18, "#")
m.set(184, 18, " ")
m.set(197, 18, " ")
# secret 3: a vault in the exit tree, through its east bark
m.rect(189, 20, 193, 23, "?")
m.rect(194, 22, 194, 23, "X")
mass(195, 24, 203, 27)                      # a ledge east of the exit tree, logs back up
log(199, 202, 22)
log(198, 201, 19)
mass(197, 30, 205, 33)                      # and a low one
pods.append((204, 29))
m.rect(207, 0, 211, H - 1, "#")             # the far cliff

for x, y in pods:
    m.set(x, y, "s")

# ---------------------------------------------------------------- items
crystals = [
    (26, 15), (40, 16), (40, 25), (57, 13), (58, 25),
    (68, 5), (80, 5), (88, 17), (100, 27),
    (110, 20), (116, 14), (129, 14), (130, 28), (141, 22),
    (160, 12), (161, 25), (169, 19), (199, 23), (201, 29),
]
for x, y in crystals:
    m.set(x, y, "*")
treasure = [
    (15, 21), (17, 21), (30, 17), (32, 17), (34, 17), (42, 16), (45, 18), (46, 18),
    (42, 25), (43, 25), (55, 13), (59, 13), (58, 10), (59, 7), (63, 19), (66, 19), (60, 25), (63, 25),
    (66, 5), (70, 5), (72, 5), (76, 5), (78, 5), (82, 5), (88, 8), (89, 11), (82, 14), (89, 17), (81, 20),
    (90, 21), (92, 21), (101, 21), (103, 21), (105, 21), (112, 20), (113, 14), (115, 14), (126, 14),
    (127, 14), (131, 22), (133, 22), (135, 22), (128, 28), (132, 28), (98, 27), (99, 27),
    (104, 26), (105, 29), (106, 31),                                   # the gem trail into secret 2
    (152, 18), (153, 18), (158, 12), (162, 12), (161, 19), (163, 19), (159, 25), (164, 25),
    (174, 19), (176, 19), (180, 18), (185, 15), (196, 23), (198, 23), (199, 20), (200, 20), (199, 29), (203, 29),
]
for x, y in treasure:
    if m.get(x, y) == " ":
        m.set(x, y, "$")
for x, y in [(73, 19), (74, 19), (75, 19)]:                                # secret 1
    m.set(x, y, "$")
m.set(76, 19, "&")
m.set(72, 19, "+")
for x, y in [(107, 33), (110, 33)]:                                        # secret 2
    m.set(x, y, "$")
m.set(108, 33, "c")
m.set(109, 33, "q")                                                         # shield
for x, y in [(190, 23), (191, 23), (192, 23)]:                             # secret 3
    m.set(x, y, "$")
m.set(193, 23, "H")
m.set(189, 23, "&")

for x, y in [(11, 21), (45, 26), (85, 14), (108, 20), (139, 22), (151, 18), (171, 19), (197, 23)]:
    m.set(x, y, "+")
for x, y in [(7, 21), (62, 25), (94, 21), (122, 20), (143, 22), (167, 19), (202, 29)]:
    m.set(x, y, "&")

# ---------------------------------------------------------------- objects
m.set(4, 21, "P")
m.set(9, 21, "t")        # sign: don't look down
m.set(20, 21, "u")       # sign: bounce pods
m.set(74, 5, "C")        # checkpoint on the crown
m.set(144, 22, "C")      # checkpoint at the end of the long bridges
m.set(191, 15, "E")

# ---------------------------------------------------------------- enemies
for x, y in [(40, 12), (51, 9), (66, 15), (93, 15), (101, 16), (111, 9), (121, 16), (134, 17),
             (148, 14), (159, 16), (170, 14), (176, 14), (186, 10), (200, 15), (64, 23), (130, 26), (96, 3)]:
    m.set(x, y, "m")     # mothlings
for x, y in [(53, 19), (93, 21), (124, 20), (169, 19), (181, 18)]:
    m.set(x, y, "j")     # leapers
for x, y in [(41, 21), (111, 20), (155, 22), (196, 15)]:
    if m.get(x, y) == " ":
        m.set(x, y, "b")     # beetles
for x, y in [(41, 24), (122, 27), (152, 25), (110, 28)]:
    if m.get(x, y) == " ":
        m.set(x, y, "n")  # snapvines under canopy masses
for x, y in [(105, 17), (150, 14), (184, 11)]:
    m.set(x, y, "M")     # mothlings that beam in

legend = [
    ("b", "enemy beetle"),
    ("j", "enemy leaper"),
    ("m", "enemy mothling"),
    ("M", "enemy mothling ambush"),
    ("n", "enemy snapvine"),
    ("s", "spring"),
    ("q", "power shield"),
    ("c", "treasure crown"),
    ("t", "sign sign.e2l3.fall"),
    ("u", "sign sign.e2l3.pods"),
]
header = [
    "# e2l3 Canopy Bridges -- built by tools/levels/e2/e2l3.py",
    "name      Canopy Bridges",
    "name.de   Kronenbrücken",
    "theme     jungle",
    "tint      0",
    "bg        jungle_a",
    "music     e2_jungle",
    "dark      0.1",
    "par       360",
]
# six more rows of open sky over the canopy
m.g = [[" "] * (W - 5) + ["#"] * 5 for _ in range(6)] + m.g
m.h += 6
m.save("e2l3", header, legend)
print(stats(m, legend))
run("e2l3", parts=[(0, 18, 40, 22), (44, 6, 50, 34), (94, 14, 56, 30), (150, 12, 62, 32)])
