"""e1l1 Cadet Quarters -- the tutorial.

Route (a loop): bunk room (start, middle left) -> training corridor (run, jump, first crystal, a soft pit) ->
mess hall (shoot, sweepers, counter ledges) -> stairwell down -> checkpoint -> lower deck: west cellar (spikes,
second secret) and east warehouse (charged shot) -> the shaft climb (right) -> observation lounge with its window
band (hoverdrones, aim up) -> gym (jump training, the easy fake-wall secret) -> exit room (upper left).
A drop shaft in the exit room leads back to the bunk room for players who missed a crystal.
"""
import lvl

m = lvl.Map(110, 40)

# ---------------------------------------------------------------- upper deck
# Exit room (x 2..12, rows 7..12), doorway to the gym through x 13.
m.rect(2, 7, 11, 6, '.')
m.rect(13, 9, 1, 4, '.')
m.set(7, 12, 'E')
m.set(11, 12, '9')                  # sign: exit
m.rect(2, 13, 2, 6, '.')            # drop shaft back to the bunk room
m.put(2, 12, '$`')
# Secret vault 1 above the exit room, behind a fake wall from the gym's top ledge.
m.rect(2, 2, 10, 3, '?')
m.put(12, 3, 'XX')
m.put(12, 4, 'XX')
m.put(2, 4, '?i?$?$?H$?')

# Gym (x 14..39, rows 2..12): climbing blocks to the top-left ledge.
m.rect(14, 2, 26, 11, '.')
m.rect(33, 11, 4, 2, '%')           # block A, stand row 10
m.rect(27, 9, 4, 1, '%')            # slab B, stand row 8
m.rect(21, 6, 4, 1, '%')            # slab C, stand row 5
m.rect(14, 5, 4, 1, '#')            # top ledge, stand row 4 (fake wall to its left)
m.put(29, 7, '*')
m.put(22, 4, '*')
m.put(14, 4, '$$`8')                # trail into the wall + sign: secret
m.put(34, 10, '$$')
m.put(28, 7, '$')
m.put(24, 12, 'a')                  # a training sweeper on the gym floor
m.put(18, 9, 'b')                   # hoverdrone over the gym floor
m.put(19, 12, '$`$')

# Bulkhead between gym and lounge (x 40), doorway rows 9..12.
# Observation lounge (x 41..108, rows 2..12) with a window band to space (rows 2..6).
m.rect(41, 2, 68, 11, '.')
m.rect(41, 2, 68, 5, ' ')
for px in (49, 77, 101):
    m.rect(px, 1, 1, 6, '#')        # window frames hanging from the ceiling
m.rect(40, 9, 1, 4, '.')
for bx in (45, 60, 73, 86):
    m.put(bx, 12, '%%')             # benches
m.rect(55, 9, 4, 1, '%')            # slab 1, stand row 8
m.rect(61, 7, 4, 1, '%')            # slab 2, stand row 6
m.rect(69, 9, 4, 1, '%')            # slab 3, stand row 8
m.put(63, 5, '*')
m.put(56, 7, '$$')
m.put(70, 7, '$$$')
m.put(82, 7, '*')
m.rect(81, 9, 4, 1, '%')            # slab 4 beside the east bench, stand row 8
m.put(66, 12, '+')
m.put(49, 11, '$')
m.put(78, 11, '$')
m.put(95, 12, '7')                  # sign: aim up
m.put(58, 5, 'b')
m.put(75, 4, 'b')
m.put(48, 5, 'b')

# ---------------------------------------------------------------- the shaft (x 98..108, rows 13..37)
m.rect(98, 13, 11, 25, '.')
# zig-zag ledges, 2 rows apart: left x 98..101, right x 105..108
for i, sy in enumerate(range(35, 14, -2)):
    left = i % 2 == 0
    m.rect(98 if left else 105, sy + 1, 4, 1, '%' if i % 3 else '#')
# Locker room off the shaft (x 79..96, rows 17..23), a door from the left ledge at stand row 23.
m.rect(79, 17, 18, 7, '.')
m.rect(97, 21, 1, 3, '.')
m.rect(84, 22, 2, 2, '%')
m.rect(90, 21, 2, 3, '%')
m.rect(80, 20, 3, 1, '%')           # a shelf, stand row 19
m.put(81, 19, '*')
m.put(80, 23, '$$$')
m.put(90, 20, '$$')
m.put(87, 23, 'c')
m.put(94, 23, '+')
m.put(107, 17, '*')                 # on a right ledge
m.put(106, 29, '$')
m.put(100, 23, '$')
m.put(103, 24, 'b')                 # a drone halfway up

# ---------------------------------------------------------------- middle deck
# Bunk room (start), x 2..13, rows 19..24.
m.rect(2, 19, 12, 6, '.')
m.put(5, 24, 'P')
m.put(8, 24, '1')                   # sign: run
m.put(10, 22, '%%%')                # a bunk frame with a gem on it
m.put(11, 21, '$')

