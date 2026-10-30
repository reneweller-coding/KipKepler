# Pixel fonts

`make_fonts.py` builds the two fonts from hand-drawn ASCII glyphs (`glyphs_small.py`, `glyphs_big.py`); no system or
downloaded fonts.

    python tools/fonts/make_fonts.py          # both fonts + specimens in work/fonts/
    python tools/fonts/make_fonts.py small    # one font

Output in `assets/fonts/`: `small.png/.txt`, `big.png/.txt`, `big_outline.png` (same layout as big.png).

## Format (docs/DESIGN.md "Fonts")

16 cells per row, in the order of the .txt. The .txt: `cell w h`, `baseline n`, then `<codepoint hex> <advance>` per
glyph (4-digit hex, e.g. `00C4 6`). Order: ASCII 32-126, then `ÄÖÜäöüßéèàçñ€©°•…«»„“”–—’`, then the buttons
U+E000-E009 (A, B, X, Y, LB, RB, dpad, stick, start, select). 130 glyphs, 9 rows.

* Draw a glyph: blit its whole cell at the pen position, then move the pen by its advance. No kerning table.
* Baseline n = the first row below the letters: capitals end on row n-1, descenders start on row n.
* Glyphs are pure white (255,255,255) on transparent, alpha 0/255, so a multiply tint gives any colour.
  `big_outline.png` adds a 1-px palette.OUTLINE border; the white parts still take the tint.
* Digits are tabular (small 6 px, big 13 px advance), so counting HUD numbers do not jitter.
* Some advances exceed the cell width (small: button glyphs 9, em dash 8; big: em dash 16, … 15); that is intended.

| font  | cell    | baseline | cap height | x-height | descenders | glyph columns |
|-------|---------|----------|------------|----------|------------|---------------|
| small | 8 x 12  | 9        | 7 (rows 2-8)  | 5  | rows 9-10  | from 0 |
| big   | 16 x 24 | 19       | 14 (rows 5-18) | 10 | rows 19-22 | 1-14 (room for the outline) |

Line height: 12 / 24 is enough (nothing reaches outside the cell).

## Editing glyphs

A glyph is `== <char> <top row> [advance]` followed by rows of `#` and `.` (all one width). Advance defaults to
width + 1 (small) / + 2 (big). Accented letters are composed from a base glyph and an accent mark (`ACCENTS`,
`COMPOSED`); the big font's button icons are a plate minus a symbol (`PLATES`, `SYMBOLS`, `BUTTONS`). The script
stops when a glyph is missing or leaves its cell. Check `work/fonts/specimen_*_4x_*.png` (4x, 1000-px tiles) and
`work/fonts/sheet_*.png` after a change.
