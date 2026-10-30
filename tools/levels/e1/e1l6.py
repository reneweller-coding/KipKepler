"""e1l6 Cargo Conveyors -- conveyor belts, crusher presses, rammers, the SCATTER gun.

Three decks and a tall sorting hall in the east. Route (a loop): loading dock (start) with the SCATTER in the
office -> pallet room: a close-quarters swarm (what the scatter is for) -> belt line (a belt that carries you, one
that fights you, a rammer on it) -> press line: a belt under crusher presses -> sorting hall: belts on both walls
and two paternoster lifts between them -> upper deck west (belts, presses, sentries) -> manifest office (secret)
-> the chute down (one-way rungs, climbable) -> lower deck east (shredder line, rammers) -> back into the hall ->
freight bay with the exit.
"""
import lvl

W, H = 160, 56
m = lvl.Map(W, H)
z, y = 'z', 'y'                     # conveyor right / left


def belt(x0, x1, row, ch):
    m.hline(x0, row, x1 - x0 + 1, ch)


# ---------------------------------------------------------------- middle deck: dock, pallet room, belts, presses
m.rect(7, 24, 14, 9, '.')           # loading dock
m.rect(7, 25, 2, 5, ' ')            # the open cargo door: space outside
m.put(12, 32, 'P')
m.rect(15, 32, 3, 1, '%')           # office desk
m.put(16, 31, 'S')
m.put(14, 32, '1')                  # sign: scatter
m.put(19, 32, '$')
m.put(12, 26, 'L')
m.rect(9, 30, 2, 3, '%')            # stacked crates by the door
m.put(9, 29, '$')
m.rect(21, 22, 16, 11, '.')         # pallet room
m.rect(21, 22, 1, 5, '#')
m.rect(25, 31, 2, 2, '%')
m.put(25, 30, '*')
m.rect(30, 32, 3, 1, '%')
m.rect(34, 30, 2, 3, '%')
m.put(34, 29, '$$')
m.put(28, 32, 'a')
m.put(31, 31, 'a')
m.put(33, 32, 'c')
m.put(29, 25, 'g')
m.put(33, 24, 'g')
m.put(27, 27, 'L')
m.rect(37, 22, 34, 11, '.')         # belt line
m.put(38, 32, '2')                  # sign: conveyors
belt(40, 55, 33, z)
belt(58, 69, 33, y)
m.rect(56, 33, 2, 1, '#')
m.hline(44, 29, 5, '-')
m.put(46, 28, '$$$')
m.rect(50, 31, 2, 2, '%')           # a crate riding the belt
m.rect(57, 30, 2, 3, '%')
m.hline(59, 28, 6, '-')
m.put(61, 27, '*')
m.put(68, 32, '*')
m.put(65, 32, 'R')                  # rammer on the reverse belt
m.put(52, 25, 'g')
m.put(45, 24, 'L')
m.put(62, 24, 'L')
m.rect(71, 28, 30, 5, '.')          # press line: a low corridor
belt(71, 100, 33, z)
m.put(72, 32, '3')                  # sign: presses
for x, ch in ((77, 'Y'), (84, 'W'), (91, 'Y'), (97, 'W')):
    m.put(x, 28, ch)
m.rect(80, 26, 3, 2, '.')           # tall pockets between the presses
m.rect(87, 26, 3, 2, '.')
m.put(81, 32, '*')
m.put(88, 32, '*')
m.put(94, 32, '$')
m.put(74, 29, 'O')
m.put(88, 27, 'O')

