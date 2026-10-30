"""e2l4 The Sunken Temple -- a temple swallowed by the jungle: ruins, switch puzzles, teleporters, many secrets.

Route: the jungle floor at dusk -> up the pyramid tip and down its shaft -> the antechamber (switch lesson: switch A
opens the gate) -> the corridor -> the atrium, a collapsed hall open to the sky (checkpoint) -> the east wing
(switch B raises a bridge over the acid AND opens the sanctum's first gate) -> the east tower down to gate B ->
the crypt under the atrium: three chambers joined by teleporter pads (lesson sign), switch C in the last one opens
the sanctum's inner gate (checkpoint) -> the sanctum and the exit; a pad there leads back to the antechamber.
Teleporters are one way: each sending pad has an arrival pad (a pad without a target) somewhere else.
Secrets: a chamber in the pyramid's base (fake wall), a niche behind breakable stones in the antechamber, the
tower's attic (fake wall), a vault under crypt chamber 1 (fake floor, a pad back up).
"""
from lvl import Map, run, stats

W, H = 196, 68
m = Map(W, H, "#")

# ---------------------------------------------------------------- the jungle floor and the pyramid tip
m.ground([(0, 195, 16)])
m.rect(36, 20, 195, 66, "%")                # the temple's stone, under an earth crust
for x0, y0, x1, y1 in ((36, 20, 43, 32), (56, 44, 75, 48), (140, 60, 160, 66), (110, 40, 125, 44),
                       (36, 58, 50, 66), (170, 20, 195, 26), (126, 34, 148, 38)):
    m.rect(x0, y0, x1, y1, "#")             # earth where the temple collapsed
m.rect(40, 13, 64, 15, "%")                 # pyramid steps (3 rows each)
m.rect(44, 10, 60, 12, "%")
m.rect(48, 7, 56, 9, "%")
m.rect(51, 7, 53, 20, ".")                  # the shaft down into the antechamber
# secret 1: a chamber in the pyramid's base behind a fake wall
m.rect(56, 14, 63, 15, "?")
m.rect(64, 14, 64, 15, "X")
# the surface: ruins, acid pools, old stones
m.rect(14, 15, 16, 15, "%")
m.rect(24, 14, 25, 15, "%")
m.rect(70, 16, 74, 16, "~")
m.rect(120, 14, 122, 15, "%")
m.rect(121, 12, 121, 13, "%")
m.rect(140, 16, 144, 16, "~")
m.rect(160, 15, 161, 15, "%")
m.rect(176, 13, 178, 15, "%")
m.put(175, 12, "%%%%%")

# the cistern under the jungle floor: a well down, old water channels turned to acid (floor 34)
m.rect(4, 24, 33, 33, ".")
m.rect(28, 16, 30, 23, ".")
m.rect(4, 24, 9, 27, "#")
m.rect(22, 24, 26, 25, "#")
m.rect(14, 34, 19, 35, "~")
m.rect(14, 36, 19, 36, "#")
m.rect(10, 31, 12, 33, "%")
m.rect(21, 31, 22, 33, "%")
m.put(14, 30, "------")
m.put(5, 30, "----")
for i, y in enumerate(range(31, 17, -3)):
    m.put(28 if i % 2 == 0 else 29, y, "--")

# ---------------------------------------------------------------- the antechamber (floor 27) and the corridor
m.rect(44, 21, 62, 26, ".")
m.rect(47, 25, 47, 26, "%")                 # broken pillars
m.rect(57, 25, 57, 26, "%")
for i, y in enumerate(range(24, 7, -3)):    # logs up the shaft (both ways)
    m.put(51 if i % 2 == 0 else 52, y, "--")
m.rect(63, 24, 63, 26, "g")                 # gate A
m.rect(64, 23, 89, 26, ".")                 # corridor, floor 27
m.rect(70, 27, 74, 28, ".")                 # a spike pit with a crumble lid
m.rect(70, 29, 74, 29, "^")
m.hline(70, 74, 27, "_")
m.rect(80, 22, 84, 22, ".")                 # a pocket in the corridor's roof
# secret 2: a niche west of the antechamber behind breakable stones (shoot them)
m.rect(43, 25, 43, 26, "B")
m.rect(37, 24, 42, 26, "?")

