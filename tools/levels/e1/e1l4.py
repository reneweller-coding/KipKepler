"""e1l4 Outer Hull -- outdoors on the ring's skin: springs, sparkmines, ambushes, plasma pits.

Route (west to east, everything walkable both ways): airlock (start) -> first spring under a one-way platform
(taught safely, nothing to fall into) -> radiator fins and the first plasma pits, a spring over a plasma pool with a
platform above it -> checkpoint -> the sensor dish: a zig-zag of ledges up its pylon (or a spring shortcut), the
dish itself with ambush drones -> the crawlway under the hull (in through one hatch, out through a spring hatch;
a fake-wall secret) -> checkpoint -> the spring hop across the plasma conduit (islands with springs) -> the docking
clamp tower (spring to its top, a fake-wall alcove) -> the exit airlock.
"""
import lvl

W, H = 170, 48
S = 36                              # the hull surface row (solid); the hero stands on row 35
m = lvl.Map(W, H)
m.rect(1, 1, W - 2, S - 1, ' ')     # open space rows 1..35


def pool(x0, x1):
    """A plasma pit in the surface: one open row, then plasma."""
    m.rect(x0, S, x1 - x0 + 1, 1, ' ')
    m.rect(x0, S + 1, x1 - x0 + 1, 2, '~')


# ---------------------------------------------------------------- Z1 airlock and the first spring (x 1..28)
m.rect(1, 26, 10, 4, '#')           # airlock roof, stand 25
m.put(1, 26, '%%%%%%%%%%')
m.rect(2, 30, 8, 6, '.')            # airlock (start)
m.rect(10, 30, 1, 2, '#')           # door frame, open rows 32..35
m.put(4, 35, 'P')
m.put(7, 35, '$')
m.hline(3, 23, 5, '-')              # a perch over the airlock, stand 22
m.put(5, 22, '*')
m.put(8, 25, '$$')
m.put(14, 35, '1')                  # sign: springs
m.put(17, 35, 's')
m.hline(13, 27, 7, '-')             # landing over the spring, stand 26
m.put(17, 26, '*')
m.put(17, 32, '$')
m.put(17, 29, '$')
m.put(15, 26, '$')
m.rect(20, 34, 7, 2, '#')           # a raised hull plate, stand 33
m.put(20, 34, '%%%%%%%')
m.put(23, 33, 'a')

# ---------------------------------------------------------------- Z2 radiator fins and plasma (x 28..63)
m.rect(30, 34, 1, 2, '%')
m.rect(33, 33, 1, 3, '%')
m.rect(36, 34, 1, 2, '%')
m.put(33, 32, '*')
m.put(34, 27, 'm')
m.put(31, 33, '$')
m.put(35, 33, '$')
pool(40, 42)
m.put(41, 32, '$')
m.put(44, 35, '2')                  # sign: plasma
pool(47, 55)
m.put(45, 35, 's')
m.hline(48, 28, 8, '-')             # platform over the pool, stand 27
m.put(52, 27, '*')
m.put(49, 27, '$`$')
m.put(54, 27, '$')
m.put(58, 35, 's')                  # the spring back
m.put(51, 31, 'm')
m.put(53, 22, 'b')
pool(60, 62)
m.put(61, 32, '*')

# ---------------------------------------------------------------- Z3 sensor dish and the crawlway (x 64..104)
m.put(66, 35, 'C')
m.put(72, 35, 's')                  # spring shortcut up the pylon
m.put(72, 25, '*')
m.rect(82, 19, 3, 17, '#')          # pylon
m.rect(76, 33, 6, 3, '%')           # base, stand 32
m.hline(79, 30, 3, '%')             # L1, stand 29
m.hline(76, 27, 3, '%')             # L2, stand 26
m.hline(79, 24, 3, '%')             # L3, stand 23
m.hline(76, 21, 3, '%')             # L4, stand 20
m.put(80, 23, '*')
m.put(77, 26, '$$')
m.put(80, 29, '$')
m.hline(74, 18, 19, '-')            # the dish, stand 17
m.rect(73, 16, 1, 3, '%')
m.rect(93, 16, 1, 3, '%')
m.put(83, 17, '*')
m.put(78, 17, '$$$')
m.put(87, 17, '$$$')
m.put(93, 15, 't')                  # turret on the dish rim
m.put(77, 13, 'g')
m.put(90, 12, 'g')
m.put(84, 11, 'm')
m.put(97, 35, 'f')
# the crawlway (x 68..102, rows 39..44)
m.rect(68, 39, 35, 6, '.')
m.rect(100, 36, 2, 3, '.')          # hatch B: the way in
m.rect(69, 36, 2, 3, '.')           # hatch A: out by the spring
m.put(69, 44, 's')
m.rect(78, 43, 3, 2, '%')
m.put(79, 42, '*')
m.rect(88, 42, 2, 3, '%')
m.put(88, 41, '$$')
m.put(84, 44, '$$$')
m.put(96, 44, '*')
m.put(92, 44, '+')
m.put(82, 44, 'a')
m.put(94, 44, 'c')
m.put(73, 44, '3')                  # sign: hatch spring
# Secret 1: a store room west of the crawlway behind a fake wall.
m.rect(67, 43, 1, 2, 'X')
m.rect(60, 41, 7, 4, '?')
m.put(61, 44, '$h$&$')

