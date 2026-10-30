"""e2l8 The Nursery -- the brood chambers of the hive, dark: hivenests, stalkers, ambushes, the gold key.

Route: the west tunnel -> the Brood Hall, a great cavern with log ladders down both sides, a comb island with a
hivenest in the middle (checkpoint on its floor) -> south through a hole into the Egg Pits (ambushes, resin, the
blue key at their east end) -> back up, east along the Larva Galleries (stalkers in the corridor, larva cells above
and below) -> the blue door -> the Royal Approach, a tall cavern: down to the gold key in the nest at its bottom,
up again to the gold door and the exit chamber.
Secrets: a cell behind a fake wall at the very start, an egg chamber behind breakable comb in the pits, a vault in
the Royal Approach's east wall.
"""
from lvl import Map, run, stats, ladder

W, H = 200, 68
m = Map(W, H, "#")


def log(x0, x1, y):
    m.hline(x0, x1, y, "-")


def comb(x0, x1, y, rows=2):
    m.rect(x0, y, x1, y + rows - 1, "%")


lights = []

# ---------------------------------------------------------------- the west tunnel (floor 20)
m.rect(4, 13, 29, 19, ".")
m.rect(10, 13, 13, 14, "#")
m.rect(20, 13, 24, 13, "#")
lights += [(8, 15), (18, 15), (27, 15)]
# secret 1: a cell behind a fake wall at the very start
m.rect(4, 18, 4, 19, "X")
m.rect(4, 13, 4, 17, "#")
m.rect(1, 15, 3, 19, "?")

# ---------------------------------------------------------------- the Brood Hall (floor 41)
m.rect(30, 5, 92, 40, " ")
m.rect(30, 20, 32, 21, "#")                 # the entrance ledge
m.rect(89, 20, 92, 21, "#")                 # the ledge at the north exit
for i, y in enumerate(range(23, 40, 3)):    # log ladders down both sides
    log(33, 37, y) if i % 2 == 0 else log(37, 41, y)
    log(84, 88, y) if i % 2 == 0 else log(80, 84, y)
comb(52, 70, 31)                            # the comb island with a hivenest
log(43, 49, 32)
log(73, 78, 32)
log(56, 60, 28)
log(61, 65, 25)
log(56, 60, 22)
log(62, 66, 19)
for x0, x1, y0, y1 in ((44, 50, 5, 9), (66, 76, 5, 8), (58, 62, 9, 12), (86, 92, 5, 11)):
    m.rect(x0, y0, x1, y1, "%")             # egg clusters hanging from the roof
m.rect(49, 41, 51, 42, "~")                 # resin on the hall floor
m.rect(71, 41, 73, 42, "~")
comb(58, 63, 39)                            # an egg mound on the floor
lights += [(34, 22), (40, 30), (35, 37), (86, 22), (81, 30), (86, 37), (55, 27), (66, 27), (61, 18), (46, 38),
           (77, 38)]

# ---------------------------------------------------------------- the Egg Pits (floor 61)
m.rect(38, 41, 41, 45, ".")                 # the hole down from the hall, logs both ways
m.rect(30, 46, 112, 60, ".")
ladder(m, 38, 40, 61, 41)
for x0, x1, y0, y1 in ((30, 36, 46, 52), (50, 56, 46, 48), (78, 84, 46, 49), (100, 112, 46, 50)):
    m.rect(x0, y0, x1, y1, "#")             # an uneven roof
for x0, x1 in ((46, 48), (65, 67), (89, 91)):
    m.rect(x0, 61, x1, 62, "~")             # resin pools
comb(52, 58, 58, 3)                         # egg mounds
comb(72, 77, 58, 3)
comb(94, 98, 58, 3)
log(60, 63, 57)
log(68, 71, 54)
log(79, 83, 56)
log(85, 89, 53)
log(99, 104, 55)
log(106, 110, 52)
# secret 2: an egg chamber behind breakable comb at the pits' east end
m.rect(113, 59, 113, 60, "B")
m.rect(114, 55, 120, 60, "?")
lights += [(36, 56), (48, 55), (60, 53), (70, 51), (82, 52), (92, 55), (104, 51), (110, 57)]

# ---------------------------------------------------------------- the Larva Galleries (corridor floor 20)
m.rect(93, 14, 150, 19, ".")
cells_up = [(100, 108), (130, 138)]
for x0, x1 in cells_up:
    m.rect(x0, 7, x1, 13, ".")
    log(x0 + 1, x0 + 4, 17)
    log(x0 + 4, x1 - 1, 14)
    log(x0 + 1, x0 + 4, 11)
cells_down = [(114, 123), (140, 148)]
for x0, x1 in cells_down:                   # crawl cells under the corridor, a 3-wide opening in its floor
    m.rect(x0, 21, x1, 22, ".")
    mid = (x0 + x1) // 2
    m.rect(mid - 1, 20, mid + 1, 20, ".")

