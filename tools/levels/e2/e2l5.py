"""e2l5 Hive Outskirts -- the edge of the hive: the cryo projector, spitters, resin pools.

Route: the hive mouth (cryo projector + sign, the first spitter on a comb block) -> the Resin Falls, a vast cavern over
a lake of resin: bone platforms east and up, a low tier near the resin (crystals, ladders back up), an upper tier
(crystals) -> the comb galleries, three tunnels through the honeycomb joined by shafts, the blue key at the east end
of the lowest one, a loft open to the cavern above -> the blue door -> down the Hive Gate cavern to the exit.
Secrets: a cell in the honeycomb behind a fake wall in the mouth, breakable comb in the middle gallery, a fake wall
behind the exit cavern's resin fall.
"""
from lvl import Map, run, stats, ladder

W, H = 208, 62
m = Map(W, H, "#")


def comb(x0, x1, y, rows=2):
    m.rect(x0, y, x1, y + rows - 1, "%")


def log(x0, x1, y):
    m.hline(x0, x1, y, "-")


# ---------------------------------------------------------------- zone A: the hive mouth (floor 40)
m.rect(3, 16, 48, 39, " ")
m.rect(3, 16, 11, 30, "#")                  # a lower roof at the mouth, rock above the start
m.rect(24, 16, 27, 18, "#")
m.rect(36, 16, 38, 19, "#")
m.rect(31, 40, 33, 41, "~")                 # a small resin pool
comb(39, 44, 37, 3)                         # the first spitter's comb block
m.rect(8, 37, 9, 39, "%")
log(18, 22, 37)
log(26, 30, 34)
# secret 1: a cell in the rock above the start, behind a fake wall at the top of a log ladder
for x0, y in ((12, 37), (15, 34), (12, 31), (12, 28)):
    log(x0, x0 + 2, y)
m.rect(4, 24, 10, 27, "?")
m.rect(11, 26, 11, 27, "X")

# ---------------------------------------------------------------- zone B: the Resin Falls (resin lake rows 55-56)
m.rect(49, 6, 106, 54, " ")
m.rect(49, 55, 106, 56, "~")
m.rect(45, 40, 48, 54, "#")                 # the mouth's lip
for x0, x1, y in ((49, 54, 40), (57, 61, 38), (73, 77, 38), (80, 84, 35), (95, 99, 31), (101, 106, 29)):
    log(x0, x1, y)                          # the main way east
comb(64, 70, 36)
comb(87, 92, 33)
# the upper tier
log(66, 68, 33)
log(62, 64, 30)
log(66, 68, 27)
comb(58, 64, 24)
log(76, 80, 26)
log(81, 85, 23)
comb(86, 92, 20)
log(94, 97, 23)
log(97, 101, 26)
# the low tier near the resin, with ladders back up
comb(52, 57, 48)
log(57, 59, 45)
log(54, 56, 42)
comb(75, 81, 50)
log(78, 80, 47)
log(74, 76, 44)
log(77, 79, 41)
comb(96, 102, 49)
log(100, 102, 46)
log(97, 99, 43)
log(94, 96, 40)
log(96, 98, 37)
log(95, 97, 34)
# hanging comb from the roof
for x0, x1, y0, y1 in ((60, 66, 6, 10), (78, 84, 6, 9), (95, 103, 6, 12)):
    m.rect(x0, y0, x1, y1, "%")

# ---------------------------------------------------------------- zone C: the comb galleries
m.rect(107, 6, 162, 58, "%")
m.rect(107, 25, 160, 28, ".")               # tunnel 1, floor 29
m.rect(113, 35, 160, 38, ".")               # tunnel 2, floor 39
m.rect(113, 45, 158, 48, ".")               # tunnel 3, floor 49
for x in (114, 136):                        # shafts between all three tunnels, ladders both ways
    m.rect(x, 29, x + 2, 34, ".")
    m.rect(x, 39, x + 2, 44, ".")
    ladder(m, x, x + 1, 49, 39)
    ladder(m, x + 1, x, 39, 29)
