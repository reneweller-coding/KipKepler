# KIP KEPLER

A 2D action platformer in HD pixel art: Kip Kepler, the most junior cadet of the Beacon Corps, collects the shards
of four shattered beacons across four episodes of nine levels each -- crystals open the exit, key cards open doors,
switches move walls, fake walls hide secrets, and nine science-fiction weapons (bought up at the Quartermaster
between levels) deal with what lives there. Four bosses, a secret level per episode behind a hidden warp, the
Commodore's radio messages (spoken, German and English), logbook pages, medals, 40 awards, high scores, New Game+,
boss rush, time trials, an assist mode and a level editor. In the spirit of the early-90s shareware jump-and-runs,
with its own world, levels and characters. Windows, Linux and the Steam Deck.

## Build

    .\build.ps1                 # Windows, MSVC: bin\msvc\KipKepler.exe and bin\msvc\KeplerTool.exe
    bash Deploy/build_linux.sh  # Linux / Steam Deck (WSL Ubuntu 22.04, GCC 12): dist/KipKepler-<v>-linux-x86_64.tar.gz
    .\Deploy\build_release.ps1# both packages into dist/

C++20 on raylib 5.5 (its sources in third_party/raylib, no download). The game reads assets/ beside the program, else
the source tree's.

## Play

Keyboard: arrows/WASD run, Up aims up, Down + jump drops through platforms, Space/K/Z jump, Ctrl/J/X or the left
mouse button fire (hold the blaster to charge), L/C or the right mouse button alt fire, Q/E or the wheel switch
weapons, Esc/P pause, F11 or Alt+Enter fullscreen. Gamepad / Steam Deck: stick or d-pad, A jump, X/B/R2 fire, Y/L2
alt fire, LB/RB weapons, Start pause. On the Deck
(`SteamDeck=1`) the game runs fullscreen at 1280 x 800 (640 x 400 virtual pixels).

The saves and settings live in %APPDATA%\KipKepler (Linux: ~/.local/share/KipKepler).

## Layout

| Path | What |
|---|---|
| src/ | the game: App (menus, flow), World* (one level in play: hero, weapons, enemies, bosses, drawing), Physics (shared with the checker), Level (the file format), Checker, Screen (virtual pixels, light, bloom), Assets, Audio, Text, Save, Input |
| src/Editor* | the level editor (Extras > Level editor, 9 slots in the user folder; F1 shows its keys) |
| src/Bot.* | the autopilot (title demo, `--autotest`) on the checker's graph |
| src/tool/ | KeplerTool: `check` (reachability with the hero's own physics), `checkall`, `render` (CPU picture of a level) |
| docs/DESIGN.md | the contract between engine and generators: pixels, physics, the level format, sheets, tiles, sounds |
| docs/LEVELS.md | the plan of the 36 levels and the rules of level design |
| tools/ | the asset generators (Python): common/palette.py, sprites/ (a signed-distance-field baker: 3D parts -> pixel art), tiles/, backgrounds/, sfx/, fonts/, ui/, music/ (ACE-Step via the AudioGenerator), story/ (FLUX stills, pixelated), voices/ (Qwen3-TTS), sfx/make_ambience.py; gpu_queue.py runs the GPU jobs one after another when the GPU is free; autotest_all.py runs the autopilot over all 40 levels |
| assets/ | what the game reads: levels, sprites, tiles, bg, sound, music, fonts, ui, text |

## Test options

    KipKepler --level FILE | --episode N --stage M      play a level directly
    KipKepler --shot OUT.png [--at X,Y] [--warm S] [--hold rljfu] [--weapons]   a picture after S seconds (tiles for --at)
    KipKepler --menu title|main|episodes|levels|shop|options|difficulty|story|tally|pause|extras|awards|logbook|radio --shot OUT.png
    KipKepler --autotest REPORT [--limit S] [--level FILE | --episode N]   the autopilot, headless and muted
    KipKepler --editor FILE                                                the level editor on a file
    KipKepler --mute --windowed --w W --h H --lang de|en --difficulty 0-2
    KeplerTool check LEVEL [overview.png] | checkall DIR | render LEVEL OUT.png [scale | x y w h]