# ---------------------------------------------------------------- the atrium: open to the sky (floor 45)
m.rect(90, 0, 104, 44, " ")
m.rect(90, 45, 95, 45, "%")
m.rect(100, 45, 104, 45, "%")
m.rect(96, 45, 99, 46, "~")                 # acid at its foot
m.hline(97, 101, 42, "-")                   # log scaffolding up the atrium (the logs overlap in the middle)
for y in (39, 33, 27, 21):
    m.hline(90, 97, y, "-")                 # west
for y in (36, 30, 24, 18):
    m.hline(97, 104, y, "-")                # east
for y in (33, 21):
    m.rect(90, y + 1, 91, y + 1, "%")       # old stone brackets under some logs
for y in (30, 18):
    m.rect(103, y + 1, 104, y + 1, "%")
m.rect(89, 23, 89, 26, ".")                 # the corridor's mouth on ledge 27
m.rect(105, 26, 105, 29, ".")               # the east wing's mouth on ledge 30
m.rect(89, 42, 89, 44, ".")                 # the way down to the crypt from the atrium floor
m.rect(80, 42, 88, 44, ".")
m.rect(80, 45, 82, 50, ".")

# ---------------------------------------------------------------- the east wing (floor 30): switch B and the bridge
m.rect(106, 24, 149, 29, ".")
for x in (110, 114, 136, 142):
    m.rect(x, 27, x, 29, "%")               # broken pillars
m.rect(121, 30, 129, 30, "o")               # bridge B: there while B is on
m.rect(121, 31, 129, 32, "~")
m.rect(132, 22, 140, 23, ".")
m.put(132, 27, "---")

# ---------------------------------------------------------------- the east tower (floor 45)
m.rect(150, 27, 150, 29, ".")
m.rect(151, 18, 165, 44, ".")
for y in (42, 36, 30, 24):
    m.hline(151, 158, y, "-")
for y in (39, 33, 27, 21):
    m.hline(158, 165, y, "-")
for y in (36, 24):
    m.rect(151, y + 1, 152, y + 1, "%")
for y in (39, 27):
    m.rect(164, y + 1, 165, y + 1, "%")
# secret 3: the tower's attic behind a fake wall
m.rect(143, 20, 149, 23, "?")
m.rect(150, 22, 150, 23, "X")
m.rect(166, 42, 166, 44, "i")               # gate B

# ---------------------------------------------------------------- the sanctum (floor 45)
m.rect(167, 30, 192, 44, ".")
m.rect(180, 40, 180, 44, "y")               # gate C
m.rect(180, 30, 180, 39, "%")
for x0, x1, y in ((168, 172, 42), (174, 178, 39), (168, 171, 36), (174, 178, 33), (182, 186, 42), (188, 192, 39),
                  (182, 185, 36)):
    m.hline(x0, x1, y, "-")

# ---------------------------------------------------------------- the crypt: three chambers and teleporters
m.rect(60, 51, 95, 58, ".")                 # chamber 1, floor 59
m.rect(80, 49, 82, 50, ".")
m.rect(66, 56, 68, 58, "%")
m.rect(87, 56, 88, 58, "%")
m.put(83, 53, "---")
m.rect(40, 48, 57, 56, ".")                 # chamber 2, floor 57 (only by teleporter)
m.rect(46, 54, 47, 56, "%")
m.put(49, 53, "----")
m.put(42, 51, "---")
m.rect(100, 52, 136, 62, ".")               # chamber 3, floor 63 (only by teleporter)
m.rect(108, 60, 112, 62, "%")
m.rect(118, 57, 125, 58, "%")
m.put(114, 60, "---")
m.put(127, 60, "---")
m.rect(130, 60, 130, 62, "%")
for x0, y in ((80, 56), (81, 53), (80, 50), (81, 47)):   # logs up to the crypt corridor
    m.put(x0, y, "--")
