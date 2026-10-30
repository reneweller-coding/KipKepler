"""e3s The Mirror Palace / Der Spiegelpalast -- the secret level of Episode 3 (ice, crumbling floors over brine).

An ice palace the comet's old miners carved for a queen who never came. Its floors are crumbling ice (`_`) over a
lake of freezing brine: keep moving, every slab drops half a second after Kip stands on it (and grows back after
four). The palace is a mirror: the east wing repeats the west wing tile for tile -- except where the mirror is
flawed (the start, the thrones, the secrets).

  the gate hall (start, sign) in the middle, on the only pier
  -> floor 1 outwards: crumble bridges between ice pillars, gaps over the brine (both wings)
  -> the outer stair towers -> floor 2 inwards: the mirror halls (slippery ice, crystal blocks)
  -> the central stair -> floor 3 outwards -> the outer towers -> floor 4 inwards: the crystal galleries
  -> the throne room (the exit between two thrones: the crown on the west one, the logbook page on the east one)
  the queen's lift (a teleporter pair) links the gate hall and the throne room, so the second wing is climbed
  from the gate as well instead of walked back down.
  secret 1: the west attic above floor 4; secret 2: the cellar under the east tower.
"""
from lvl import Lv, main

W, H = 151, 56
AX = 75                 # the mirror axis (column)
F1, F2, F3, F4 = 46, 37, 28, 19   # floor rows (the hero stands one row above)