m.rect(156, 29, 158, 34, ".")
ladder(m, 156, 157, 39, 29)
m.rect(125, 39, 127, 40, "~")               # resin pools in the tunnel floors
m.rect(146, 49, 148, 50, "~")
m.rect(104, 27, 106, 28, " ")
# the loft above tunnel 1, open to the hive
m.rect(118, 12, 150, 21, " ")
m.rect(130, 22, 132, 24, ".")
ladder(m, 130, 131, 29, 22)
log(124, 128, 19)
comb(118, 122, 16)
log(127, 130, 16)
log(134, 138, 19)
comb(140, 146, 16)
log(136, 139, 14)
for x0, y0, x1, y1 in ((107, 6, 162, 10), (107, 52, 162, 58), (140, 40, 162, 44), (107, 30, 112, 34),
                       (150, 6, 162, 24)):
    m.replace(x0, y0, x1, y1, "%", "#")     # chitin bands through the honeycomb
# secret 2: breakable comb at the west end of tunnel 2
m.rect(112, 37, 112, 38, "B")
m.rect(108, 35, 111, 38, "?")

# ---------------------------------------------------------------- zone D: the blue door and the Hive Gate cavern
m.rect(161, 26, 161, 28, "d")
m.rect(162, 10, 204, 57, " ")
m.rect(162, 29, 166, 31, "#")
steps = [(167, 172, 32, "%"), (174, 178, 35, "-"), (168, 173, 38, "-"), (175, 181, 41, "%"), (184, 188, 44, "-"),
         (190, 195, 47, "%"), (197, 204, 50, "#"), (184, 189, 53, "-"), (176, 182, 55, "%")]
for x0, x1, y, ch in steps:
    if ch == "-":
        log(x0, x1, y)
    else:
        m.rect(x0, y, x1, y + 1, ch)
m.rect(162, 58, 204, 61, "#")
m.rect(162, 56, 175, 57, "~")               # resin at the foot of the gate cavern
m.rect(183, 56, 196, 57, "~")
m.rect(197, 52, 204, 57, "#")
m.rect(176, 57, 182, 57, "#")
# upper ledges with crystals
log(186, 191, 32)
log(193, 198, 29)
comb(198, 204, 26)
log(181, 185, 27)
comb(172, 177, 23)
log(166, 170, 26)
log(185, 188, 50)                           # from the low steps back up
# secret 3: a hollow in the cavern's east wall behind a fake wall beside the exit
m.rect(206, 45, 207, 49, "?")
m.rect(205, 48, 205, 49, "X")

# ---------------------------------------------------------------- items
crystals = [
    (20, 36), (42, 35), (28, 33), (5, 27),
    (54, 47), (67, 26), (62, 23), (78, 49), (89, 19), (99, 48), (90, 32),
    (119, 15), (144, 15), (128, 15), (120, 28), (150, 38), (124, 48), (157, 48),
    (178, 40), (199, 49), (195, 28), (174, 22), (186, 52),
]
for x, y in crystals:
    m.set(x, y, "*")
treasure = [
    (14, 39), (19, 36), (21, 36), (27, 33), (29, 33), (35, 39), (37, 39), (13, 36), (16, 33), (13, 30), (12, 27),
    (51, 39), (53, 39), (59, 37), (60, 37), (66, 35), (68, 35), (75, 37), (82, 34), (83, 34), (90, 32),
    (97, 30), (103, 28), (105, 28), (60, 23), (64, 23), (78, 25), (83, 22), (87, 19), (91, 19), (96, 22),
    (53, 47), (56, 47), (76, 49), (80, 49), (98, 48), (101, 48),
    (110, 28), (118, 28), (122, 28), (140, 28), (146, 28), (152, 28), (118, 38), (122, 38), (132, 38),
    (142, 38), (146, 38), (118, 48), (128, 48), (134, 48), (140, 48), (152, 48),
    (120, 15), (125, 18), (127, 18), (129, 15), (142, 15), (145, 15), (136, 18), (137, 13), (138, 13),
    (169, 31), (171, 31), (176, 34), (170, 37), (177, 40), (179, 40), (186, 43), (192, 46), (199, 49),
    (201, 49), (186, 52), (179, 54), (180, 54), (188, 31), (190, 31), (195, 28), (197, 28), (182, 26),
    (175, 22), (176, 22), (168, 25),
]
for x, y in treasure:
    if m.get(x, y) in ". ":
        m.set(x, y, "$")
