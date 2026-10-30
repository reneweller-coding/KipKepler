"""e1l7 Antenna Field -- a vertical climb on the outer hull in low gravity (0.8): movers, springbots.

Low gravity: a jump reaches ~4.2 tiles, a spring ~14. The climb still uses 3-row steps so it stays comfortable.
Route (bottom to top, everything falls back to the hull surface, nothing below is deadly):
the antenna roots (airlock start, ledges, a ferry mover, a spring onto the first dish) -> the dish cluster (a lift
mover) -> a ferry west and a staircase of antenna housings (checkpoint) -> a lift up to the relay tower -> inside the
tower: one-way rungs, springbots, turrets (checkpoint) -> out onto the array: a ferry, a spring, the last housings ->
the summit platform with the exit. Side perches hold crystals and treasure; three fake-wall secrets.
"""
import lvl

W, H = 84, 120
m = lvl.Map(W, H)
m.rect(1, 1, W - 2, 111, ' ')       # open space down to the hull surface (row 112)


def ledge(x0, x1, s, ch='%'):
    """A ledge to stand on at row s (solid at s + 1)."""
    m.hline(x0, s + 1, x1 - x0 + 1, ch)


# ---------------------------------------------------------------- A: the antenna roots (rows 95..111)
m.rect(1, 102, 13, 10, '#')         # airlock block, roof stand 101
m.put(4, 102, '%%%%%%%%%%')
m.rect(5, 106, 8, 6, '.')           # airlock
m.rect(13, 108, 1, 4, '.')          # its door
m.put(7, 111, 'P')
m.put(10, 111, '$')
# Secret 1: a locker behind the airlock's back wall.
m.rect(4, 110, 1, 2, 'X')
m.rect(1, 109, 3, 3, '?')
m.put(1, 111, '$H$')
m.put(15, 111, '1')                 # sign: low gravity
m.put(17, 111, 's')                 # spring onto the airlock roof
m.put(6, 101, '*')
m.put(9, 101, '$$')
ledge(6, 11, 98, '-')
m.put(8, 97, '$`$')
ledge(20, 24, 108)
ledge(27, 31, 105)
ledge(34, 38, 102)
m.put(29, 104, '$')
m.put(36, 101, '*')
m.put(41, 103, 'aaa')               # ferry east: x 41..43 -> 50..52
m.put(46, 99, '$')
ledge(54, 58, 102, '#')
m.rect(55, 104, 3, 4, '#')          # the root mast (hangs; walk under it)
m.put(58, 102, 's')                 # spring onto the first dish
m.put(66, 111, 'h')
m.put(30, 111, 'h')
m.rect(68, 109, 3, 3, '%')
m.put(69, 108, '*')
m.put(75, 111, '$`$')
m.put(80, 111, '*')
m.put(20, 85, 'g')
m.put(30, 78, 'm')
m.put(48, 94, 'm')
m.put(22, 100, 'g')

# ---------------------------------------------------------------- B: the dish cluster (rows 68..94)
ledge(48, 64, 90, '-')              # the first dish, stand 90
m.rect(47, 89, 1, 2, '%')
m.rect(65, 89, 1, 2, '%')
m.put(56, 89, '*')
m.put(51, 89, '$$')
m.put(61, 89, '$$')
ledge(67, 71, 87)
ledge(73, 77, 84)
m.put(76, 83, '$')
m.put(69, 86, '*')
m.put(79, 85, 'bbb')                # lift: x 79..81, rows 85 -> 72
ledge(72, 77, 71)
m.put(80, 67, '*')                  # a jump off the lift's top reaches it
m.put(74, 71, 'h')
m.put(70, 80, 'g')
ledge(64, 70, 68, '-')
m.put(65, 67, '$$$')

# ---------------------------------------------------------------- C: ferry west, antenna housings (rows 55..70)
m.put(61, 69, 'ccc')                # ferry west: x 61..63 -> 49..51
ledge(43, 47, 68)
m.put(45, 68, 'C')
ledge(36, 40, 65)
ledge(29, 33, 62)
ledge(22, 26, 59)
ledge(15, 19, 56)
m.put(31, 62, '*')
m.put(17, 56, '*')
m.put(24, 59, '$$')
m.put(39, 65, 'h')
m.put(36, 64, '*')
m.put(40, 57, 'm')
m.put(30, 54, 'g')
m.put(11, 57, 'nnn')                # lift: x 11..13, rows 57 -> 47
ledge(1, 7, 52)                     # a perch beside the lift
m.put(3, 52, '$i$')
m.put(5, 47, 'm')