lights += [(96, 15), (104, 9), (110, 15), (118, 22), (126, 15), (134, 9), (144, 22), (148, 15)]

# the hatchery: a cave under the galleries, down a shaft from the corridor (floor 46)
m.rect(128, 20, 130, 33, ".")
m.rect(116, 34, 150, 45, ".")
ladder(m, 128, 129, 46, 20)
m.rect(116, 34, 122, 37, "#")
m.rect(142, 34, 150, 36, "#")
comb(119, 124, 43, 3)
comb(136, 140, 44, 2)
m.rect(131, 46, 134, 47, "~")
m.rect(131, 46, 131, 46, ".")
m.rect(134, 46, 134, 46, ".")
m.rect(131, 47, 134, 47, "#")
m.rect(132, 46, 133, 46, "~")
log(141, 145, 41)
log(145, 149, 38)
lights += [(126, 36), (138, 38), (147, 42), (119, 40)]
# ---------------------------------------------------------------- the blue door and the Royal Approach
m.rect(151, 17, 151, 19, "d")
m.rect(152, 8, 189, 61, " ")
m.rect(152, 20, 157, 21, "#")               # the ledge behind the blue door
steps = [  # (x0, x1, row, kind): the way down to the nest and up to the gold door
    (160, 164, 23, "-"), (156, 160, 26, "-"), (160, 164, 29, "-"), (156, 160, 32, "-"), (160, 164, 35, "-"),
    (156, 160, 38, "-"), (160, 164, 41, "-"), (156, 160, 44, "-"), (160, 164, 47, "-"), (156, 160, 50, "-"),
    (160, 164, 53, "-"), (156, 160, 56, "-"), (160, 164, 59, "-"),
    (172, 178, 59, "%"), (180, 184, 56, "-"), (185, 189, 53, "-"), (180, 184, 50, "-"), (185, 189, 47, "-"),
    (180, 184, 44, "-"), (185, 189, 41, "-"), (180, 184, 38, "-"), (185, 189, 35, "-"), (180, 184, 32, "-"),
    (185, 189, 29, "-"), (180, 184, 26, "-"), (185, 189, 23, "-"), (180, 184, 20, "-"), (185, 189, 17, "-"),
    (167, 172, 44, "%"), (170, 175, 30, "%"), (166, 170, 37, "-"), (173, 177, 24, "-"),
]
for x0, x1, y, ch in steps:
    if ch == "-":
        log(x0, x1, y)
    else:
        comb(x0, x1, y)
m.rect(164, 62, 167, 63, "~")               # resin beside the nest
# the gold door and the exit chamber
m.rect(190, 14, 191, 15, "#")
m.rect(190, 11, 190, 13, "D")
m.rect(191, 8, 197, 13, ".")
# secret 3: a vault in the east wall behind a fake wall
m.rect(190, 39, 190, 40, "X")
m.rect(191, 36, 197, 40, "?")
lights += [(154, 18), (162, 25), (158, 34), (162, 45), (158, 54), (168, 58), (176, 57), (182, 48), (187, 39),
           (182, 28), (187, 19), (172, 28), (194, 10), (194, 38)]

# ---------------------------------------------------------------- items
crystals = [
    (16, 19), (26, 16),
    (35, 22), (39, 34), (86, 25), (82, 37), (60, 30), (64, 24), (58, 21), (64, 18), (46, 31), (76, 31),
    (44, 60), (55, 55), (62, 56), (74, 57), (87, 52), (96, 57), (108, 51),
    (104, 10), (134, 10), (114, 22), (148, 22), (121, 42), (148, 37),
    (162, 58), (175, 58), (169, 43), (172, 29), (187, 16),
]
for x, y in crystals:
    m.set(x, y, "*")
treasure = [
    (7, 19), (9, 19), (12, 16), (22, 16), (28, 19),
    (34, 19), (36, 25), (40, 28), (34, 31), (40, 37), (85, 22), (81, 28), (86, 34), (81, 40), (54, 30), (66, 30),
    (57, 27), (59, 27), (62, 24), (63, 24), (57, 21), (63, 18), (65, 18), (44, 31), (48, 31), (74, 31), (77, 31),
    (32, 40), (38, 40), (45, 40), (56, 38), (65, 40), (79, 40), (88, 40),
    (35, 60), (42, 60), (51, 60), (57, 56), (61, 56), (69, 53), (70, 53), (80, 55), (82, 55), (86, 52), (88, 52),
    (100, 54), (102, 54), (107, 51), (110, 60),
    (96, 19), (102, 13), (106, 13), (110, 19), (116, 22), (121, 22), (126, 19), (132, 13), (136, 13),
    (142, 22), (146, 22), (149, 19), (125, 45), (127, 45), (137, 43), (139, 43), (143, 40), (146, 37),
    (155, 19), (162, 22), (158, 31), (162, 40), (158, 49), (162, 52), (174, 58), (177, 58), (182, 55), (187, 46),
    (182, 37), (187, 28), (182, 19), (168, 36), (175, 23), (192, 13), (193, 13),
]
for x, y in treasure:
    if m.get(x, y) in ". ":
        m.set(x, y, "$")
