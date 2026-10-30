"""e2l6 Spore Marsh -- a marsh of acid at dusk: sporepods, crumbling rotten logs, stalkers.

Route: the hill (sporepod sign) -> the marsh edge -> the wide marsh: islands joined by crumble bridges, a high log
route above with treasure, the stalker lesson on a long island -> the hummock: over its top or through the mud cave
underneath (both hold crystals; checkpoint at the hummock) -> the drowned forest: trunks with branch ladders, crumble
bridges, sporepods (checkpoint) -> the east bank and the exit.
Secrets: a hollow in the hill behind a fake wall, a niche in the mud cave behind breakable rock, a hollow at the top
of the tallest trunk.
"""
from lvl import Map, run, stats, ladder

W, H = 220, 54
m = Map(W, H, "#")


def log(x0, x1, y):
    m.hline(x0, x1, y, "-")


def crumble(x0, x1, y):
    m.hline(x0, x1, y, "_")


# ---------------------------------------------------------------- the surface
m.ground([
    (0, 2, 18), (3, 20, 30), (21, 23, 33), (24, 30, 36), (31, 34, 37), (35, 49, 36),
    (50, 112, 38),                           # the wide marsh
    (113, 118, 33), (119, 146, 30), (147, 152, 33),
    (153, 203, 38),                          # the drowned forest
    (204, 219, 34),
])
# zone A: hill, a pool, a lone tree's logs
m.rect(31, 37, 34, 38, "~")
m.rect(31, 39, 34, 39, "#")
m.rect(10, 29, 11, 29, "%")
m.rect(14, 28, 14, 29, "%")
log(38, 42, 33)
log(43, 46, 30)
log(36, 39, 27)
# secret 1: a hollow in the hill behind a fake wall at its foot
m.rect(12, 33, 20, 35, "?")
m.rect(21, 34, 23, 35, "X")

# ---------------------------------------------------------------- the wide marsh (acid rows 38-40)
m.rect(50, 38, 112, 40, "~")
islands = [(53, 57, 36), (62, 68, 35), (73, 76, 36), (81, 90, 35), (95, 98, 36), (103, 108, 35)]
for x0, x1, top in islands:
    m.rect(x0, top, x1, 41, "#")
crumble(58, 61, 36)
crumble(69, 72, 36)
crumble(91, 94, 36)
log(99, 102, 35)
crumble(109, 112, 35)
# the high route: logs above the marsh
for x0, x1, y in ((64, 67, 32), (69, 73, 29), (76, 80, 27), (83, 87, 29), (89, 92, 31), (96, 99, 32),
                  (55, 58, 33), (58, 61, 30)):
    log(x0, x1, y)
m.rect(77, 26, 79, 26, " ")
# reeds and stones on the islands
m.put(65, 34, "%")
m.put(86, 34, "%%")
m.put(105, 34, "%")

# ---------------------------------------------------------------- the sump: a tunnel under the marsh (floor 50)
m.rect(44, 46, 121, 49, ".")
m.rect(44, 36, 46, 45, ".")                 # the hole down from the marsh edge
ladder(m, 44, 45, 50, 36)
for x0, x1 in ((58, 61), (79, 82), (100, 102)):
    m.rect(x0, 50, x1, 51, "~")             # acid puddles in its floor
for x0, x1 in ((66, 68), (90, 92)):
    m.rect(x0, 46, x1, 47, "#")             # low rock in the roof
m.rect(108, 48, 109, 49, "%")
m.rect(73, 48, 74, 49, "%")