# ---------------------------------------------------------------- D: the relay tower (x 22..45, rows 26..47)
ledge(15, 21, 46)
m.put(17, 46, '*')
m.rect(22, 26, 24, 22, '#')
m.rect(23, 27, 22, 20, '.')
m.rect(22, 44, 1, 3, '.')           # door from the lift side
m.put(25, 46, 'C')
for i, s in enumerate((43, 40, 37, 34, 31)):
    if i % 2 == 0:
        ledge(32, 43, s, '-')
    else:
        ledge(23, 34, s, '-')
ledge(23, 44, 28, '-')              # the top rung runs to the upper door
m.rect(45, 27, 1, 2, '.')           # top door out onto the array
m.put(40, 43, '*')
m.put(26, 34, '*')
m.put(41, 28, '*')
m.put(28, 40, '$$')
m.put(38, 37, '$$')
m.put(35, 31, '$')
m.put(42, 30, '*')
m.put(65, 40, 'm')
m.put(39, 46, 'h')
m.put(42, 46, '+')
m.put(30, 27, 't')                  # ceiling turret
m.put(38, 36, 'f')
m.put(28, 39, 'h')
for (lx, ly) in ((24, 29), (43, 38), (24, 44)):
    m.put(lx, ly, 'L')
# Secret 2: a cable bay on the tower's east side, through a fake wall from rung 37.
m.rect(46, 34, 5, 5, '#')
m.rect(45, 36, 1, 2, 'X')
m.rect(46, 35, 4, 3, '?')
m.put(46, 37, '$&$o')

# ---------------------------------------------------------------- E: the array and the summit (rows 5..28)
ledge(46, 52, 28)
m.put(55, 29, 'eee')                # ferry east: x 55..57 -> 65..67
ledge(70, 76, 28)
m.put(75, 28, 's')                  # spring to the upper array
m.put(74, 28, '*')
ledge(64, 76, 16, '-')
m.put(66, 16, '*')
m.put(70, 16, '$$$')
ledge(57, 62, 13)
ledge(49, 54, 10)
m.put(59, 13, '*')
m.put(50, 28, 'h')
m.put(72, 27, 'f')
m.put(51, 10, '*')
m.rect(28, 9, 18, 3, '#')           # summit platform, stand 8
m.put(28, 9, '%%%%%%%%%%%%%%%%%%')
m.put(37, 8, 'E')
m.put(32, 8, '*')
m.put(42, 8, '$$')
m.put(29, 8, 't')
m.put(61, 21, 'm')
m.put(48, 18, 'g')
m.put(56, 6, 'g')
# Secret 3: a relay box at the east end of the upper array.
m.rect(77, 12, 5, 6, '#')
m.rect(77, 15, 1, 2, 'X')
m.rect(78, 14, 3, 3, '?')
m.put(78, 16, '$H$')

# antenna masts (decoration on structure ends, off the route)
m.rect(24, 21, 1, 5, '#')           # on the relay tower's roof
m.rect(31, 23, 1, 3, '#')
m.rect(47, 84, 1, 5, '#')           # dish rim masts
m.rect(28, 4, 1, 5, '#')            # summit mast
m.rect(81, 8, 1, 4, '#')            # on the relay box
m.rect(1, 97, 1, 5, '#')            # airlock antenna
# a lattice perch in the empty middle with treasure, reached from the ferry west
ledge(52, 55, 65, '-')
ledge(57, 60, 62, '-')
ledge(52, 55, 59, '-')
ledge(56, 61, 56, '%')
m.rect(61, 44, 1, 12, '#')          # its mast
m.put(57, 55, '$$$$')
# health, ammo and enemies topped up after the first review
m.place(74, 84, '+')
m.place(47, 28, '&')
m.place(43, 68, '&')
m.border()

header = [
    ('name', 'Antenna Field'),
    ('name.de', 'Antennenfeld'),
    ('theme', 'hull'),
    ('tint', '1'),
    ('bg', 'hull_b'),
    ('music', 'e1_hull'),
    ('dark', '0.15'),
    ('par', '360'),
    ('gravity', '0.8'),
]
legend = {
    'h': 'enemy springbot',
    'g': 'enemy hoverdrone ambush',
    'm': 'enemy sparkmine',
    't': 'enemy turret',
    'f': 'enemy sentry left',
    's': 'spring',
    'a': 'mover 9 0 70',
    'b': 'mover 0 -13 80',
    'c': 'mover -12 0 70',
    'n': 'mover 0 -10 80',
    'e': 'mover 10 0 70',
    'i': 'treasure idol',
    'o': 'power shield',
    'L': 'light cyan 5',
    '1': 'sign sign.e1l7.gravity',
}

if __name__ == '__main__':
    lvl.write('e1l7', header, legend, m)
    lvl.check('e1l7')