def build():
    L = Lv(W, H)
    L.legend.update({
        'a': 'enemy crystalcrab',
        'c': 'enemy crystalcrab ceiling',
        'b': 'enemy icebat',
        'h': 'enemy shardling',
        'o': 'enemy wisp',
        'O': 'enemy wisp elite=regenerating',
        'n': 'enemy minerbot',
        'N': 'enemy minerbot left',
        'u': 'enemy cryoturret',
        'G': 'enemy frostgolem elite=armoured',
        'I': 'treasure idol',
        'R': 'treasure crown',
        'p': 'power overdrive',
        'L': 'lore e3s_vault',
        '1': 'sign sign.e3s.crumble',
        '2': 'sign sign.e3s.mirror',
        '3': 'teleport 5',
        '4': 'teleport 6',
        '5': 'arrive',
        '6': 'arrive',
        'l': 'light cyan 6',
        'q': 'light violet 6',
    })

    # ==== the west half (x 0-75); the east half is its mirror ================================================
    L.fill(2, 4, AX - 1, 44, '.')     # the palace interior, rows 4-47
    L.fill(2, 48, AX - 1, 4, '~')     # the brine, rows 48-51
    # windows to the comet sky high up in the halls
    for x0, x1 in ((14, 21), (34, 41), (50, 55)):
        L.rect(x0, 7, x1, 13, ' ')
    for x0, x1 in ((14, 21), (38, 45)):
        L.rect(x0, 30, x1, 33, ' ')

    # --- the gate hall (centre, floor 1): the only pier; its ceiling is floor 2's solid middle
    L.fill(66, F1, AX - 66 + 1, 6, '#')
    L.fill(64, F2, AX - 64 + 1, 1, '#')
    # --- floor 1 (row 46) outwards: crumble bridges, ice pillars, gaps
    L.put(52, F1, '_' * 14)            # x 52-65
    L.fill(48, F1, 4, 6, '#')          # pillar x 48-51
    L.put(48, F1, '%%%%')
    L.put(34, F1, '______..._____')    # x 34-47, gap x 40-42
    L.fill(30, F1, 4, 6, '#')          # pillar x 30-33
    L.put(30, F1, '%%%%')
    L.put(10, F1, '________...________')  # x 10-28, gap x 18-20
    L.set(29, F1, '_')
    L.fill(2, F1, 8, 6, '#')           # the outer tower's foot (x 2-9)
    L.set(41, F1 - 3, '*')             # crystals over the gaps
    L.set(19, F1 - 3, '*')
    L.put(55, F1 - 1, '$ $ $')
    L.put(24, F1 - 1, '$$')
    L.put(4, F1 - 1, '$+')
    L.set(8, F1 - 1, '&')
    # --- the outer tower: floor 1 -> floor 2 (one-way steps every 3 rows)
    L.put(5, 43, '-----')
    L.put(2, 40, '-----')
    L.put(2, F2, '--------')           # x 2-9 (floor 2's end)
    # --- floor 2 (row 37) inwards: the mirror hall
    L.put(10, F2, '%%%%%%')            # x 10-15 slippery ice
    L.put(16, F2, '____________')      # x 16-27
    L.fill(28, 34, 4, 4, '#')          # a crystal block, three above the floor (x 28-31)
    L.put(32, F2, '______________')    # x 32-45
    L.put(46, F2, '%%%%')              # x 46-49
    L.put(50, F2, '______________')    # x 50-63
    L.set(29, 33, '*')
    L.set(30, 33, '$')
    L.set(39, F2 - 3, '*')
    L.put(52, F2 - 1, '$$$')
    L.put(11, F2 - 1, '$$')
    # --- the central stair: floor 2 -> floor 3
    L.put(66, 34, '-----')             # x 66-70 (mirrored: 80-84)
    L.put(72, 31, '----')              # x 72-75 (mirrored: 75-78)
    L.put(64, F3, '-' * (AX - 64 + 1))  # floor 3's middle is one-way
    L.set(AX, 30, '*')
    # --- floor 3 (row 28) outwards
    L.put(50, F3, '______________')    # x 50-63
    L.put(36, F3, '______..._____')    # x 36-49, gap x 42-44
    L.fill(30, F3, 6, 2, '%')          # a solid ice balcony (x 30-35)
    L.put(10, F3, '________..._________')  # x 10-29, gap x 18-20
    L.set(43, F3 - 3, '*')
    L.set(19, F3 - 3, '*')
    L.put(31, F3 - 1, '$$$$')
    L.put(56, F3 - 1, '$ $')
    # --- the outer tower: floor 3 -> floor 4
    L.put(2, F3, '--------')
    L.put(5, 25, '-----')
    L.put(2, 22, '-----')
    L.put(2, F4, '--------')
    # --- floor 4 (row 19) inwards: the crystal gallery
    L.put(10, F4, '________________')  # x 10-25
    L.fill(26, F4, 4, 2, '%')          # x 26-29
    L.put(30, F4, '______...________')  # x 30-46, gap x 36-38
    L.fill(47, F4, 3, 2, '%')          # x 47-49
    L.put(50, F4, '____________')      # x 50-61
    L.set(37, F4 - 3, '*')
    L.put(27, F4 - 1, '$$')
    L.put(54, F4 - 1, '$$$')
    L.put(14, F4 - 1, '$ $')
    # --- the throne room (x 62-88, rows 8-18, floor 19)
    L.fill(62, 4, AX - 62 + 1, 4, '#')  # the ceiling above it (rows 4-7)
    L.fill(62, 8, 1, 7, '#')           # the west wall, open below (rows 15-18)
    L.fill(62, F4, AX - 62 + 1, 3, '#')
    L.fill(66, 16, 3, 3, '%')          # the throne (x 66-68, top row 16)
    L.put(70, 18, '$$')
    # --- mid-height ledges of clear ice (side steps with treasure) and icicles under the solid slabs
    for x0, y, w in ((24, 42, 4), (44, 42, 3), (52, 33, 4), (12, 24, 4), (54, 24, 4)):
        L.fill(x0, y, w, 1, '%')
    L.put(25, 41, '$$')
    L.set(45, 41, '*')
    L.put(53, 32, '$$')
    L.put(13, 23, '$$')
    L.set(55, 23, '*')
    L.put(31, 30, 'vvvv')              # under the floor-3 balcony
    L.put(26, 21, 'vvvv')              # under the floor-4 slabs
    L.put(47, 21, 'vvv')
    L.put(46, 38, 'vvvv')              # under the floor-2 slab

    # ==== the mirror =========================================================================================
    L.mirror(0, 0, AX, H, AX)

    # ==== the flaws in the mirror (what is not the same on both sides) =======================================
    L.set(AX, F1 - 1, 'P')
    L.set(71, F1 - 1, '1')
    L.set(79, F1 - 1, '&')
    L.set(85, 18, '2')
    L.set(AX, 18, 'E')
    L.set(67, 15, 'R')                 # the crown on the west throne
    L.set(83, 15, 'L')                 # the logbook page on the east throne
    # the queen's lift: a pad in the gate hall up to the throne room and one back down
    L.set(67, F1 - 1, '3')
    L.set(83, F1 - 1, '6')
    L.set(86, 18, '4')
    L.set(64, 18, '5')
    L.set(64, 15, 'I')
    L.set(86, 15, 'I')
    # secret 1: the west attic above floor 4 (in through the palace masonry)
    L.fill(2, 4, 8, 13, '#')          # the masonry of the west corner (rows 4-16)
    L.fill(2, 12, 6, 4, '?')
    L.col(8, 14, 'XX')
    L.col(9, 14, 'XX')
    L.put(3, 15, '$I$H')
    # secret 2: the cellar under the east tower
    L.put(143, F1, 'XX')
    L.fill(142, 47, 7, 2, '?')
    L.fill(141, 47, 1, 2, '#')
    L.fill(141, 49, 8, 3, '#')
    L.put(145, 48, '$p$')

    # ==== enemies =============================================================================================
    for x, y, c in [
        (24, F1 - 1, 'h'), (126, F1 - 1, 'h'),
        (40, 40, 'b'), (110, 40, 'b'),
        (12, F2 - 1, 'a'), (47, F2 - 1, 'n'), (103, F2 - 1, 'N'), (138, F2 - 1, 'a'),
        (68, 22, 'c'), (82, 22, 'c'),
        (33, F3 - 1, 'n'), (117, F3 - 1, 'N'),
        (44, 24, 'o'), (106, 24, 'o'),
        (28, F4 - 1, 'h'), (122, F4 - 1, 'h'),
        (20, 5, 'b'), (130, 5, 'b'),
        (79, 18, 'G'), (AX, 9, 'O'),
    ]:
        L.set(x, y, c)
    for x, y in ((10, 5), (140, 5)):
        L.set(x, y, 'u')

    # ==== lights =============================================================================================
    for x, y, c in [(6, 44, 'l'), (144, 44, 'l'), (40, 39, 'q'), (110, 39, 'q'), (AX, 39, 'l'), (AX, 32, 'q'),
                    (24, 26, 'l'), (126, 26, 'l'), (40, 17, 'q'), (110, 17, 'q'), (70, 10, 'l'), (80, 10, 'l'),
                    (5, 13, 'q')]:
        L.set(x, y, c)
    return L


META = [
    ('name', 'The Mirror Palace'),
    ('name.de', 'Der Spiegelpalast'),
    ('theme', 'ice'),
    ('tint', '2'),
    ('bg', 'ice_b'),
    ('music', 'e3_crystal'),
    ('dark', '0.35'),
    ('par', '420'),
]

if __name__ == '__main__':
    main(build, 'e3s', META)