# ---------------------------------------------------------------- the hummock and the mud cave (floor 45)
m.rect(116, 35, 150, 44, ".")
m.rect(116, 35, 119, 37, "#")
m.rect(130, 35, 133, 36, "#")
m.rect(144, 35, 150, 37, "#")
m.rect(121, 30, 123, 34, ".")               # the way down from the top, logs both ways
ladder(m, 121, 122, 45, 30)
m.rect(140, 30, 142, 34, ".")               # and the second way up at the east end
ladder(m, 141, 140, 45, 30)
m.rect(127, 45, 130, 46, "~")               # an acid pool with a crumble lid
crumble(127, 130, 45)
m.rect(127, 47, 130, 47, "#")
m.rect(136, 45, 138, 46, ".")               # a spike pit with a crumble lid
m.rect(136, 47, 138, 47, "^")
crumble(136, 138, 45)
m.rect(124, 42, 125, 44, "%")
log(132, 135, 41)
log(126, 129, 38)
m.rect(146, 38, 150, 44, ".")
m.rect(118, 45, 120, 45, ".")               # up from the sump into the mud cave
ladder(m, 118, 119, 50, 45)
log(147, 150, 41)
# secret 2: a niche behind breakable rock at the cave's west end
m.rect(116, 43, 116, 44, "B")
m.rect(111, 42, 115, 44, "?")
# the hummock's top: a ruin and logs
m.rect(126, 28, 128, 29, "%")
m.rect(135, 27, 136, 29, "%")
log(130, 133, 26)
log(138, 142, 24)

# ---------------------------------------------------------------- the drowned forest (acid rows 38-40)
m.rect(153, 38, 203, 40, "~")
for x0, x1, top in ((153, 157, 36), (165, 169, 36), (179, 183, 36), (193, 197, 36)):
    m.rect(x0, top, x1, 41, "#")
crumble(198, 203, 36)
# trunks standing in the acid: a ladder of branches up one side and down the other
for x0, x1, top in ((160, 161, 24), (172, 175, 15), (187, 188, 22)):
    m.rect(x0, top, x1, 41, "#")
for xs, ys in (((157, 162), range(33, 24, -3)), ((169, 176), range(33, 15, -3)), ((184, 189), range(33, 22, -3))):
    for y in ys:
        log(xs[0], xs[0] + 2, y)
        log(xs[1], xs[1] + 2, y)
log(173, 174, 12)
# secret 3: a hollow at the top of the tallest trunk, behind a fake wall beside the top branch
m.rect(173, 16, 174, 17, "?")
m.rect(172, 16, 172, 17, "X")
# the east bank
m.rect(208, 32, 209, 33, "%")               # a broken stone on the bank
m.rect(217, 27, 218, 33, "%")               # and a tall one behind the exit
m.put(216, 26, "%%%%")

# ---------------------------------------------------------------- items
crystals = [
    (8, 29), (44, 29), (37, 26),
    (55, 35), (66, 31), (78, 25), (88, 34), (97, 35), (106, 34),
    (127, 27), (131, 25), (140, 23), (125, 41), (134, 40), (148, 40), (137, 44),
    (63, 49), (96, 49), (155, 35), (161, 23), (170, 20), (173, 14), (177, 26), (188, 21), (190, 29), (195, 35),
]
for x, y in crystals:
    m.set(x, y, "*")
treasure = [
    (4, 29), (16, 29), (18, 29), (22, 32), (26, 35), (28, 35), (32, 34), (33, 33), (40, 32), (45, 29),
    (54, 35), (56, 35), (59, 35), (60, 35), (63, 34), (67, 34), (70, 35), (71, 35), (74, 35), (75, 35),
    (65, 31), (71, 28), (72, 28), (77, 25), (79, 25), (84, 28), (86, 28), (90, 30), (97, 31), (98, 31),
    (56, 32), (59, 29), (60, 29), (92, 35), (93, 35), (100, 34), (101, 34), (110, 34), (111, 34),
    (114, 32), (117, 32), (120, 29), (124, 29), (131, 29), (133, 29), (139, 29), (144, 29), (149, 32),
    (122, 44), (123, 44), (128, 44), (129, 44), (139, 44), (141, 44), (127, 37), (128, 37), (149, 40),
    (154, 35), (157, 35), (158, 32), (163, 29), (159, 26), (166, 35), (168, 35), (170, 32), (177, 29),
    (171, 23), (177, 17), (180, 35), (182, 35), (185, 32), (190, 26), (185, 23), (194, 35), (199, 35), (201, 35),
    (211, 33), (212, 33), (208, 31), (209, 31),
    (50, 49), (52, 49), (54, 49), (70, 49), (76, 49), (85, 49), (87, 49), (104, 49), (112, 49), (114, 49),
]
for x, y in treasure:
    if m.get(x, y) in ". ":
        m.set(x, y, "$")
for x, y in [(13, 35), (14, 35), (15, 35), (17, 35)]:                     # secret 1
    m.set(x, y, "$")
