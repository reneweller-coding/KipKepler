# Sound effects

`make_sfx.py` synthesises every sound of docs/DESIGN.md "Sounds" into `assets/sound/<name>.wav` (44.1 kHz, 16 bit,
mono). No samples, no downloads; deterministic (fixed seeds).

    python tools/sfx/make_sfx.py              # all sounds, work/sfx/levels.txt, work/sfx/contact_*.png
    python tools/sfx/make_sfx.py shoot jump   # only these
    python tools/sfx/make_sfx.py --list

The script warns when DESIGN.md lists a sound it does not make.

## How the sounds are made

A small synth toolkit at the top of the file: band-limited oscillators (PolyBLEP saw/pulse, sine, triangle) with
pitch envelopes, two-operator FM, additive bells, filtered noise (static Butterworth and a time-varying state-variable
filter), grain clouds (sparkles, debris, tinkles), crackle, light bit-crush, and a short convolution tail built from
decaying, darkening noise. Each sound is one function `s_<name>` registered with its loudness target.

`finish()` then: 28 Hz high pass, trim of the silent tail, 1.5 ms fade-in and a short fade-out (no clicks; every
layer also ends at zero), gain to the loudness target, a look-ahead limiter, peak <= -1.1 dBFS.

## Levels

Loudness = the loudest 100 ms window, K-weighted (BS.1770 filters), in LU. Frequent sounds sit low (step -33,
shoot_repeater -30, land -29, jump -27, shoot -25), pickups around -21 to -18, big events high (explosions -18 to -12,
boss roar -11, boss death -10). `work/sfx/levels.txt` lists peak, RMS, loudness, target, length, first/last sample per
file; `work/sfx/contact_*.png` shows waveform and spectrogram of each sound. Judge sounds there, never through the
speakers while someone sits at the machine.

## Extra files for the engine

* `shoot`, `shoot_2`, `shoot_3` and `shoot_repeater`, `shoot_repeater_2`, `shoot_repeater_3`: pick one at random per
  shot. `step`, `step_2`, `step_3` the same.
* `charge` (0.8 s, rising) plays once while the blaster charges; `charge_loop` (0.5 s) is a seamless loop of the
  full charge (every partial an integer number of cycles, starts at zero) to loop while the button stays held;
  `charge_full` pings when the charge is complete.