# ---------------------------------------------------------------- sorting hall (x 101..140, rows 4..50)
m.rect(101, 4, 40, 47, '.')
m.hline(101, 33, 4, '#')
belt(105, 116, 33, z)               # west, the middle deck's belt continues (stand 32)
m.put(102, 32, 'C')
belt(104, 116, 45, z)               # west, stand 44
belt(104, 116, 25, z)               # west, stand 24
m.hline(101, 17, 3, '#')            # upper deck sill, stand 16
m.hline(104, 17, 13, '-')           # catwalk from the sill to the lift
belt(127, 140, 39, y)               # east, stand 38
belt(127, 140, 27, y)               # east, stand 26
belt(127, 140, 11, y)               # east, stand 10
belt(108, 132, 51, y)               # the hall floor
m.put(117, 50, 'JJJJ')              # lift up (bottom -> top)
m.put(121, 11, 'NNNN')              # lift down (top -> bottom)
m.put(106, 44, '*')
m.put(138, 38, '*')
m.put(106, 24, '*')
m.put(130, 26, '*')
m.put(137, 10, '*')
m.put(110, 32, '$$')
m.put(133, 38, '$$')
m.put(110, 24, '$$')
m.put(126, 50, '$`$`$')
m.put(112, 44, 'R')
m.put(135, 26, 'R')
m.put(139, 15, 'e')
m.rect(138, 16, 3, 1, '%')          # turret perch, stand 15
m.put(128, 4, 't')
m.put(110, 8, 'g')
m.put(132, 31, 'g')
for (lx, ly) in ((104, 6), (136, 6), (104, 30), (136, 30), (110, 47), (134, 47)):
    m.put(lx, ly, 'L')
# Secret 4: a maintenance cupboard off the top belt.
m.rect(141, 9, 1, 2, 'X')
m.rect(142, 8, 4, 3, '?')
m.put(142, 10, '$i$')

# freight bay with the exit (x 141..157, rows 38..50)
m.rect(141, 46, 1, 5, '.')
m.rect(142, 38, 12, 13, '.')
m.put(149, 50, 'E')
m.put(152, 50, '*')
# Secret 3: a closet behind the freight bay's east wall.
m.rect(154, 49, 1, 2, 'X')
m.rect(155, 47, 4, 4, '?')
m.put(155, 50, '$H$&')
m.put(145, 50, '$$')
m.rect(147, 48, 2, 3, '%')
m.put(147, 47, '$')
m.put(150, 42, 'L')

# ---------------------------------------------------------------- upper deck (x 2..100, rows 6..16, floor 17)
m.rect(7, 6, 94, 11, '.')
belt(60, 99, 17, y)                 # belts toward the west
belt(22, 52, 17, y)
for x, ch in ((70, 'Q'), (79, 'G'), (34, 'Q')):
    m.put(x, 10, ch)
m.rect(66, 6, 18, 4, '#')           # a low press housing over the belt (crushers hang from it)
m.rect(30, 6, 9, 4, '#')
m.put(75, 16, '*')
m.put(36, 16, '$')
m.rect(88, 14, 3, 3, '%')           # stand 13
m.hline(91, 11, 5, '-')
m.put(93, 10, '*')
m.put(89, 13, '$')
m.put(86, 16, 'f')
m.put(99, 16, 'C')
m.rect(54, 14, 3, 3, '%')           # stand 13
m.hline(46, 11, 6, '-')             # stand 10
m.put(48, 10, '*')
m.put(55, 13, '$')
m.put(58, 16, 'R')
m.put(44, 16, 'e')
m.put(62, 9, 'g')
m.put(25, 9, 'g')
for lx in (14, 28, 44, 58, 86, 98):
    m.put(lx, 7, 'L')
