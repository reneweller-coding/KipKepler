"""e1l5 Reactor Spine -- dark, laser fences, switches and toggle blocks, the gold key, lights.

Three decks (upper U, middle M, lower L) around the reactor spine, a shaft with plasma at its bottom.
Route: U west (start; laser fences taught on a flat floor) -> grating bridge over the spine -> switch A opens a
bulkhead (touch or shoot; a second switch on the far side) -> east shaft down to M east (ceiling turrets, lasers)
-> shoot switch B: a bridge appears across the spine -> M west pump hall -> west shaft down to L west, where the
gold door hides the exit -> switch C: a bridge over the plasma -> L east laser gauntlet -> shoot switch D: the key
vault opens -> GOLD KEY -> back west over bridge C -> the gold door -> exit.
The spine itself is a climbable connector (one-way rungs between the bridges, horizontal lasers across it).
Every switch has a twin on the other side, so every part can be revisited.
"""
import lvl

W, H = 150, 60
m = lvl.Map(W, H)
U0, U1 = 4, 12                      # upper deck rows (floor 13)
M0, M1 = 19, 30                     # middle deck rows (floor 31)
L0, L1 = 38, 50                     # lower deck rows (floor 51)
m.rect(2, U0, 146, U1 - U0 + 1, '.')
m.rect(2, M0, 146, M1 - M0 + 1, '.')
m.rect(2, L0, 146, L1 - L0 + 1, '.')

# ---------------------------------------------------------------- the spine (x 68..81)
m.rect(68, 4, 14, 49, '.')
m.rect(68, 53, 14, 2, '~')
m.hline(68, 13, 14, '-')            # grating bridge on U
m.hline(70, 31, 10, 'Q')            # bridge B (appears with switch B)
m.hline(70, 51, 10, 'R')            # bridge C over the plasma (switch C)
# rungs on alternating walls, 3 rows apart (left x 68..73, right x 76..81)
for row, left in ((28, 1), (25, 0), (22, 1), (19, 0), (16, 1), (48, 0), (45, 1), (42, 0), (39, 1), (33, 1)):
    m.hline(68 if left else 76, row, 6, '-')
m.hline(76, 36, 6, '-')             # the right rung to the alcove
m.put(68, 17, 'h')                  # horizontal lasers across the spine
m.put(68, 35, 'h')
m.put(78, 18, '*')
m.put(74, 23, 'g')
m.put(75, 41, 'g')
m.put(70, 44, '*')
m.put(72, 27, '$$')
m.put(77, 47, '$$')
for y in (8, 24, 46):
    m.put(69, y, 'O')
    m.put(80, y, 'O')
# Secret 3: an alcove in the spine wall off the wide rung.
m.rect(82, 34, 1, 2, 'X')
m.rect(83, 33, 4, 3, '?')
m.put(83, 35, '$H$$')

# ---------------------------------------------------------------- U west (x 2..67): start, laser fences
m.rect(2, 4, 13, 3, '#')            # low ceiling over the start room
m.put(5, 12, 'P')
m.put(9, 7, 'L')
m.rect(15, 4, 1, 5, '#')            # bulkhead, door rows 9..12
m.put(18, 12, '1')                  # sign: laser fences
m.put(24, 4, 'V')
m.put(30, 4, 'w')
m.rect(27, 11, 2, 2, '%')
m.put(27, 10, '*')
m.put(36, 4, 'V')
m.put(21, 5, 'r')
m.put(33, 5, 'r')
m.put(39, 12, '$`$')
m.put(32, 12, '$')
# anteroom (x 42..67) with Secret 1 in its ceiling block
m.rect(51, 4, 8, 5, '#')
m.rect(52, 5, 5, 3, '?')
m.put(52, 7, '$&o$?')
m.rect(51, 6, 1, 2, 'X')
m.hline(47, 8, 4, '%')              # ledge, stand 7
m.rect(44, 10, 2, 3, '%')           # crates, stand 9
m.put(48, 7, '$')
m.put(60, 12, '*')
m.put(57, 12, 'e')
m.put(63, 9, 'L')
m.put(46, 5, 'L')

