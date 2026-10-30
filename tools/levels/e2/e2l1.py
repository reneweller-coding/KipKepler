"""e2l1 Landing Glade -- outdoors under the big sky of Thessa: acid pools, beetles, leapers.

Route: landing ground (acid lesson, ruin spire) -> glade with log terraces (beetle lesson) -> down the hollow shaft
into the Glade Hollow cave (west branch with crystals, east to the mesa chimney) -> up the chimney onto Mesa One
(checkpoint) -> acid lake: islands below, high log bridge above -> east beach, Mesa Two -> the field and the cave
under the cliffs (checkpoint) -> the terraced cliffs -> the plateau ruins and the exit.
Secrets: fake wall left of the start; breakable wall at the west end of the hollow; an alcove in Mesa Two reached
from the high bridge.
"""
import sys
from lvl import Map, run, stats

W, H = 186, 55
m = Map(W, H, "#")

# ---------------------------------------------------------------- the surface (sky above the top row of each run)
m.ground([
    (0, 9, 14),      # the cliff behind the landing ground
    (10, 21, 30),    # landing ground
    (22, 24, 31),    # pool 1 (acid lesson)
    (25, 27, 30),
    (28, 31, 26),    # ruin spire
    (32, 35, 30),
    (36, 47, 27),    # the glade
    (48, 52, 29),    # pool 2 with a stepping stone
    (53, 62, 27),
    (63, 66, 27),    # the hollow's mouth
    (67, 69, 27),
    (70, 82, 16),    # Mesa One
    (83, 85, 23),    # its east shoulder
    (86, 87, 31),    # west beach
    (88, 110, 33),   # the acid lake
    (111, 115, 30),  # east beach
    (116, 124, 18),  # Mesa Two
    (125, 143, 30),  # the field
    (144, 153, 27),  # cliff terraces
    (154, 163, 23),
    (164, 185, 19),  # the plateau
])

# landing ground: the cliff, a stone landing pad, the first small acid pool, a ruin spire with a crystal
m.rect(10, 30, 18, 30, "%")                 # landing pad (old stone)
m.rect(22, 31, 24, 32, "~")
m.rect(28, 26, 31, 29, "%")
m.put(25, 28, "---")                        # a log to reach the spire
m.put(33, 29, "%")                          # rubble
m.rect(34, 28, 35, 29, "%")
m.put(36, 27, "%%")

# secret 1: a fake wall left of the start into the cliff
m.rect(3, 25, 8, 29, "?")
m.put(9, 28, "X")
m.put(9, 29, "X")
m.rect(3, 24, 6, 24, "?")

# the glade: pool 2 with a stepping stone, ruin pillars carrying log terraces
m.rect(48, 29, 49, 30, "~")
m.rect(51, 29, 52, 30, "~")
m.rect(50, 28, 50, 30, "%")
m.vline(40, 25, 26, "%")                    # a stump under the first terrace
m.put(38, 24, "-----")
m.put(43, 21, "----")
m.put(47, 18, "-----")
m.put(53, 19, "----")                       # free logs further out
m.put(57, 22, "---")

# the hollow's mouth: a shaft down with logs left and right
m.rect(63, 27, 66, 41, ".")
m.put(63, 30, "--")
m.put(65, 33, "--")
m.put(63, 36, "--")
m.put(65, 39, "--")

# ---------------------------------------------------------------- the Glade Hollow (cave under the glade)
m.rect(44, 42, 80, 47, ".")                 # main hall, floor row 48
m.rect(52, 40, 62, 41, ".")                 # higher ceiling pockets
m.rect(67, 40, 76, 41, ".")
m.put(53, 45, "----")                       # logs under the pockets
m.put(68, 45, "----")
m.rect(46, 48, 48, 48, "~")                 # a small acid pool
m.rect(14, 44, 43, 51, ".")                 # west hall, floor row 52
m.rect(41, 50, 43, 51, "%")                 # a step back up to the main hall
m.rect(14, 52, 43, 52, "#")
m.rect(31, 52, 33, 52, "~")                 # acid stream in the west hall
m.rect(24, 40, 36, 43, ".")                 # a high gallery in the west hall
m.put(24, 47, "%%%")                        # stone blocks to climb to the gallery
m.rect(27, 44, 29, 47, "#")
m.put(36, 47, "----")
m.put(20, 49, "---")
m.rect(14, 44, 20, 46, "#")                 # west hall's sloped roof
m.rect(14, 47, 16, 47, "#")
# secret 2: breakable rocks at the far west end
m.rect(4, 47, 12, 51, "?")
m.rect(13, 50, 13, 51, "B")
m.rect(13, 47, 13, 49, "#")

m.put(45, 42, "#")                          # rock teeth and a ruin step in the main hall
m.put(57, 42, "##")
m.put(72, 42, "#")
m.rect(59, 46, 60, 47, "%")

