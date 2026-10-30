"""e2l9 Broodmother -- the queen's chamber at the heart of the hive.

A short approach (a tunnel and the Throat, a small cavern with a few crystals, a checkpoint, health and ammo), then a
drop into the arena: 38 wide, 14 rows high (the Broodmother flies), a flat floor with resin channels along the walls,
one-way platforms 3 rows above the floor and a second row higher up to dodge her dives. Health and ammo in the
corners, the exit in the arena (it opens when she dies). Once the hero drops in, the arena keeps him.
"""
from lvl import Map, run, stats, ladder

W, H = 106, 40
m = Map(W, H, "#")


def log(x0, x1, y):
    m.hline(x0, x1, y, "-")


def comb(x0, x1, y, rows=2):
    m.rect(x0, y, x1, y + rows - 1, "%")


# ---------------------------------------------------------------- the approach: a tunnel (floor 13)
m.rect(2, 7, 36, 12, ".")
m.rect(10, 7, 13, 8, "#")
m.rect(22, 7, 26, 7, "#")
comb(16, 18, 11, 2)
m.rect(28, 13, 30, 14, "~")
# the Throat: a cavern that winds down to the arena's door (floor 17 at the drop)
m.rect(37, 5, 58, 24, " ")
m.rect(37, 13, 41, 14, "#")                 # the tunnel's mouth
log(42, 46, 16)
comb(48, 52, 19)
log(43, 47, 22)
m.rect(37, 25, 58, 25, "~")                 # resin at its foot
m.rect(37, 26, 58, 27, "#")
log(53, 57, 22)
m.rect(54, 17, 60, 18, "#")                 # the ledge before the drop
log(49, 53, 13)
log(43, 46, 10)
comb(50, 54, 7, 2)
# the door in the arena's west wall: walk off the ledge and fall in
m.rect(59, 13, 61, 16, ".")
m.rect(61, 17, 61, 18, ".")

# ---------------------------------------------------------------- the arena (floor 28, rows 14-27 open)
m.rect(62, 14, 99, 27, ".")
m.rect(61, 19, 61, 27, ".")
m.rect(61, 14, 61, 16, ".")
m.rect(62, 28, 64, 28, "~")                 # resin channels along the walls
m.rect(97, 28, 99, 28, "~")
m.rect(62, 29, 64, 29, "#")
m.rect(97, 29, 99, 29, "#")
log(62, 64, 19)                             # a way back up to the door (crystals left in the approach)
log(66, 70, 25)                             # platforms 3 rows above the floor
log(78, 84, 25)
log(91, 95, 25)
log(71, 75, 21)                             # and a second row for her dives
log(86, 90, 21)
comb(62, 63, 22, 1)
comb(98, 99, 22, 1)
m.rect(62, 14, 99, 14, ".")
for x0, x1 in ((66, 70), (78, 84), (92, 96)):
    m.rect(x0, 13, x1, 13, ".")             # ribbed ceiling pockets
m.rect(61, 28, 61, 29, "#")

# ---------------------------------------------------------------- items and objects
for x, y in [(20, 10), (44, 15), (50, 18), (45, 21), (51, 6)]:
    m.set(x, y, "*")
for x, y in [(6, 12), (8, 12), (14, 12), (24, 12), (26, 12), (33, 12), (43, 9), (45, 9), (49, 12), (51, 12),
             (44, 21), (46, 21), (54, 21), (56, 21), (49, 18), (51, 18), (52, 6), (53, 6)]:
    if m.get(x, y) in ". ":
        m.set(x, y, "$")
m.set(4, 12, "P")
m.set(56, 16, "C")       # checkpoint before the drop
m.set(57, 16, "t")       # sign: do not disturb
m.set(55, 16, "H")
m.set(58, 16, "&")
m.set(32, 12, "+")
m.set(34, 12, "&")
m.set(65, 27, "H")       # health and ammo in the arena's corners
m.set(96, 27, "H")
m.set(66, 27, "&")
m.set(95, 27, "&")
m.set(74, 27, "E")       # the exit in the middle of the arena
m.set(92, 20, "!")       # the Broodmother, on the far side

# a few creatures in the approach
for x, y, ch in [(18, 10, "j"), (30, 9, "m"), (47, 9, "m"), (44, 21, "y"), (24, 12, "J")]:
    if m.get(x, y) in ". ":
        m.set(x, y, ch)

legend = [
    ("!", "boss broodmother"),
    ("j", "enemy leaper"),
    ("m", "enemy mothling"),
    ("J", "enemy leaper ambush"),
    ("y", "enemy spitter"),
    ("t", "sign sign.e2l9.boss"),
]
header = [
    "# e2l9 Broodmother -- built by tools/levels/e2/e2l9.py",
    "name      Broodmother",
    "name.de   Brutmutter",
    "theme     hive",
    "tint      3",
    "bg        hive_b",
    "music     boss",
    "dark      0.25",
    "par       180",
]
m.save("e2l9", header, legend)
print(stats(m, legend))
run("e2l9", parts=[(0, 2, 62, 28), (56, 8, 50, 26)])
