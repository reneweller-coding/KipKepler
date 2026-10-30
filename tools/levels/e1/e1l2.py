"""e1l2 Maintenance Deck -- one-way catwalks, crumble blocks, the blue key and door, sentries.

Route (a loop): start at the foot of the catwalk hall, right beside the locked blue door (the exit vault is behind
it) -> climb the one-way catwalks -> pipe gallery east (sentries, a breakable wall secret) -> drop into the settling
tank: checkpoint, a harmless crumble ledge, then the long crumble bridge over coolant -> pump room: up to a crystal
and a fake-wall alcove, down through the floor hole to the blue key -> checkpoint -> the bilge west (crumble over
spikes, pump channels) -> climb back into the catwalk hall through its floor hatch -> the blue door -> exit.
"""
import lvl

m = lvl.Map(132, 46)

# ---------------------------------------------------------------- catwalk hall (x 16..33, rows 2..30)
m.rect(16, 2, 18, 29, '.')
m.put(19, 30, 'P')
m.put(17, 30, '2')                  # sign: blue door
m.put(23, 30, '1')                  # sign: one-way platforms
cat = [(28, 20, 27), (25, 16, 22), (22, 21, 28), (19, 26, 33), (16, 19, 27), (13, 16, 21), (10, 21, 33)]
for row, x0, x1 in cat:
    m.hline(x0, row, x1 - x0 + 1, '-')
m.hline(17, 6, 5, '-')              # a high catwalk with a crystal, stand row 5
m.put(19, 5, '*')
m.put(16, 24, '*$')
m.put(33, 18, '*')
m.put(22, 27, '$`$`$')
m.put(23, 21, '$$')
m.put(21, 15, '$`$')
m.put(27, 9, '$$$')
m.put(29, 18, 'e')                  # sentry patrolling catwalk 18
m.put(29, 5, 'b')                   # hoverdrone at the top of the hall
# floor hatch (x 30..33) down to the bilge, with one-way rungs below
m.rect(30, 31, 4, 3, '.')
m.hline(30, 32, 4, '-')
# Exit vault behind the blue door (x 2..14, rows 24..30).
m.rect(2, 24, 13, 7, '.')
m.vline(15, 28, 3, 'd')
m.put(5, 30, 'E')
m.rect(11, 28, 3, 3, '%')
m.put(12, 27, '*')
m.put(9, 30, '*')
m.put(2, 30, '$')
# Secret 1: the old lift cabin behind a fake wall off catwalk 13.
m.vline(15, 11, 2, 'X')
m.rect(9, 10, 6, 3, '?')
m.put(9, 12, '?$i?o?')

# ---------------------------------------------------------------- filter room (x 37..59, rows 17..27)
# Off catwalk 19 through a short duct; its floor hole drops into the bilge.
m.rect(34, 16, 3, 3, '.')
m.rect(37, 17, 23, 11, '.')
m.hline(37, 22, 5, '-')             # stand 21, back up to the duct
m.rect(40, 25, 3, 3, '%')           # filter tank, stand 24
m.rect(47, 23, 3, 5, '%')           # filter tank, stand 22
m.hline(51, 21, 5, '-')             # stand 20
m.rect(53, 26, 2, 2, '%')
m.rect(56, 28, 3, 6, '.')           # floor hole into the bilge
m.put(48, 22, '*')
m.put(52, 20, '$$$')
m.put(44, 27, '$`$')
m.put(38, 21, '$')
m.put(51, 27, 'f')
m.put(45, 19, 'b')

# ---------------------------------------------------------------- pipe gallery (x 34..69, rows 2..9)
m.rect(34, 2, 36, 8, '.')
for x0, x1 in ((36, 44), (48, 60), (63, 69)):
    m.hline(x0, 2, x1 - x0 + 1, '%')    # pipes along the ceiling
m.put(41, 9, '%%')
m.rect(55, 8, 3, 2, '%')
m.hline(45, 6, 7, '-')
m.hline(59, 6, 5, '-')
m.put(48, 5, '*')
m.put(61, 5, '*')
m.put(46, 5, '$`$')
m.put(52, 9, '$$')
m.put(37, 9, '$')
m.put(50, 9, 'e')
m.put(62, 9, 'f')
m.put(56, 4, 'b')
m.put(44, 9, 'a')
m.rect(65, 10, 3, 2, '.')           # hole down into the settling tank
# Secret 2: a store behind breakable blocks at the gallery's end.
m.vline(70, 8, 2, 'B')
m.rect(71, 6, 6, 4, '?')
m.put(71, 9, '?$&$+?')
m.put(72, 8, '`$')

# ---------------------------------------------------------------- settling tank (x 62..96, rows 12..27)
m.rect(62, 12, 35, 6, '.')
m.put(63, 17, 'C')
m.put(66, 17, '3')                  # sign: crumble blocks
m.hline(68, 14, 3, '_')             # harmless crumble ledge over the landing, stand row 13
m.put(69, 13, '*')
m.rect(72, 18, 21, 8, '.')          # the pit under the bridge
m.hline(72, 26, 21, '~')
m.hline(72, 27, 21, '#')
m.hline(72, 18, 21, '_')
m.put(79, 18, '--')                 # rest pads that do not crumble
m.put(86, 18, '--')
m.put(75, 15, '$`$')
m.put(82, 14, '*')
m.put(89, 15, '$`$')
m.put(95, 17, '$')