# the mesa chimney: up from the hall's east end through Mesa One, stone ledges left and right
m.rect(76, 18, 80, 41, ".")
m.rect(79, 16, 80, 17, ".")                 # the way out onto the mesa top
m.rect(73, 26, 75, 29, ".")                 # a side room half way with a crystal
for i, y in enumerate(range(19, 47, 3)):
    m.put(79 if i % 2 == 0 else 76, y, "--")
for y in (21, 27, 33, 39):                  # old stone set into the chimney walls
    m.rect(81, y, 81, y + 1, "%")
for y in (24, 36):
    m.rect(75, y, 75, y + 1, "%")

# ---------------------------------------------------------------- the acid lake
m.rect(88, 33, 110, 35, "~")
for x0, top in ((91, 31), (96, 30), (101, 31), (106, 30)):
    m.rect(x0, top, x0 + 1, 35, "%")
m.rect(86, 31, 87, 31, "%")
m.rect(111, 30, 112, 30, "%")
# logs up Mesa One's east face: back from the lake to the mesa top
m.put(86, 28, "--")
m.put(86, 25, "--")
m.put(83, 20, "---")
m.put(83, 18, "--")
# the high log bridge from Mesa One to Mesa Two
m.put(86, 16, "-----")
m.put(94, 14, "----")
m.put(101, 16, "----")
m.put(108, 14, "-----")
m.put(113, 16, "---")                       # a step between the bridge and Mesa Two
m.rect(98, 11, 99, 13, " ")
# Mesa Two: an alcove (secret 3) behind a fake wall on its west side, logs to climb it from the east
m.rect(117, 19, 121, 21, "?")
m.put(116, 19, "X")
m.put(116, 20, "X")
m.put(113, 21, "---")                       # logs up the west face
m.put(111, 24, "---")
m.put(113, 27, "--")
m.put(125, 27, "--")
m.put(127, 24, "--")
m.put(125, 21, "--")

# ---------------------------------------------------------------- the field and the cave under the cliffs
m.rect(129, 30, 132, 39, ".")               # stairs down into the cave
for i, y in enumerate(range(44, 30, -3)):   # a log ladder from the cave floor up to the field
    m.put(131 if i % 2 == 0 else 129, y, "--")
m.rect(118, 40, 176, 46, ".")               # long cave, floor row 47
m.rect(118, 47, 140, 50, ".")               # lower west basin, floor row 51
m.rect(122, 50, 124, 50, "~")
m.rect(135, 50, 137, 50, "~")
m.put(126, 49, "%%%%%%%%")
m.rect(126, 50, 133, 50, "#")
m.rect(139, 49, 140, 50, "%")                # a step up to the cave floor
m.put(118, 47, ",")
m.rect(150, 47, 158, 47, "~")               # an acid trench with stepping stones in the east part
m.put(153, 47, "%")
m.put(156, 47, "%")
m.rect(145, 38, 150, 39, ".")
m.rect(162, 38, 170, 39, ".")
m.put(145, 44, "----")
m.put(164, 44, "----")
m.put(125, 40, "##")                        # rock teeth
m.put(141, 40, "#")
m.put(157, 40, "##")
# the cliff cave: from a pit in the lower terrace east to the shaft, with a drop into the long cave
m.rect(146, 31, 170, 35, ".")               # floor row 36
m.rect(147, 27, 149, 30, ".")               # the pit from the terrace, logs both ways
m.put(147, 30, "--")
m.put(148, 33, "--")
m.rect(150, 29, 152, 30, ".")
m.rect(156, 30, 166, 30, ".")
m.rect(171, 33, 171, 35, ".")               # into the shaft
m.rect(159, 36, 160, 37, ".")               # a hole down into the long cave
m.rect(155, 34, 156, 35, "%")
m.rect(165, 34, 165, 35, "%")
# the shaft up to the plateau at the cave's east end
m.rect(172, 19, 175, 39, ".")
for i, y in enumerate(range(44, 22, -3)):
    m.put(174 if i % 2 == 0 else 172, y, "--")
m.put(173, 21, "--")

# cliff terraces: steps and ledges
m.rect(142, 28, 143, 29, "%")
m.rect(152, 24, 153, 26, "%")
m.put(150, 25, "-")
m.rect(162, 20, 163, 22, "%")
m.put(146, 22, "----")
m.put(157, 18, "----")
m.put(160, 15, "---")
# the plateau ruins
m.rect(167, 17, 168, 18, "%")                # a broken stump
m.rect(184, 11, 185, 18, "%")                # a tall pillar behind the exit
m.put(183, 10, "%%%")
m.put(164, 16, "---")
m.put(169, 13, "-----")

