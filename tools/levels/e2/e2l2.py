"""e2l2 Root Caverns -- under the dusk jungle: crumble blocks, snapvines, the ricochet.

Route: a strip of dusk surface -> the sinkhole -> the ricochet alcove (weapon + sign) -> the root gallery (crumble
lesson over a safe pit, snapvine lesson over a gem) -> down into the great root hall (roots, spike pits with crumble
bridges, the skylight climb to the optional high road) -> the deep roots (checkpoint, acid river with crumble bridges
and islands, the blue key on the east bank) -> up the east shaft -> blue door -> the Tangle, a climb through roots
to the exit under the sky.
Secrets: breakable rocks beside the ricochet (shoot them), a fake root wall at the hall's west end, a trapdoor
in the west bank into a vault.
"""
from lvl import Map, run, stats

W, H = 204, 66
m = Map(W, H, "#")

# ---------------------------------------------------------------- the surface at dusk
m.ground([(0, 2, 3), (3, 36, 12), (37, 168, 5)])
m.rect(8, 11, 10, 11, "%")                  # old stones on the surface
m.rect(16, 10, 18, 11, "%")
m.put(17, 9, "%")
m.put(21, 9, "----")
m.rect(26, 11, 27, 11, "%")
m.rect(40, 3, 41, 4, "%")                   # ruins along the high road
m.rect(118, 4, 120, 4, "%")
m.rect(150, 3, 151, 4, "%")

# the sinkhole, logs both ways
m.rect(30, 12, 33, 23, ".")
for i, y in enumerate(range(26, 12, -3)):
    m.put(30 if i % 2 == 0 else 32, y, "--")

# ---------------------------------------------------------------- the root gallery (floor row 29)
m.rect(20, 24, 70, 28, ".")
m.rect(36, 22, 46, 23, ".")                 # a higher stretch of ceiling
m.put(39, 26, "-----")
# secret 1: breakable rocks west of the ricochet alcove (shoot them)
m.rect(12, 25, 18, 28, "?")
m.rect(19, 25, 19, 26, "#")
m.rect(19, 27, 19, 28, "B")
# crumble lesson: a shallow pit (safe, 3 deep) partly bridged by crumble blocks
m.rect(50, 29, 56, 31, ".")
m.hline(50, 54, 29, "_")
# a root column in the gallery
m.rect(63, 24, 64, 25, "#")
# down to the root hall: a shaft with logs (they also lead back up)
m.rect(66, 29, 69, 33, ".")
for x0, y in ((66, 31), (67, 34), (64, 37), (67, 40), (64, 43)):
    m.put(x0, y, "---")

# ---------------------------------------------------------------- the great root hall (floor row 46)
m.rect(38, 34, 128, 45, ".")
m.rect(58, 32, 63, 33, ".")                 # ceiling pockets
m.rect(108, 32, 118, 33, ".")
# roots hanging from the ceiling and a stone stump on the floor
m.rect(74, 34, 75, 39, "#")
m.rect(73, 34, 76, 35, "#")
m.rect(90, 41, 91, 45, "%")
m.rect(117, 34, 118, 38, "#")
m.rect(116, 34, 119, 35, "#")
m.rect(84, 34, 86, 35, "#")
# spike pits with crumble bridges
m.rect(78, 46, 84, 47, ".")
m.hline(78, 84, 48, "^")
m.hline(78, 84, 46, "_")
m.rect(104, 46, 110, 47, ".")
m.hline(104, 110, 48, "^")
m.hline(105, 109, 46, "_")
# ledges in the hall (every 3 rows: floor 46 -> 43 -> 40 -> 37)
for x0, x1, y in ((43, 46, 43), (49, 51, 40), (55, 58, 37), (59, 61, 43), (80, 83, 43), (86, 88, 43),
                  (112, 115, 43), (118, 120, 43), (121, 123, 40)):
    m.hline(x0, x1, y, "-")
# the skylight: a sky shaft from the hall up to the surface, stone ledges up its walls
m.rect(96, 5, 103, 33, " ")
m.hline(96, 103, 5, "-")                    # a log bridge over the skylight
m.put(95, 43, "----")
m.put(100, 40, "----")
m.put(96, 37, "---")
for i, y in enumerate(range(34, 6, -3)):
    m.put(101 if i % 2 == 0 else 96, y, "%%%")
# secret 2: a fake root wall at the hall's west end
m.rect(31, 42, 37, 45, "?")
m.put(38, 44, "X")
m.put(38, 45, "X")

# the root knot: an optional cave between the high road and the hall's east end (floor row 27)
m.rect(108, 15, 146, 26, ".")
m.rect(108, 15, 116, 17, "#")               # an uneven roof
m.rect(124, 15, 127, 16, "#")
m.rect(136, 15, 138, 17, "#")
m.rect(128, 27, 133, 27, ".")               # a dip with a crystal
m.rect(122, 24, 123, 26, "%")               # a ruin block
m.put(116, 24, "---")
m.put(119, 21, "---")
m.rect(139, 5, 142, 14, ".")                # the pit from the high road, logs both ways
for i, y in enumerate(range(24, 6, -3)):
    m.put(139 if i % 2 == 0 else 141, y, "--")