# ---------------------------------------------------------------- pump room (x 98..125, rows 9..43)
m.rect(98, 9, 28, 16, '.')          # upper hall rows 9..24
m.rect(97, 15, 1, 3, '.')           # entry from the tank
m.hline(98, 18, 5, '#')             # entry ledge, stand row 17
m.hline(105, 15, 5, '-')            # P1, stand 14
m.hline(112, 12, 5, '-')            # P2, stand 11
m.hline(120, 12, 6, '-')            # P3, stand 11
m.put(114, 11, '*')
m.put(106, 14, '$`$')
m.put(121, 11, '$$')
m.rect(106, 20, 4, 5, '%')          # pump, stand 19
m.rect(112, 22, 4, 3, '%')          # pump, stand 21
m.put(107, 19, '$$')
m.rect(102, 22, 2, 3, '%')          # crates up from the floor, stand 21
m.put(100, 24, 'e')
m.put(117, 16, 'b')
# Secret 3: alcove behind a fake wall at the end of P3.
m.vline(126, 10, 2, 'X')
m.rect(127, 9, 4, 3, '?')
m.put(127, 11, '$H$?')
# lower hall rows 27..43, floor hole x 116..123 with zig-zag rungs
m.rect(98, 27, 28, 17, '.')
m.rect(116, 25, 8, 2, '.')
for i, row in enumerate((26, 29, 32, 35, 38, 41)):
    m.hline(120 if i % 2 == 0 else 116, row, 4, '-')
m.put(122, 31, '*')
m.rect(100, 42, 3, 2, '%')          # key plinth, stand 41
m.put(101, 41, 'k')
m.rect(107, 36, 4, 8, '%')          # pump tower, stand 35
m.hline(111, 41, 3, '-')
m.hline(111, 38, 3, '-')
m.put(108, 35, '*$')
m.put(104, 43, 'e')
m.put(104, 31, 'b')
m.put(124, 43, '$')
m.put(113, 43, '$$')

# ---------------------------------------------------------------- bilge (x 16..96, rows 34..43)
m.rect(16, 34, 81, 10, '.')
m.rect(97, 34, 1, 10, '.')          # opening into the pump room's lower hall
m.put(94, 43, 'C')
m.hline(87, 44, 3, '~')             # a coolant gap in the floor
m.put(88, 41, '$')
m.rect(78, 41, 7, 3, '%')           # raised walkway, stand 40
m.put(81, 40, 'f')
m.rect(62, 41, 4, 3, '%')           # west ledge, stand 40
m.hline(66, 41, 12, '_')            # crumble bridge over spikes
m.put(71, 41, '--')
m.hline(66, 43, 12, '^')
m.put(68, 38, '$`$`$`$')
m.put(75, 37, '*')
# pump channels (x 36..61)
m.rect(52, 41, 3, 3, '%')           # a pump block, stand 40
m.hline(42, 38, 8, '-')             # catwalk, stand 37
m.hline(56, 38, 5, '-')             # catwalk, stand 37
m.put(45, 37, '*')
m.put(57, 37, '$$')
m.put(53, 40, '$')
m.put(58, 43, 'a')
m.put(40, 43, 'c')
m.put(47, 37, 'e')
m.put(50, 35, 'b')
m.put(38, 43, '+')
# west end under the hall: one-way rungs up through the hatch
for row in (35, 38, 41):
    m.hline(30, row, 4, '-')
m.put(19, 43, '*')
m.put(21, 43, '$$$')
m.rect(24, 41, 3, 3, '%')
m.put(25, 40, '$')
m.put(27, 43, 'a')

# health, ammo and enemies topped up after the first review
m.place(28, 30, '+')
m.place(98, 24, '+')
m.place(84, 14, 'b')
m.place(38, 9, 'a')
m.place(118, 43, 'f')
m.border()

header = [
    ('name', 'Maintenance Deck'),
    ('name.de', 'Wartungsdeck'),
    ('theme', 'station'),
    ('tint', '1'),
    ('bg', 'station_a'),
    ('music', 'e1_station'),
    ('dark', '0.2'),
    ('par', '270'),
]
legend = {
    'a': 'enemy sweeper',
    'c': 'enemy sweeper left',
    'b': 'enemy hoverdrone',
    'e': 'enemy sentry',
    'f': 'enemy sentry left',
    'i': 'treasure idol',
    'o': 'power overdrive',
    '1': 'sign sign.e1l2.oneway',
    '2': 'sign sign.e1l2.door',
    '3': 'sign sign.e1l2.crumble',
}

if __name__ == '__main__':
    lvl.write('e1l2', header, legend, m)
    lvl.check('e1l2')