# Training corridor, x 14..37, rows 17..24.
m.rect(14, 17, 24, 8, '.')
m.put(17, 24, '2')                  # sign: jump
m.rect(20, 24, 3, 1, '#')           # step 1, stand row 23
m.rect(23, 22, 8, 3, '#')           # step 2, stand row 21
m.put(25, 21, '3')                  # sign: crystals
m.put(28, 20, '*')
m.rect(35, 22, 3, 3, '#')           # far side of the soft pit (x 31..34)
m.put(33, 24, '%')                  # a crate to climb out of the pit
m.put(31, 24, '$$')
m.put(32, 18, '$$')                 # an arc of treasure over the pit
m.put(21, 23, '$')

# Mess hall, x 38..66, rows 15..24.
m.rect(38, 15, 29, 10, '.')
m.put(38, 23, '%%')                 # crate step down from the corridor
m.put(38, 24, '%%')
m.put(42, 24, '4')                  # sign: shoot
m.put(46, 24, '%%%')                # a table
m.rect(50, 22, 4, 1, '%')           # counter ledge L1, stand row 21
m.rect(56, 19, 5, 1, '#')           # ledge L2, stand row 18
m.rect(63, 17, 4, 1, '#')           # ledge L3, stand row 16
m.put(59, 18, '*')
m.put(65, 16, '*')
m.put(51, 21, '$$')
m.put(47, 23, '$')
m.put(57, 24, 'a')
m.put(63, 24, 'c')

# Stairwell, x 67..76, rows 15..37: slabs down to the lower deck.
m.rect(67, 15, 10, 12, '.')
m.rect(69, 27, 4, 1, '%')           # stand 26
m.rect(73, 30, 4, 1, '%')           # stand 29
m.rect(69, 33, 4, 1, '%')           # stand 32
m.rect(74, 36, 3, 2, '%')           # a crate on the floor, stand 35
m.put(70, 26, '$')
m.put(74, 29, '$')

# ---------------------------------------------------------------- lower deck (rows 27..37)
m.rect(37, 27, 61, 11, '.')
m.rect(37, 27, 18, 2, '#')          # a lower ceiling over the west cellar
m.rect(55, 27, 2, 1, '#')
m.put(79, 37, 'C')
m.put(77, 37, '5')                  # sign: checkpoint

# West cellar (x 37..66): crates, spikes, a crystal stack, the second secret.
m.put(52, 37, '^^^')
m.put(57, 37, '6')                  # sign: spikes
m.rect(44, 35, 3, 3, '%')           # a crate stack, stand row 34
m.rect(48, 36, 2, 2, '%')           # a step to it, stand row 35
m.put(45, 34, '*')
m.put(39, 37, '*')
m.put(53, 34, '$$$')                # treasure over the spikes
m.rect(61, 35, 2, 3, '%')           # crates, stand 34
m.put(61, 34, '$$')
m.put(41, 37, 'a')
m.put(59, 37, '+')
m.put(36, 36, 'X')
m.put(36, 37, 'X')
m.rect(30, 35, 6, 3, '?')
m.put(30, 37, '?+$?j?')

# East warehouse (x 77..97): crate stacks, the charged-shot sign, two sweepers in a row.
m.put(81, 37, '0')                  # sign: charged shot
m.put(83, 37, '%')                  # a low crate keeps the sweepers away from the checkpoint
m.rect(91, 36, 2, 2, '%')           # crates, stand 35
m.rect(94, 33, 3, 1, '%')           # a crate shelf, stand 32
m.put(95, 32, '*')
m.put(91, 35, '$$')
m.put(87, 37, 'c')
m.put(89, 37, 'c')
m.put(86, 34, '$')
m.put(96, 37, '+')
m.put(106, 37, '$')

m.border()

header = [
    ('name', 'Cadet Quarters'),
    ('name.de', 'Kadettenquartiere'),
    ('theme', 'station'),
    ('tint', '0'),
    ('bg', 'station_a'),
    ('music', 'e1_station'),
    ('dark', '0.15'),
    ('par', '210'),
]
legend = {
    'a': 'enemy sweeper',
    'c': 'enemy sweeper left',
    'b': 'enemy hoverdrone',
    'i': 'treasure idol',
    'j': 'treasure chip',
    '1': 'sign sign.e1l1.run',
    '2': 'sign sign.e1l1.jump',
    '3': 'sign sign.e1l1.crystal',
    '4': 'sign sign.e1l1.shoot',
    '5': 'sign sign.e1l1.checkpoint',
    '6': 'sign sign.e1l1.spikes',
    '0': 'sign sign.e1l1.charge',
    '7': 'sign sign.e1l1.aimup',
    '8': 'sign sign.e1l1.secret',
    '9': 'sign sign.e1l1.exit',
}

if __name__ == '__main__':
    lvl.write('e1l1', header, legend, m)
    lvl.check('e1l1')