# manifest office (west end) and Secret 2
m.rect(7, 6, 1, 7, '#')
m.rect(10, 14, 4, 3, '%')           # filing cabinets, stand 13
m.put(11, 13, '*')
m.put(17, 16, '$$')
m.rect(16, 12, 1, 5, '#')           # office partition, door at rows 12..16? no: a low wall
m.rect(16, 15, 1, 2, '.')
m.put(20, 16, '$')
m.hline(8, 11, 2, '%')              # ledge to the hidden door, stand 10
m.rect(7, 9, 1, 2, 'X')             # behind the office's west wall
m.rect(1, 7, 6, 4, '?')
m.rect(1, 11, 6, 1, '#')
m.put(1, 10, '?$o$$?')
# the chute (x 2..5) from the upper deck down to the lower deck, rungs alternating
m.rect(2, 12, 4, 26, '.')
m.rect(2, 12, 4, 1, '#')
m.rect(6, 13, 1, 4, '.')
for i, row in enumerate(range(16, 38, 3)):
    m.hline(2 if i % 2 == 0 else 4, row, 2, '-')

# ---------------------------------------------------------------- lower deck (x 2..100, rows 38..50, floor 51)
m.rect(2, 38, 99, 13, '.')
m.put(8, 50, 'C')
m.put(14, 47, 'L')
belt(14, 40, 51, z)                 # the shredder line runs east
m.rect(24, 38, 20, 5, '#')          # shredder housing, crushers below it
for x, ch in ((27, 'U'), (33, 'V'), (39, 'U')):
    m.put(x, 43, ch)
m.put(30, 50, '*')
m.put(20, 50, '*')
m.put(36, 50, '$')
m.rect(46, 48, 4, 3, '%')           # a crate stack, stand 47
m.hline(50, 45, 6, '-')             # stand 44
m.put(52, 44, '*')
m.put(47, 47, '$$')
m.put(58, 50, 'R')
m.put(70, 50, 'c')
belt(62, 92, 51, y)                 # a long belt against you
m.rect(66, 48, 3, 3, '%')           # stand 47
m.rect(72, 48, 2, 3, '%')           # stand 47
m.rect(75, 45, 4, 1, '%')           # stand 44
m.put(77, 44, '*')
m.rect(84, 48, 3, 3, '%')           # stand 47
m.hline(87, 45, 5, '-')             # stand 44
m.put(89, 44, '*')
m.put(85, 47, '$')
m.put(94, 50, 'f')
m.put(80, 42, 'g')
m.put(55, 40, 'e')
m.hline(53, 41, 4, '%')             # sentry perch, stand 40
m.put(98, 50, '+')
for lx in (30, 48, 64, 80, 96):
    m.put(lx, 39, 'L')

# health, ammo and enemies topped up after the first review
m.place(41, 32, '+')
m.place(64, 16, '&')
m.place(129, 38, '+')
m.place(12, 50, '&')
m.border()

header = [
    ('name', 'Cargo Conveyors'),
    ('name.de', 'Frachtbänder'),
    ('theme', 'station'),
    ('tint', '1'),
    ('bg', 'station_b'),
    ('music', 'e1_station'),
    ('dark', '0.3'),
    ('par', '420'),
]
legend = {
    'a': 'enemy sweeper',
    'c': 'enemy sweeper left',
    'g': 'enemy hoverdrone ambush',
    'e': 'enemy sentry',
    'f': 'enemy sentry left',
    'R': 'enemy rammer left',
    't': 'enemy turret',
    'S': 'weapon scatter',
    'o': 'power overdrive',
    'i': 'treasure idol',
    'z': 'conveyor 1',
    'y': 'conveyor -1',
    'Y': 'crusher 4 3.0',
    'W': 'crusher 4 2.4',
    'U': 'crusher 7 3.2',
    'Q': 'crusher 6 3.0',
    'G': 'crusher 6 2.4',
    'J': 'mover 0 -39 110 1.2',
    'N': 'mover 0 39 110 1.2',
    'V': 'crusher 7 2.6',
    'L': 'light warm 6',
    'O': 'light orange 4',
    '1': 'sign sign.e1l6.scatter',
    '2': 'sign sign.e1l6.conveyor',
    '3': 'sign sign.e1l6.crusher',
}

if __name__ == '__main__':
    lvl.write('e1l6', header, legend, m)
    lvl.check('e1l6')