m.set(16, 35, "&")
m.set(18, 35, "+")
for x, y in [(112, 44), (113, 44)]:                                        # secret 2
    m.set(x, y, "$")
m.set(114, 44, "H")
m.set(111, 44, "q")                                                        # shield
m.set(173, 17, "i")                                                        # secret 3
m.set(174, 17, "&")
for x, y in [(173, 11), (174, 11)]:
    m.set(x, y, "$")

for x, y in [(30, 35), (88, 49), (68, 34), (90, 34), (118, 32), (146, 29), (126, 44), (156, 35), (181, 35), (205, 33)]:
    if m.get(x, y) in ". ":
        m.set(x, y, "+")
for x, y in [(23, 32), (48, 49), (62, 34), (85, 34), (113, 32), (143, 44), (167, 35), (196, 35), (206, 33), (163, 26)]:
    if m.get(x, y) in ". ":
        m.set(x, y, "&")
for x, y in [(120, 36), (135, 37), (145, 39), (128, 41)]:
    if m.get(x, y) == ".":
        m.set(x, y, "G")     # glowing fungus in the mud cave

# ---------------------------------------------------------------- objects
m.set(6, 29, "P")
m.set(25, 35, "t")       # sign: sporepods
m.set(74, 35, "u")       # sign: stalkers
m.set(115, 32, "C")      # checkpoint on the hummock
m.set(204, 33, "C")      # checkpoint on the east bank? no: before the forest
m.set(214, 33, "E")

# ---------------------------------------------------------------- enemies
for x, y in [(33, 31), (42, 27), (60, 31), (78, 32), (94, 30), (101, 29), (127, 22), (163, 30), (180, 28),
             (192, 28), (198, 31), (166, 17)]:
    if m.get(x, y) == " ":
        m.set(x, y, "o")     # sporepods
for x, y in [(88, 34), (66, 34), (138, 29), (133, 44), (200, 35)]:
    if m.get(x, y) in ". ":
        m.set(x, y, "z")     # stalkers on long floors
for x, y in [(143, 29), (120, 44), (145, 44), (107, 34), (210, 33), (18, 29), (45, 35), (68, 49), (110, 49)]:
    if m.get(x, y) in ". ":
        m.set(x, y, "b")     # beetles
for x, y in [(57, 35), (96, 35), (169, 35), (197, 35), (64, 34), (104, 34)]:
    if m.get(x, y) in ". ":
        m.set(x, y, "j")     # leapers
for x, y in [(126, 36), (141, 36), (136, 39), (56, 46), (84, 46), (98, 46)]:
    if m.get(x, y) == ".":
        m.set(x, y, "n")     # snapvines in the mud cave
for x, y in [(110, 26), (150, 24), (186, 18)]:
    if m.get(x, y) == " ":
        m.set(x, y, "M")     # mothlings that beam in
for x, y in [(120, 29), (181, 35), (95, 49)]:
    if m.get(x, y) in ". ":
        m.set(x, y, "Z")     # stalkers that beam in

# the second checkpoint stands at the forest's edge, not on the east bank
m.set(204, 33, "&")
m.set(151, 32, "C")

legend = [
    ("o", "enemy sporepod"),
    ("z", "enemy stalker"),
    ("Z", "enemy stalker ambush"),
    ("b", "enemy beetle"),
    ("j", "enemy leaper"),
    ("n", "enemy snapvine"),
    ("M", "enemy mothling ambush"),
    ("q", "power shield"),
    ("i", "treasure idol"),
    ("G", "light green 5"),
    ("t", "sign sign.e2l6.sporepod"),
    ("u", "sign sign.e2l6.stalker"),
]
header = [
    "# e2l6 Spore Marsh -- built by tools/levels/e2/e2l6.py",
    "name      Spore Marsh",
    "name.de   Sporensumpf",
    "theme     jungle",
    "tint      2",
    "bg        jungle_b",
    "music     e2_jungle",
    "dark      0.3",
    "par       420",
]
m.save("e2l6", header, legend)
print(stats(m, legend))
run("e2l6", parts=[(0, 16, 50, 26), (48, 18, 66, 26), (108, 18, 48, 32), (150, 6, 70, 36)])