# ---------------------------------------------------------------- U east (x 82..147)
m.put(85, 12, '2')                  # sign: switches
m.put(87, 7, 'a')                   # switch A (west), shoot it from below
m.rect(90, 4, 1, 9, 'A')            # bulkhead A
m.put(93, 7, 'a')                   # switch A (east)
m.put(88, 5, 'L')
m.rect(98, 10, 4, 3, '%')           # control desks, stand 9
m.hline(104, 9, 6, '-')             # stand 8
m.put(106, 8, '*')
m.put(99, 9, '$$')
m.rect(114, 4, 1, 4, '#')           # hanging bulkhead
m.put(118, 12, 'f')
m.rect(124, 11, 3, 2, '%')
m.put(125, 10, '$')
m.hline(128, 9, 5, '-')
m.put(130, 8, '$')
m.rect(133, 11, 2, 2, '%')
m.hline(135, 9, 4, '-')
m.put(137, 8, '*')
m.put(103, 4, 't')
m.put(122, 6, 'g')
m.put(110, 5, 'L')
m.put(128, 5, 'L')
m.put(138, 5, 'L')
# east shaft U <-> M (x 141..146), zig-zag rungs
m.rect(141, 13, 6, 6, '.')
for i, row in enumerate((16, 19, 22, 25, 28)):
    m.hline(141 if i % 2 == 0 else 144, row, 3, '-')
m.put(146, 30, '+')

# ---------------------------------------------------------------- M east (x 82..147)
m.put(85, 27, 'b')                  # switch B (east), shoot it from below
m.put(87, 30, '3')                  # sign: shoot switches
m.put(100, 19, 't')
m.put(108, 19, 't')
m.put(116, 19, 'V')
m.put(120, 19, 'w')
m.put(118, 20, 'r')
m.rect(124, 28, 4, 3, '%')          # stand 27
m.hline(129, 25, 5, '-')            # stand 24
m.put(131, 24, '*')
m.put(125, 27, '$$')
m.rect(96, 28, 3, 3, '%')           # stand 27
m.hline(99, 25, 5, '-')             # stand 24
m.put(101, 24, '*')
m.put(97, 27, '$')
m.put(104, 30, 'e')
m.put(112, 30, 'f')
m.put(138, 30, 'C')
m.put(92, 24, 'g')
m.put(100, 20, 'L')
m.put(126, 21, 'L')
m.put(140, 21, 'L')

# ---------------------------------------------------------------- M west (x 2..67): pump hall
m.put(64, 27, 'b')                  # switch B (west)
m.put(60, 21, 'L')
m.rect(52, 28, 4, 3, '%')           # pump, stand 27
m.hline(46, 25, 5, '-')             # stand 24
m.rect(38, 28, 4, 3, '%')           # pump, stand 27
m.hline(30, 25, 7, '-')             # stand 24
m.put(48, 24, '*')
m.put(33, 24, '*$$')
m.put(53, 27, '$')
m.put(43, 30, 'n')
m.put(58, 30, 'e')
m.put(36, 21, 'g')
m.put(26, 21, 'g')
m.put(44, 21, 'L')
m.put(28, 21, 'L')
m.put(12, 21, 'L')
m.rect(9, 28, 3, 3, '%')
m.put(10, 27, '$')
m.hline(14, 25, 5, '-')             # stand 24
m.put(16, 24, '*')
# Secret 2: a pump bypass behind a fake wall at the hall's west end.
m.rect(2, 19, 4, 12, '#')
m.rect(5, 29, 1, 2, 'X')
m.rect(2, 27, 3, 4, '?')
m.put(2, 30, '$i$')
# west shaft M <-> L (x 20..25)
m.rect(20, 31, 6, 7, '.')
for i, row in enumerate((33, 36, 39, 42, 45, 48)):
    m.hline(20 if i % 2 == 0 else 23, row, 3, '-')
m.put(14, 30, '$$')

# ---------------------------------------------------------------- L west (x 2..67): the gold door
m.rect(2, L0, 13, 6, '#')           # vault ceiling (rows 38..43)
m.vline(15, 48, 3, 'D')
m.rect(15, L0, 1, 10, '#')
m.put(7, 50, 'E')
m.put(11, 50, '*')
m.put(3, 50, '$$')
m.put(10, 45, 'L')
m.put(18, 50, '4')                  # sign: gold door
m.put(64, 47, 'c')                  # switch C (west)  -- see legend: 'c' is reused? no
m.rect(34, 48, 3, 3, '%')
m.put(35, 47, '*')
m.hline(40, 45, 6, '-')
m.put(42, 44, '$$$')
m.rect(50, 48, 3, 3, '%')           # stand 47
m.put(51, 47, '*')
m.put(40, 50, 'n')
m.put(29, 50, 'C')
m.put(57, 50, 'n')
m.put(46, 50, '+')
m.put(28, 40, 'L')
m.put(44, 40, 'L')
m.put(60, 40, 'L')

