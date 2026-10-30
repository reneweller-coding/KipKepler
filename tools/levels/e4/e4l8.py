"""e4l8 -- Core Approach / Kernzugang (citadel, dark). Everything, riftgates; the hardest level.

  Z1 outer ring (start): a laser fence, the first riftgate (taught), shieldbots, a vault under the floor (secret).
  Z2 conveyor gate: a low tunnel with a belt under hammers, a hall with laser eyes, a riftgate, the blue key.
  Z3 spring shaft: springs and lifts up a tall shaft, jetpackers, a riftgate; a vault behind its west wall
  (secret). The blue door at its foot leads to Z5.
  Z4 switch vault (top of the shaft): gate A (its switch on the lower floor), a teleporter pad into the sealed
  key room (gold key, switch B opens gate B back into the vault).
  Z5 plasma bridge (behind the blue door): movers between pillars over plasma, laser fences across the movers,
  brutes and a riftgate on the pillars.
  Z6 core gate (behind the gold door): the final climb -- springs, a lift, hammer corridors, two riftgates --
  to the exit at the top; a vault under its floor (secret).
"""
from kit import Map, main


def build():
    m = Map(260, 80)
    m.key('name', 'Core Approach')
    m.key('name.de', 'Kernzugang')
    m.key('theme', 'citadel')
    m.key('tint', 3)
    m.key('bg', 'citadel_b')
    m.key('music', 'e4_citadel')
    m.key('dark', 0.4)
    m.key('par', 660)
    T = m.legend('a', 'enemy trooper')
    TL = m.legend('b', 'enemy trooper left')
    TA = m.legend('e', 'enemy trooper ambush')
    G = m.legend('g', 'enemy gloamhound')
    GL = m.legend('h', 'enemy gloamhound left')
    J = m.legend('j', 'enemy jetpacker')
    JA = m.legend('y', 'enemy jetpacker ambush')
    RG = m.legend('R', 'enemy riftgate')
    SB = m.legend('f', 'enemy shieldbot')
    EY = m.legend('z', 'enemy lasereye')
    BL = m.legend('i', 'enemy blinker')
    BLA = m.legend('I', 'enemy blinker ambush')
    BR = m.legend('w', 'enemy brute')
    BRL = m.legend('W', 'enemy brute left')
    S = m.legend('S', 'spring')
    m.legend('q', 'switch A')
    m.legend('s', 'switch B')
    m.legend('A', 'toggle A solid')
    m.legend('G', 'toggle B solid')
    m.legend('1', 'teleport U')
    m.legend('2', 'teleport V')
    m.legend('U', 'teleport')
    m.legend('V', 'teleport')
    Q = m.legend('Q', 'conveyor -1')
    CR1 = m.legend('m', 'crusher 5 2.4')
    CR2 = m.legend('M', 'crusher 4 2.6')
    CR3 = m.legend('N', 'crusher 4 3.1')
    LZ1 = m.legend('6', 'laser v 1.6 1.4')
    LZ2 = m.legend('7', 'laser v 1.2 1.8')
    mv = {}
    for ch, spec in (('3', '4 0 60'), ('4', '7 0 70'), ('5', '7 0 70'), ('8', '5 0 60'),
                     ('9', '0 -14 70 1.0'), ('0', '0 -24 80 1.0'), ('T', '0 -12 70 1.0'), ('Z', '0 -12 70 1.0')):
        mv[ch] = m.legend(ch, 'mover ' + spec)
    m.legend('n', 'sign sign.e4l8.riftgate')
    m.legend('L', 'light magenta 7')
    m.legend('l', 'light blue 6')
    m.legend('o', 'power overdrive')
    m.legend('p', 'power shield')
    m.legend('u', 'treasure crown')
    m.legend('x', 'treasure cube')

    # ================================================================ rooms
    m.room(2, 52, 50, 18)                  # Z1 x2-51, floor 70
    m.room(52, 64, 20, 6)                  # Z2 tunnel x52-71
    m.room(72, 56, 28, 14)                 # Z2 hall x72-99
    m.room(100, 8, 30, 62)                 # Z3 x100-129, floor 70
    m.room(131, 4, 45, 30)                 # Z4 x131-175, floor 34
    m.room(130, 12, 1, 4)                  # Z3 -> Z4 doorway
    m.room(178, 18, 12, 16)                # Z4 key room x178-189, floor 34
    m.room(131, 40, 70, 36)                # Z5 x131-200, plasma 72-75
    m.room(202, 6, 56, 64)                 # Z6 x202-257, floor 70

    # ================================================================ Z1 outer ring (start)
    m.sky(8, 53, 20, 6)
    m.put(5, 69, 'P')
    m.box(12, 67, 6, 3, '%')
    m.put(14, 66, '*')
    m.put(22, 52, LZ1)                     # a laser fence from the ceiling to the floor
    m.put(27, 69, 'n')
    m.put(40, 69, RG)
    m.put(33, 69, SB)
    m.hl(25, 67, 5, '-')
    m.hl(31, 64, 4, '-')
    m.hl(36, 61, 5, '-')
    m.put(38, 60, '*')
    m.box(43, 62, 9, 1, '%')
    m.put(48, 61, TL)
    m.row(44, 61, '$$')
    m.put(19, 69, '$')
    m.put(10, 56, 'l')
    m.put(30, 56, 'L')
    m.put(46, 58, 'l')
    # secret 1: a fake floor plate drops into a vault; a girder leads back up through it
    m.box(8, 70, 2, 1, 'X')
    m.box(4, 71, 12, 4, '?')
    m.hl(8, 73, 2, '-')
    m.row(5, 74, '$.$.u.$.H')

    # ================================================================ Z2 conveyor gate
    m.hl(54, 70, 17, Q)                    # a belt under three hammers in a low tunnel
    m.put(57, 64, CR1)
    m.put(62, 64, CR1)
    m.put(67, 64, CR1)
    m.put(53, 69, '+')
    m.put(60, 66, 'l')
    m.box(80, 69, 1, 1, '%')
    m.put(80, 68, EY)
    m.box(72, 56, 28, 2, '#')
    m.put(78, 69, T)
    m.put(88, 69, TL)
    m.put(82, 69, GL)
    m.put(92, 69, RG)
    m.hl(84, 67, 4, '-')
    m.put(86, 66, '*')
    m.hl(88, 64, 4, '-')
    m.box(92, 61, 8, 1, '%')
    m.put(96, 60, 'k')
    m.put(98, 60, '$')
    m.put(75, 69, '$')
    m.put(83, 60, 'L')
    m.put(97, 63, 'l')

    # ================================================================ Z3 spring shaft (x100-129, floor 70)
    m.sky(104, 9, 22, 8)
    m.box(109, 70, 13, 2, '~')
    m.put(102, 69, 'C')
    m.box(100, 60, 8, 1, '%')              # L1
    m.put(108, 69, S)
    m.put(104, 59, '*')
    m.hl(109, 60, 3, mv['9'])              # lift up to L2
    m.box(113, 46, 13, 1, '%')             # L2
    m.put(123, 45, RG)
    m.hl(126, 70, 3, mv['0'])              # a lift from the east floor back up to L2
    m.put(120, 45, '*')
    m.put(114, 45, S)
    m.box(100, 36, 12, 1, '%')             # L3
    m.put(105, 35, '*')
    m.put(102, 35, TL)
    m.hl(112, 36, 3, mv['T'])              # lift up to L4
    m.box(116, 24, 14, 1, '%')             # L4
    m.put(124, 23, '*')
    m.put(117, 23, S)
    m.box(120, 16, 10, 1, '%')             # L5 (to Z4)
    m.put(126, 15, '*')
    m.put(110, 30, J)
    m.put(122, 32, J)
    m.put(106, 50, JA)
    m.put(124, 69, '&')
    m.put(128, 69, '+')
    m.put(104, 64, 'l')
    m.put(120, 52, 'L')
    m.put(106, 40, 'l')
    m.put(124, 28, 'L')
    m.put(110, 20, 'l')
    # the blue door at the shaft's foot (to Z5)
    m.vl(130, 67, 3, 'd')
    # secret 2: a vault behind the shaft's west wall from L3
    m.box(99, 34, 1, 2, 'X')
    m.box(91, 32, 8, 4, '?')
    m.row(92, 35, '$.p.$.$')

    # ================================================================ Z4 switch vault (x131-175, floor 34)
    m.box(131, 16, 10, 1, '%')             # entry ledge
    m.put(133, 15, 'C')
    m.box(141, 4, 35, 8, '#')              # the upper corridor's ceiling
    m.box(141, 16, 35, 1, '%')             # the upper corridor's floor
    m.room(142, 16, 3, 1)                  # a hole down into the vault
    m.vl(150, 13, 3, 'A')                  # gate A
    m.put(146, 33, 'q')                    # switch A on the vault floor
    for x, y in ((144, 31), (141, 28), (144, 25), (141, 22), (144, 19)):
        m.hl(x, y, 2, '-')
    m.put(172, 15, 'V')                    # teleporter pads in the corridor
    m.put(174, 15, '1')
    m.put(160, 15, '*')
    m.put(166, 15, TL)
    m.put(156, 15, '$')
    m.put(145, 13, 'l')
    m.put(165, 13, 'L')
    # the vault floor (rows 17-33)
    m.put(134, 33, BL)
    m.put(166, 33, BL)
    m.put(170, 33, RG)
    m.box(155, 31, 6, 3, '%')
    m.put(157, 30, '*')
    m.hl(162, 28, 4, '-')
    m.put(164, 27, '$')
    m.put(137, 26, BLA)
    m.put(140, 33, '+')
    m.put(174, 33, '&')
    m.put(138, 22, 'L')
    m.put(160, 22, 'l')
    m.put(170, 26, 'L')
    # the sealed key room: arriving pad, gold key, switch B opens gate B back into the vault
    m.put(180, 33, 'U')
    m.put(178, 33, '2')
    m.hl(182, 31, 4, '-')
    m.hl(185, 28, 4, '-')
    m.box(178, 25, 5, 1, '%')
    m.put(179, 24, 'K')
    m.put(181, 24, '$')
    m.put(187, 27, 's')
    m.put(186, 33, BLA)
    m.box(176, 31, 2, 3, 'G')              # gate B
    m.put(184, 20, 'l')

    # ================================================================ Z5 plasma bridge (x131-200, plasma 72-75)
    m.box(131, 72, 70, 4, '~')
    m.box(131, 70, 7, 6, '%')              # entry ledge
    m.put(133, 69, 'C')
    m.hl(139, 70, 3, mv['3'])              # -> x143-145
    m.box(146, 70, 4, 6, '%')              # pillar 1
    m.hl(151, 70, 3, mv['4'])              # -> x158-160
    m.box(162, 67, 4, 9, '%')              # pillar 2
    m.hl(167, 67, 3, mv['5'])              # -> x174-176
    m.box(178, 70, 4, 6, '%')              # pillar 3
    m.hl(183, 70, 3, mv['8'])              # -> x188-190
    m.box(193, 70, 8, 6, '%')              # exit ledge
    m.put(156, 40, LZ2)                    # laser fences across the movers
    m.put(188, 40, LZ1)
    m.put(147, 69, BR)
    m.put(179, 69, BRL)
    m.put(163, 66, RG)
    m.put(150, 52, J)
    m.put(185, 48, J)
    m.put(143, 66, '*')
    m.put(156, 65, '*')
    m.put(172, 62, '*')
    m.put(196, 69, '*')
    m.put(198, 69, '+')
    m.hl(159, 64, 4, '-')                  # a side climb to a treasure ledge
    m.hl(164, 61, 4, '-')
    m.box(169, 58, 7, 1, '%')
    m.put(172, 57, '*')
    m.row(170, 57, '$')
    m.row(174, 57, '$$')
    m.put(140, 60, 'L')
    m.put(172, 50, 'L')
    m.put(195, 60, 'l')
    m.put(150, 64, 'l')
    # the gold door into the core gate
    m.vl(201, 67, 3, 'D')

    # ================================================================ Z6 core gate (x202-257, floor 70)
    m.sky(206, 7, 48, 5)
    m.put(205, 69, 'C')
    m.put(225, 69, RG)
    m.put(216, 69, S)
    m.box(202, 60, 13, 1, '%')             # W1
    m.put(210, 59, '*')
    m.put(212, 59, TL)
    m.hl(216, 57, 4, '-')
    m.hl(221, 54, 4, '-')
    m.box(226, 52, 25, 1, '%')             # E1, hammers over it
    m.box(226, 43, 20, 4, '#')
    m.put(231, 47, CR2)
    m.put(236, 47, CR3)
    m.put(241, 47, CR2)
    m.put(234, 51, '*')
    m.put(249, 51, S)
    m.put(240, 42, '*')                    # W2 = the top of the hammer housing
    m.put(230, 42, RG)
    m.put(244, 42, SB)
    m.hl(220, 40, 4, '-')
    m.hl(215, 37, 4, '-')
    m.box(202, 34, 12, 1, '%')             # W3
    m.put(205, 33, '*')
    m.put(208, 33, T)
    m.hl(214, 34, 3, mv['Z'])              # lift up to E3
    m.box(218, 22, 28, 1, '%')             # E3, hammers over it
    m.box(218, 13, 28, 4, '#')
    for x, ch in ((224, CR2), (230, CR3), (236, CR2), (242, CR3)):
        m.put(x, 17, ch)
    m.put(227, 21, '*')
    m.put(239, 21, '$')
    m.hl(247, 19, 4, '-')
    m.hl(252, 16, 4, '-')
    m.box(246, 13, 5, 1, '%')
    m.put(240, 12, 'E')
    m.put(245, 12, '*')
    m.put(222, 12, '$')
    m.put(232, 12, '$')
    m.put(250, 69, GL)
    m.put(214, 69, G)
    m.put(127, 69, TA)
    m.put(190, 69, TA)
    m.put(240, 69, SB)
    m.put(232, 69, '&')
    m.put(255, 69, 'H')
    m.put(212, 26, J)
    m.put(250, 30, JA)
    m.put(210, 64, 'l')
    m.put(236, 60, 'L')
    m.put(222, 46, 'l')
    m.put(208, 40, 'L')
    m.put(232, 28, 'l')
    m.put(250, 24, 'L')
    m.put(226, 10, 'l')
    # secret 3: a fake floor plate, a vault under the core gate
    m.box(238, 70, 2, 1, 'X')
    m.box(232, 71, 13, 4, '?')
    m.hl(238, 73, 2, '-')
    m.row(233, 74, '$.$.o.$.x')
    # treasure trails and supplies
    for x, y, t in ((26, 66, '$.$'), (32, 63, '$$'), (56, 69, '$.$.$'), (101, 59, '$$'), (115, 45, '$.$'),
                    (106, 35, '$$'), (118, 23, '$$'), (121, 15, '$$'), (136, 33, '$.$'), (152, 15, '$'),
                    (147, 66, '$'), (194, 69, '$$'), (203, 59, '$$'), (227, 51, '$'), (203, 33, '$'),
                    (248, 18, '$')):
        m.row(x, y, t)
    for x, y in ((48, 69), (90, 69), (118, 45), (150, 33), (184, 33), (210, 33), (246, 12)):
        m.put(x, y, '&')
    return m


if __name__ == '__main__':
    main(build, 'e4l8')