for x, y in [(1, 19), (2, 19), (1, 17)]:                                   # secret 1
    m.set(x, y, "$")
m.set(3, 19, "&")
for x, y in [(115, 60), (116, 60), (118, 60), (119, 60)]:                 # secret 2
    m.set(x, y, "$")
m.set(117, 60, "c")                                                        # a crown
m.set(120, 60, "H")
for x, y in [(192, 40), (193, 40), (195, 40)]:                             # secret 3
    m.set(x, y, "$")
m.set(194, 40, "w")                                                        # overdrive
m.set(196, 40, "&")

for x, y in [(20, 19), (31, 40), (90, 40), (67, 60), (98, 60), (112, 19), (138, 19), (153, 19), (162, 61),
             (182, 49), (188, 22)]:
    if m.get(x, y) in ". ":
        m.set(x, y, "+")
for x, y in [(24, 19), (37, 40), (85, 40), (40, 60), (85, 60), (124, 19), (146, 19), (157, 25), (178, 58),
             (186, 34)]:
    if m.get(x, y) in ". ":
        m.set(x, y, "&")
for x, y in lights:
    if m.get(x, y) in ". ":
        m.set(x, y, "L")

# ---------------------------------------------------------------- objects
m.set(7, 19, "P")
m.set(33, 40, "C")       # checkpoint on the Brood Hall floor
m.set(154, 19, "C")      # checkpoint behind the blue door
m.set(109, 60, "k")      # blue key at the pits' east end
m.set(170, 61, "K")      # gold key in the nest
m.set(195, 13, "E")

# ---------------------------------------------------------------- enemies
for x, y in [(61, 30), (68, 30), (80, 60), (176, 58), (138, 43)]:
    if m.get(x, y) in ". ":
        m.set(x, y, "h")     # hivenests
for x, y in [(100, 19), (120, 19), (140, 19), (44, 40), (82, 40), (90, 60), (170, 60), (186, 13)]:
    if m.get(x, y) in ". ":
        m.set(x, y, "z")     # stalkers
for x, y in [(46, 15), (74, 14), (60, 36), (170, 15), (178, 36), (165, 50)]:
    if m.get(x, y) == " ":
        m.set(x, y, "m")     # mothlings
for x, y in [(45, 46), (66, 47), (90, 47), (106, 14), (136, 14), (175, 9), (160, 9)]:
    if m.get(x, y) in ". ":
        m.set(x, y, "n")     # snapvines
for x, y in [(76, 31), (48, 32), (104, 54), (184, 55), (173, 29)]:
    if m.get(x, y) in ". *":
        pass
for x, y in [(75, 30), (47, 31), (103, 54), (183, 55), (171, 29), (57, 55)]:
    if m.get(x, y) in ". ":
        m.set(x, y, "y")     # spitters
for x, y in [(56, 60), (75, 60), (103, 60), (110, 19), (132, 19), (160, 62), (184, 19), (147, 45)]:
    if m.get(x, y) in ". ":
        m.set(x, y, "Z")     # stalkers that beam in
for x, y in [(62, 60), (96, 60), (116, 19), (163, 53), (181, 43)]:
    if m.get(x, y) in ". ":
        m.set(x, y, "J")     # leapers that beam in
for x, y in [(36, 31), (85, 28)]:
    if m.get(x, y) in ". ":
        m.set(x, y, "b")

legend = [
    ("h", "enemy hivenest"),
    ("z", "enemy stalker"),
    ("Z", "enemy stalker ambush"),
    ("m", "enemy mothling"),
    ("n", "enemy snapvine"),
    ("y", "enemy spitter"),
    ("J", "enemy leaper ambush"),
    ("b", "enemy beetle"),
    ("w", "power overdrive"),
    ("c", "treasure crown"),
    ("L", "light orange 6"),
]
header = [
    "# e2l8 The Nursery -- built by tools/levels/e2/e2l8.py",
    "name      The Nursery",
    "name.de   Die Brutkammern",
    "theme     hive",
    "tint      2",
    "bg        hive_a",
    "music     e2_hive",
    "dark      0.5",
    "par       540",
]
m.save("e2l8", header, legend)
print(stats(m, legend))
run("e2l8", parts=[(0, 4, 50, 40), (28, 2, 66, 42), (28, 40, 94, 26), (90, 4, 64, 26), (150, 4, 50, 62)])