# secret 4: a fake floor in chamber 1 drops into a vault; a pad leads back up
m.rect(74, 59, 76, 60, "X")
m.rect(70, 61, 82, 63, "?")

# ---------------------------------------------------------------- objects
m.set(5, 15, "P")
m.set(45, 26, "S")       # switch A (the antechamber's west end)
m.set(49, 26, "t")       # sign: switches
m.set(118, 29, "T")      # switch B, before the acid pit
m.set(133, 62, "U")      # switch C, at the end of chamber 3
m.set(62, 58, "u")       # sign: teleporters
m.set(64, 58, "1")       # chamber 1 -> chamber 2
m.set(41, 56, "(")
m.set(56, 56, "2")       # chamber 2 -> chamber 3
m.set(102, 62, ")")
m.set(135, 62, "3")      # chamber 3 -> chamber 1
m.set(93, 58, "[")
m.set(81, 63, "4")       # vault -> chamber 1
m.set(91, 58, "]")
m.set(191, 44, "5")      # sanctum -> antechamber
m.set(60, 26, "{")
m.set(92, 44, "C")       # checkpoint on the atrium floor
m.set(104, 62, "C")      # checkpoint in chamber 3
m.set(187, 44, "E")

# ---------------------------------------------------------------- items
crystals = [
    (52, 6), (20, 15), (150, 15), (6, 33), (16, 29),
    (59, 26), (86, 26), (82, 22),
    (99, 41), (103, 29), (93, 20),
    (108, 29), (125, 29), (136, 22),
    (154, 41), (162, 20),
    (70, 58), (84, 52), (44, 50), (52, 52), (110, 59), (122, 56),
    (170, 41), (176, 32), (190, 38),
]
for x, y in crystals:
    m.set(x, y, "*")
treasure = [
    (10, 15), (12, 15), (30, 15), (32, 15), (46, 12), (58, 12), (50, 9), (54, 9), (66, 15), (68, 15),
    (80, 15), (86, 15), (5, 29), (7, 29), (11, 30), (15, 29), (18, 29), (24, 33), (26, 33), (110, 15), (130, 15), (165, 15), (170, 15),
    (50, 26), (55, 26), (66, 26), (68, 26), (71, 26), (73, 26), (81, 22), (83, 22),
    (96, 41), (92, 38), (94, 38), (101, 35), (103, 35), (92, 32), (94, 32), (101, 23), (95, 26), (91, 20),
    (112, 25), (116, 29), (122, 28), (124, 28), (127, 28), (133, 25), (138, 21), (145, 29), (147, 29),
    (153, 35), (155, 29), (161, 38), (163, 32), (154, 23), (161, 26),
    (62, 54), (64, 54), (77, 58), (79, 58), (85, 52), (42, 50), (43, 50), (50, 52), (54, 56),
    (103, 59), (106, 59), (115, 59), (116, 59), (120, 56), (124, 56), (128, 59), (131, 62),
    (169, 41), (171, 41), (175, 38), (177, 38), (169, 35), (175, 32), (183, 41), (185, 41), (183, 35), (191, 38),
]
for x, y in treasure:
    if m.get(x, y) in ". ":
        m.set(x, y, "$")
for x, y in [(57, 15), (58, 15), (59, 15), (61, 15)]:                     # secret 1
    m.set(x, y, "$")
m.set(62, 15, "&")
for x, y in [(38, 26), (39, 26), (41, 26)]:                                # secret 2
    m.set(x, y, "$")
m.set(40, 26, "H")
for x, y in [(144, 23), (145, 23), (146, 23), (148, 23)]:                 # secret 3
    m.set(x, y, "$")
m.set(147, 23, "w")                                                        # overdrive
for x, y in [(71, 63), (72, 63), (73, 63), (77, 63), (78, 63)]:           # secret 4
    m.set(x, y, "$")
m.set(75, 63, "c")
m.set(79, 63, "&")