# ---------------------------------------------------------------- items
crystals = [
    (30, 25), (40, 23), (49, 17),                     # spire, terraces
    (26, 39), (35, 45), (16, 51),                     # west hall and gallery
    (58, 47), (74, 29),                               # main hall, chimney side room
    (96, 29), (106, 29),                              # lake islands
    (72, 15),                                         # Mesa One
    (162, 33), (169, 35),                             # cliff cave
    (120, 46), (130, 48), (155, 46), (166, 40),       # cave under the cliffs
    (147, 21), (158, 17), (171, 12),                  # terraces and plateau
]
for x, y in crystals:
    m.set(x, y, "*")
treasure = [
    (22, 28), (23, 27), (24, 28),                     # arc over pool 1
    (49, 27), (50, 26), (51, 27),                     # arc over pool 2
    (44, 20), (45, 20), (53, 18), (54, 18), (55, 18), (56, 20),
    (64, 29), (65, 32), (64, 35),                     # down the shaft
    (54, 42), (55, 42), (69, 42), (70, 42),
    (25, 42), (28, 42), (31, 42), (34, 42),           # gallery
    (88, 15), (90, 15), (95, 13), (96, 13), (98, 10), (99, 10), (102, 15), (103, 15), (109, 13), (111, 13),
    (91, 30), (101, 30),
    (126, 26), (128, 23), (126, 20),
    (130, 32), (132, 35),
    (127, 48), (128, 48), (132, 48),
    (146, 41), (148, 41), (164, 41), (168, 41),
    (147, 21), (148, 21), (149, 21),
    (161, 14), (170, 12), (172, 12), (173, 12),
    (150, 35), (151, 35), (163, 35), (164, 35), (147, 29),
]
for x, y in treasure:
    if m.get(x, y) not in "*":
        m.set(x, y, "$")
for x, y in [(4, 29), (5, 29), (6, 27), (7, 29), (4, 26), (5, 26)]:     # secret 1
    m.set(x, y, "$")
m.set(8, 29, "&")
for x, y in [(5, 51), (6, 51), (7, 51), (9, 51)]:                       # secret 2
    m.set(x, y, "$")
m.set(8, 51, "w")                                                      # overdrive
m.set(11, 51, "H")
for x, y in [(118, 21), (119, 21), (120, 21)]:                         # secret 3
    m.set(x, y, "$")
m.set(121, 21, "i")
m.set(117, 21, "&")

for x, y in [(34, 26), (61, 26), (78, 47), (85, 22), (113, 29), (136, 29), (146, 46), (171, 46), (175, 18)]:
    m.set(x, y, "+")
m.set(39, 51, "H")
m.set(119, 50, "H")
for x, y in [(20, 29), (45, 47), (82, 15), (114, 29), (128, 46), (158, 46), (166, 18)]:
    m.set(x, y, "&")

# ---------------------------------------------------------------- objects
m.set(13, 29, "P")
m.set(19, 29, "t")      # sign: acid
m.set(55, 26, "u")      # sign: beetles
m.set(77, 15, "C")      # checkpoint on Mesa One
m.set(143, 46, "C")     # checkpoint in the cave under the cliffs
m.set(181, 18, "E")

# ---------------------------------------------------------------- enemies
for x, y in [(60, 26), (70, 47), (56, 47), (38, 51), (22, 51), (139, 29), (167, 46), (162, 46), (180, 18), (152, 35), (160, 35), (120, 17)]:
    m.set(x, y, "b")    # beetles on long floors
for x, y in [(30, 43), (115, 29), (123, 50), (133, 46), (168, 39), (149, 26), (158, 22), (172, 18), (173, 14), (133, 29), (42, 26)]:
    m.set(x, y, "j")    # leapers
for x, y in [(52, 47), (40, 51), (113, 29), (159, 46), (151, 22), (171, 14)]:
    if m.get(x, y) in ".  ":
        m.set(x, y, "J")  # leapers that beam in

legend = [
    ("b", "enemy beetle"),
    ("j", "enemy leaper"),
    ("J", "enemy leaper ambush"),
    ("w", "power overdrive"),
    ("i", "treasure idol"),
    ("t", "sign sign.e2l1.acid"),
    ("u", "sign sign.e2l1.beetle"),
]
header = [
    "# e2l1 Landing Glade -- built by tools/levels/e2/e2l1.py",
    "name      Landing Glade",
    "name.de   Landelichtung",
    "theme     jungle",
    "tint      0",
    "bg        jungle_a",
    "music     e2_jungle",
    "dark      0.1",
    "par       330",
]
m.save("e2l1", header, legend)
print(stats(m, legend))
run("e2l1", parts=[(0, 18, 40, 16), (36, 12, 40, 22), (10, 36, 40, 18), (60, 10, 40, 40), (84, 6, 44, 30),
                   (116, 16, 40, 38), (140, 8, 46, 42)])