m.put(139, 7, "--")
m.rect(110, 27, 113, 31, ".")               # the shaft down to the hall, logs both ways
for x0, y in ((110, 40), (112, 37), (110, 34), (112, 31), (110, 28)):
    m.put(x0, y, "--")

# ---------------------------------------------------------------- the deep roots (banks: floor row 59)
m.rect(45, 46, 49, 49, ".")                 # the hole down from the hall, logs both ways
for i, y in enumerate(range(56, 46, -3)):
    m.put(45 if i % 2 == 0 else 48, y, "--")
m.rect(26, 50, 150, 58, ".")
m.rect(26, 50, 31, 53, "#")
m.rect(59, 59, 146, 59, ".")                # the river channel: acid rows 60-61
m.rect(59, 60, 146, 61, "~")
islands = [(63, 65, 57), (69, 70, 56), (77, 79, 57), (83, 84, 56), (89, 91, 57), (95, 96, 55), (102, 104, 57),
           (108, 109, 56), (115, 117, 57), (121, 122, 56), (128, 130, 57), (134, 135, 56), (141, 143, 57)]
for x0, x1, top in islands:
    m.rect(x0, top, x1, 61, "%")
for x0, x1, y in ((59, 62, 58), (71, 76, 57), (85, 88, 57), (97, 101, 57), (110, 114, 57), (123, 127, 57),
                  (136, 140, 58)):
    m.hline(x0, x1, y, "_")
for x0, x1, y in ((77, 80, 54), (92, 95, 52), (104, 106, 54), (118, 121, 52), (131, 133, 54)):
    m.hline(x0, x1, y, "-")
for x in (68, 81, 94, 107, 124, 137):       # roots hanging over the river
    m.rect(x, 50, x + 1, 51, "#")
# secret 3: a trapdoor (fake floor) in the west bank into a vault, a log to climb back out
m.rect(50, 59, 52, 60, "X")
m.rect(42, 61, 56, 63, "?")
m.put(50, 61, "-")

# the east shaft from the east bank up into the corridor to the blue door
m.rect(129, 42, 150, 45, ".")               # corridor, floor row 46
m.rect(147, 46, 150, 49, ".")
for i, y in enumerate(range(56, 46, -3)):
    m.put(147 if i % 2 == 0 else 149, y, "--")
m.rect(151, 43, 151, 45, "d")

# ---------------------------------------------------------------- the Tangle (x 152-201)
m.rect(152, 10, 201, 56, ".")
m.rect(152, 57, 201, 57, "#")
m.rect(158, 55, 194, 56, "~")               # acid at its foot
m.rect(152, 10, 159, 12, "#")               # an uneven roof with a high dome
m.rect(160, 6, 181, 9, ".")
m.rect(160, 6, 163, 7, "#")
tangle = [  # (x0, x1, top row, kind): terrain blocks are 2 rows thick
    (152, 158, 46, "#"), (161, 164, 44, "-"), (167, 171, 42, "#"), (174, 177, 40, "_"), (180, 184, 38, "#"),
    (187, 190, 36, "-"), (193, 199, 34, "#"), (189, 192, 31, "-"), (182, 186, 28, "%"), (175, 179, 26, "_"),
    (168, 172, 24, "#"), (161, 165, 22, "-"), (153, 158, 19, "#"), (160, 163, 16, "-"), (166, 170, 14, "_"),
    (174, 178, 13, "#"),
    (164, 168, 51, "#"), (160, 162, 48, "-"),          # a low ledge over the acid
    (195, 199, 51, "%"), (196, 199, 48, "-"),          # a ledge in the far corner with treasure
    (200, 201, 45, "-"), (197, 199, 42, "-"), (200, 201, 39, "-"), (200, 201, 36, "-"),   # and the way back up
]
for x0, x1, y, ch in tangle:
    if ch in "#%":
        m.rect(x0, y, x1, y + 1, ch)
    else:
        m.hline(x0, x1, y, ch)
m.rect(195, 53, 201, 56, "#")               # no dry floor at the bottom of the Tangle
m.rect(152, 48, 157, 56, "#")
m.rect(182, 12, 201, 13, "#")               # the exit ledge
m.rect(182, 0, 201, 11, " ")                # the sky over the exit
m.rect(182, 0, 183, 9, "#")

# ---------------------------------------------------------------- items
crystals = [
    (17, 8), (31, 22),                                   # surface, sinkhole
    (52, 31), (60, 28),                                  # gallery: pit, under the snapvine
    (44, 42), (57, 36), (90, 40), (102, 21), (97, 9), (122, 39),             # root hall + skylight
    (130, 3), (120, 20), (131, 27),                      # the high road, the root knot
    (27, 58), (70, 55), (96, 54), (122, 55), (145, 58),  # deep roots
    (162, 43), (166, 50), (196, 33), (184, 27), (155, 18), (176, 12),        # the Tangle
]
for x, y in crystals:
    m.set(x, y, "*")