# ---------------------------------------------------------------- Z4 the plasma conduit (x 104..140)
m.put(106, 35, 'C')
m.put(112, 35, 's')
pool(114, 133)
m.rect(119, 33, 3, 3, '#')          # island 1, stand 32
m.put(120, 32, 's')
m.put(119, 32, '*')
m.rect(126, 33, 3, 3, '#')          # island 2, stand 32
m.put(127, 32, 's')
m.put(128, 32, '$')
m.put(135, 35, 's')                 # the spring back
m.hline(136, 26, 4, '-')            # perch over it, stand 25
m.put(138, 25, '*')
m.put(123, 22, '*')
m.put(116, 26, '$')
m.put(130, 25, '$')
m.put(117, 21, 'm')
m.put(124, 18, 'm')
m.put(131, 22, 'm')
m.put(98, 24, 'b')
m.put(139, 30, 'g')

# ---------------------------------------------------------------- Z5 docking clamp and the exit airlock (x 140..168)
m.rect(148, 22, 5, 14, '#')         # clamp tower, top stand 21
m.put(148, 22, '%%%%%')
m.hline(145, 33, 3, '%')            # W1, stand 32
m.hline(142, 30, 3, '%')            # W2, stand 29
m.hline(142, 27, 6, '-')            # W3, stand 26
m.put(143, 26, 's')                 # spring to the tower top
m.put(154, 35, 's')                 # and the way back from the east: spring, two perches
m.hline(153, 27, 4, '-')            # E1, stand 26
m.hline(153, 24, 4, '-')            # E2, stand 23
m.put(146, 32, '*')
m.put(143, 29, '*')
m.put(150, 21, '*')
m.put(152, 21, 't')
m.put(146, 26, '$')
m.put(149, 21, '$')
m.put(155, 23, '$')
# Secret 2: a hollow in the clamp tower, through a fake wall from W3.
m.rect(148, 25, 1, 2, 'X')
m.rect(149, 24, 3, 3, '?')
m.put(149, 26, '$H$')
m.put(154, 26, 'm')
m.put(156, 35, 'c')
m.put(142, 35, 'f')
m.put(160, 24, 'g')
# exit airlock
m.rect(159, 26, 10, 4, '#')
m.put(159, 26, '%%%%%%%%%%')
m.rect(160, 30, 8, 6, '.')
m.rect(159, 30, 1, 2, '#')
m.put(164, 35, 'E')
m.put(166, 35, '*')
m.put(161, 35, '$')
# Secret 3: a cache on the exit airlock's roof, behind its antenna housing.
m.rect(163, 22, 6, 4, '%')
m.rect(163, 23, 1, 2, 'X')
m.rect(164, 23, 3, 2, '?')
m.put(164, 24, '$i$')
m.put(160, 25, '$')

# armour plating on parts of the surface
for x0, x1 in ((28, 39), (63, 68), (71, 75), (102, 111), (157, 158)):
    m.hline(x0, S, x1 - x0 + 1, '%')
# nothing lives above row 10: trim the empty sky
m.g = [m.g[0]] + m.g[7:]
m.h = len(m.g)
# health, ammo and enemies topped up after the first review
m.place(90, 28, '+')
m.place(139, 28, '+')
m.place(64, 28, '&')
m.place(108, 28, '&')
m.border()

header = [
    ('name', 'Outer Hull'),
    ('name.de', 'Außenhülle'),
    ('theme', 'hull'),
    ('tint', '0'),
    ('bg', 'hull_a'),
    ('music', 'e1_hull'),
    ('dark', '0.1'),
    ('par', '300'),
]
legend = {
    'a': 'enemy sweeper',
    'c': 'enemy sweeper left',
    'b': 'enemy hoverdrone',
    'g': 'enemy hoverdrone ambush',
    'f': 'enemy sentry left',
    'm': 'enemy sparkmine',
    't': 'enemy turret',
    's': 'spring',
    'h': 'power shield',
    'i': 'treasure idol',
    '1': 'sign sign.e1l4.spring',
    '2': 'sign sign.e1l4.plasma',
    '3': 'sign sign.e1l4.hatch',
}

if __name__ == '__main__':
    lvl.write('e1l4', header, legend, m)
    lvl.check('e1l4')