for x, y in [(34, 15), (32, 33), (61, 26), (88, 26), (94, 44), (107, 29), (146, 29), (160, 44), (90, 58), (45, 56),
             (101, 62), (168, 44), (184, 44)]:
    if m.get(x, y) in ". ":
        m.set(x, y, "+")
for x, y in [(56, 26), (8, 33), (85, 26), (102, 44), (131, 29), (156, 44), (61, 58), (48, 56), (126, 62), (172, 44)]:
    if m.get(x, y) in ". ":
        m.set(x, y, "&")

# lights (dark level): warm torches in the halls, green glow in the crypt
for x, y in [(46, 22), (55, 22), (66, 24), (78, 24), (88, 24), (108, 25), (118, 25), (128, 25), (140, 25),
             (148, 25), (153, 28), (163, 31), (153, 38), (170, 31), (178, 35), (186, 31), (191, 42)]:
    if m.get(x, y) in ".":
        m.set(x, y, "L")
for x, y in [(65, 52), (77, 52), (90, 52), (44, 52), (54, 49), (104, 54), (116, 54), (128, 54), (134, 56),
             (75, 62), (81, 46), (84, 43), (8, 30), (20, 27), (31, 27)]:
    if m.get(x, y) in ".":
        m.set(x, y, "G")

# ---------------------------------------------------------------- enemies
for x, y in [(28, 15), (24, 33), (110, 15), (171, 44), (152, 15), (68, 26), (112, 29), (145, 29), (75, 58), (115, 62), (175, 44)]:
    if m.get(x, y) in ". ":
        m.set(x, y, "b")     # beetles
for x, y in [(85, 23), (128, 24), (156, 19), (72, 51), (52, 49), (108, 53), (124, 53), (186, 31), (16, 24)]:
    if m.get(x, y) in ".":
        m.set(x, y, "n")     # snapvines
for x, y in [(97, 10), (96, 30), (100, 24), (158, 34), (172, 37), (188, 34), (120, 21)]:
    if m.get(x, y) in ". ":
        m.set(x, y, "m")     # mothlings
for x, y in [(40, 15), (12, 30), (133, 29), (155, 44), (88, 58), (50, 56), (128, 62), (190, 44)]:
    if m.get(x, y) in ". ":
        m.set(x, y, "j")     # leapers
for x, y in [(120, 29), (164, 44), (60, 15)]:
    if m.get(x, y) in ". ":
        m.set(x, y, "J")

legend = [
    ("b", "enemy beetle"),
    ("j", "enemy leaper"),
    ("J", "enemy leaper ambush"),
    ("m", "enemy mothling"),
    ("n", "enemy snapvine"),
    ("S", "switch A"),
    ("g", "toggle A solid"),
    ("T", "switch B"),
    ("i", "toggle B solid"),
    ("o", "toggle B empty"),
    ("U", "switch C"),
    ("y", "toggle C solid"),
    ("1", "teleport ("),
    ("(", "teleport"),
    ("2", "teleport )"),
    (")", "teleport"),
    ("3", "teleport ["),
    ("[", "teleport"),
    ("4", "teleport ]"),
    ("]", "teleport"),
    ("5", "teleport {"),
    ("{", "teleport"),
    ("w", "power overdrive"),
    ("c", "treasure crown"),
    ("L", "light warm 6"),
    ("G", "light green 5"),
    ("t", "sign sign.e2l4.switch"),
    ("u", "sign sign.e2l4.teleport"),
]
header = [
    "# e2l4 The Sunken Temple -- built by tools/levels/e2/e2l4.py",
    "name      The Sunken Temple",
    "name.de   Der versunkene Tempel",
    "theme     jungle",
    "tint      3",
    "bg        jungle_b",
    "music     e2_jungle",
    "dark      0.4",
    "par       480",
]
m.save("e2l4", header, legend)
print(stats(m, legend))
run("e2l4", parts=[(0, 0, 70, 30), (40, 14, 70, 34), (100, 12, 70, 36), (36, 44, 104, 24), (150, 26, 46, 22)])