treasure = [
    (10, 10), (12, 10), (22, 8), (23, 8), (24, 8), (34, 11),
    (33, 25), (30, 19), (40, 23), (42, 23), (44, 23), (51, 31), (53, 31), (55, 31), (59, 27), (61, 27),
    (50, 39), (51, 39), (60, 42), (81, 42), (82, 42), (87, 42), (113, 42), (114, 42), (119, 42),
    (97, 36), (98, 30), (102, 27), (97, 24), (98, 15), (102, 12),
    (50, 4), (60, 4), (70, 4), (80, 4), (90, 4), (110, 4), (125, 4), (135, 4), (140, 4), (145, 4), (160, 4),
    (135, 44), (138, 44), (141, 44),
    (78, 53), (79, 53), (93, 51), (94, 51), (119, 51), (120, 51), (64, 56), (90, 56), (116, 56), (142, 56),
    (36, 58), (40, 58),
    (169, 41), (183, 37), (198, 33), (190, 30), (170, 23), (162, 21), (157, 18), (161, 15), (168, 13),
    (197, 50), (198, 50), (197, 47), (198, 47),
    (112, 26), (117, 23), (118, 23), (125, 26), (126, 26), (134, 26), (144, 26), (145, 26), (140, 20),
]
for x, y in treasure:
    if m.get(x, y) in ". ":
        m.set(x, y, "$")
for x, y in [(13, 28), (14, 28), (15, 28), (16, 26), (17, 28)]:            # secret 1
    m.set(x, y, "$")
m.set(12, 28, "&")
for x, y in [(32, 45), (33, 45), (34, 45), (35, 43)]:                       # secret 2
    m.set(x, y, "$")
m.set(36, 45, "H")
for x, y in [(43, 63), (44, 63), (45, 63), (54, 63), (55, 63)]:            # secret 3
    m.set(x, y, "$")
m.set(47, 63, "c")                                                          # a crown
m.set(53, 63, "w")                                                          # overdrive

for x, y in [(35, 28), (65, 28), (58, 45), (100, 45), (30, 58), (100, 51), (140, 58), (176, 25), (157, 45)]:
    m.set(x, y, "+")
for x, y in [(124, 45), (147, 58), (170, 41)]:
    m.set(x, y, "H")
for x, y in [(21, 28), (47, 28), (70, 45), (110, 45), (146, 26), (33, 58), (105, 53), (149, 58), (185, 37), (162, 15),
             (130, 45)]:
    m.set(x, y, "&")

# ---------------------------------------------------------------- objects
m.set(6, 11, "P")
m.set(23, 28, "r")       # the ricochet
m.set(26, 28, "t")       # sign: ricochet
m.set(47, 27, "u")       # sign: crumble
m.set(57, 28, "q")       # sign: snapvines
m.set(38, 58, "C")       # checkpoint in the deep roots
m.set(154, 45, "C")      # checkpoint behind the blue door
m.set(148, 58, "k")      # blue key on the east bank
m.set(193, 11, "E")

# ---------------------------------------------------------------- enemies
for x, y in [(42, 28), (68, 28), (57, 45), (86, 45), (115, 45), (52, 58), (140, 45), (198, 11), (186, 11),
             (196, 33), (118, 26), (136, 26)]:
    if m.get(x, y) in ".":
        m.set(x, y, "b")     # beetles
for x, y in [(60, 24), (79, 36), (94, 36), (111, 36), (69, 52), (88, 52), (110, 52), (129, 52), (139, 52),
             (170, 45), (178, 41), (157, 21), (185, 30), (135, 43), (165, 15), (131, 20), (120, 19)]:
    if m.get(x, y) in ".":
        m.set(x, y, "n")     # snapvines hang from the ceiling above
for x, y in [(73, 45), (122, 45), (46, 58), (182, 37), (170, 23), (195, 33)]:
    if m.get(x, y) in ".":
        m.set(x, y, "j")     # leapers
for x, y in [(98, 45), (149, 58), (184, 27), (102, 56)]:
    if m.get(x, y) in ".":
        m.set(x, y, "J")

legend = [
    ("b", "enemy beetle"),
    ("j", "enemy leaper"),
    ("J", "enemy leaper ambush"),
    ("n", "enemy snapvine"),
    ("r", "weapon ricochet"),
    ("w", "power overdrive"),
    ("c", "treasure crown"),
    ("t", "sign sign.e2l2.ricochet"),
    ("u", "sign sign.e2l2.crumble"),
    ("q", "sign sign.e2l2.snapvine"),
]
header = [
    "# e2l2 Root Caverns -- built by tools/levels/e2/e2l2.py",
    "name      Root Caverns",
    "name.de   Wurzelhöhlen",
    "theme     jungle",
    "tint      1",
    "bg        jungle_b",
    "music     e2_jungle",
    "dark      0.3",
    "par       480",
]
m.save("e2l2", header, legend)
print(stats(m, legend))
run("e2l2", parts=[(0, 0, 40, 32), (36, 20, 50, 30), (80, 0, 50, 48), (24, 44, 60, 22), (80, 44, 70, 22),
                   (150, 8, 54, 52)])