# ---------------------------------------------------------------- L east (x 82..147): gauntlet and the key vault
m.put(85, 47, 'c')                  # switch C (east)
m.put(90, 40, 'L')
m.put(96, 38, 'V')
m.put(100, 38, 'w')
m.put(104, 38, 'V')
m.put(100, 39, 'r')
m.rect(108, 48, 3, 3, '%')
m.put(109, 47, '$')
m.hline(110, 45, 5, '-')
m.put(112, 44, '*')
m.put(92, 50, 'n')
m.put(126, 50, 'e')
m.put(88, 44, 'g')
m.put(113, 50, 'e')
m.put(117, 45, 'j')                 # switch D (outside), shoot it from below
m.put(115, 40, 'L')
m.rect(120, L0, 1, 13, 'G')         # the vault wall
m.put(123, 45, 'j')                 # switch D (inside)
m.put(126, 38, 't')
m.put(136, 38, 't')
m.rect(139, 50, 3, 1, '%')          # pedestal
m.set(139, 50, '%')
m.put(140, 49, 'K')
m.put(144, 50, '*')
m.put(130, 50, '$$')
m.put(134, 50, '$$')
m.put(131, 41, 'L')
m.put(143, 41, 'Y')
m.put(98, 50, '$')
m.put(102, 50, '$')
m.put(100, 50, '*')
m.put(122, 30, '*')

# room structure: ducts, hanging bulkheads and lower ceilings break up the long decks
m.rect(95, 4, 19, 2, '%')           # a duct along the U east ceiling
m.rect(119, 4, 1, 4, '#')
m.put(103, 6, 't')                  # ceiling turret under the duct
m.rect(24, 19, 1, 4, '#')           # M west bulkheads
m.rect(60, 19, 1, 3, '#')
m.rect(2, 19, 22, 2, '#')
m.rect(106, 19, 1, 5, '#')          # M east bulkheads
m.rect(137, 19, 1, 4, '#')
m.rect(28, 38, 12, 3, '#')          # L west lower ceiling
m.rect(92, 38, 1, 5, '#')           # L east bulkhead
m.rect(142, 38, 6, 3, '#')
# health, ammo and enemies topped up after the first review
m.place(62, 12, '+')
m.place(88, 12, '&')
m.place(60, 50, '+')
m.place(111, 50, '&')
m.border()

header = [
    ('name', 'Reactor Spine'),
    ('name.de', 'Reaktorrückgrat'),
    ('theme', 'station'),
    ('tint', '3'),
    ('bg', 'station_a'),
    ('music', 'e1_station'),
    ('dark', '0.45'),
    ('par', '360'),
]
legend = {
    'e': 'enemy sentry',
    'f': 'enemy sentry left',
    'g': 'enemy hoverdrone',
    'n': 'enemy sweeper',
    't': 'enemy turret',
    'i': 'treasure idol',
    'o': 'power overdrive',
    'a': 'switch A',
    'A': 'toggle A solid',
    'b': 'switch B',
    'Q': 'toggle B empty',
    'c': 'switch C',
    'R': 'toggle C empty',
    'j': 'switch D',
    'G': 'toggle D solid',
    'V': 'laser v 1.5 1.5',
    'w': 'laser v 1.0 2.0',
    'h': 'laser h 1.2 1.8',
    'L': 'light cyan 6',
    'O': 'light orange 5',
    'Y': 'light yellow 5',
    'r': 'light red 4',
    '1': 'sign sign.e1l5.laser',
    '2': 'sign sign.e1l5.switch',
    '3': 'sign sign.e1l5.shoot',
    '4': 'sign sign.e1l5.golddoor',
}

if __name__ == '__main__':
    lvl.write('e1l5', header, legend, m)
    lvl.check('e1l5')