for x, y in [(6, 27), (8, 27), (9, 27)]:                                   # secret 1
    m.set(x, y, "$")
m.set(7, 27, "&")
for x, y in [(109, 38), (110, 38)]:                                        # secret 2
    m.set(x, y, "$")
m.set(108, 38, "H")
m.set(111, 38, "w")                                                        # overdrive
for x, y in [(206, 49), (207, 49)]:                                        # secret 3
    m.set(x, y, "$")
m.set(207, 47, "i")

for x, y in [(30, 39), (48, 39), (71, 35), (100, 28), (112, 28), (130, 38), (155, 48), (165, 28), (180, 40),
             (203, 49)]:
    if m.get(x, y) in ". ":
        m.set(x, y, "+")
for x, y in [(10, 39), (22, 39), (55, 47), (85, 34), (104, 28), (116, 38), (150, 28), (138, 48), (168, 31),
             (191, 46), (199, 25)]:
    if m.get(x, y) in ". ":
        m.set(x, y, "&")

# ---------------------------------------------------------------- objects
m.set(6, 39, "P")
m.set(20, 39, "c")       # the cryo projector
m.set(16, 39, "t")       # sign: cryo
m.set(36, 39, "u")       # sign: spitters
m.set(53, 39, "C")       # checkpoint at the Resin Falls
m.set(117, 28, "C")      # checkpoint in the comb galleries
m.set(157, 47, "k")      # blue key at the east end of tunnel 3
m.set(201, 49, "E")

# ---------------------------------------------------------------- enemies
for x, y in [(43, 36), (68, 35), (91, 32), (122, 15), (141, 15), (176, 40), (193, 46), (97, 48), (189, 31)]:
    if m.get(x, y) in ". ":
        m.set(x, y, "y")     # spitters on ledges and blocks
for x, y in [(70, 20), (84, 14), (100, 18), (58, 44), (90, 44), (135, 14), (180, 20), (192, 38), (170, 47)]:
    if m.get(x, y) in " ":
        m.set(x, y, "m")     # mothlings
for x, y in [(26, 39), (126, 28), (148, 28), (128, 38), (152, 48), (120, 48)]:
    if m.get(x, y) in ". ":
        m.set(x, y, "b")     # beetles
for x, y in [(140, 38), (196, 50), (176, 55)]:
    if m.get(x, y) in ". ":
        m.set(x, y, "j")     # leapers
for x, y in [(144, 28), (132, 48), (172, 32)]:
    if m.get(x, y) in ". ":
        m.set(x, y, "Y")     # spitters that beam in

legend = [
    ("y", "enemy spitter"),
    ("Y", "enemy spitter ambush"),
    ("m", "enemy mothling"),
    ("b", "enemy beetle"),
    ("j", "enemy leaper"),
    ("c", "weapon cryo"),
    ("w", "power overdrive"),
    ("i", "treasure idol"),
    ("t", "sign sign.e2l5.cryo"),
    ("u", "sign sign.e2l5.spitter"),
]
header = [
    "# e2l5 Hive Outskirts -- built by tools/levels/e2/e2l5.py",
    "name      Hive Outskirts",
    "name.de   Rand des Stocks",
    "theme     hive",
    "tint      0",
    "bg        hive_a",
    "music     e2_hive",
    "dark      0.25",
    "par       450",
]
m.save("e2l5", header, legend)
print(stats(m, legend))
run("e2l5", parts=[(0, 14, 50, 30), (46, 4, 62, 54), (104, 8, 60, 46), (160, 8, 48, 54)])
