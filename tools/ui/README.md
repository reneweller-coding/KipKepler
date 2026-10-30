# HUD and menu art

`make_ui.py` draws everything from the shared palette (tools/common/palette.py) with a small mask toolkit (polygons,
bevel with light from the top left, 1-px OUTLINE, ordered dithering, glow layer). Every picture is checked: palette
colours only, alpha 0 or 255.

    python tools/ui/make_ui.py        # assets/ui/* + enlarged previews and work/ui/contact.png

## Files in assets/ui/

| file | size | notes |
|------|------|-------|
| `hud.png`, `hud.txt`, `hud_glow.png` | 32x32 cells, 8 per row | sprite-sheet format, `anim <name> 1 loop <index>` per icon, anchor 16 16 |
| `bar_frame.png` | 100x14 | frame with the empty (dark) bar inside |
| `bar_fill.png`, `bar_fill_low.png`, `bar_fill_white.png` | 92x8 | green, red, grey (to tint, e.g. per weapon ammo) |
| `bar.txt` | | `frame 100 14`, `fill 4 3 92 8`: draw the frame, then the fill at (4,3) cropped to width round(92 * fraction) |
| `logo.png`, `logo_glow.png` | 420x110 | "KIP KEPLER", prism bevel, orange beacon and stripe; glow = emissive pixels |
| `subtitle.png`, `subtitle_glow.png` | 240x22 | empty plate; write the subtitle into x 12-227, y 4-17 (small font at y 5, centred) |
| `panel.png`, `panel.txt`, `panel_glow.png` | 48x48 | 9-slice, `slice 16`; edges and centre are flat, so stretching and tiling both work |
| `cursor.png`, `cursor_glow.png` | 16x16 | menu arrow pointing right, tip at (13, 8) |
| `weapon_slot.png`, `weapon_slot_selected.png` (+ `_glow`) | 40x40 | interior 32x32 at (4,4): draw the hud weapon icon there |
| `ep1.png` .. `ep4.png` | 200x120 | episode cards: Academy ring, jungle moon Thessa, comet mines of Ysk, Gloam dreadnought |

HUD icon names: crystal, health (alias heart), key_blue, key_gold, score (alias star), clock, power_overdrive,
power_boots, power_shield, ammo, skull, secret, credits, weapon_blaster, weapon_repeater, weapon_scatter,
weapon_ricochet, weapon_cryo, weapon_lancer, weapon_mortar, weapon_arc, weapon_seeker. Weapon colours: blaster cyan,
repeater orange, scatter yellow, ricochet green, cryo icy white, lancer red, mortar violet, arc electric blue, seeker
magenta. Weapons point right like all sprites.
