# Tweaks: what each request changes

Most tweaks are a flag or a one-field edit to car.json, then a rebuild. Rebuild to a new file name
(`my-race-night.html`) so the version that worked is kept.

| The user says | Do this |
|---|---|
| "night mode", "make it night" | `--night` (or `--time night`). Lit windows, street lamps, neon signs, headlight beam. |
| "sunset", "golden hour" | `--time dusk` |
| "make it rain", "wet roads" | `--rain`. Rain streaks, darker roads, a little less grip for everyone. |
| "more traffic", "rush hour" | `--traffic high` or `--traffic max`. "No traffic" is `--traffic none`. |
| "more rivals", "harder" | `--rivals 5` (up to 7). "Just me" is `--rivals 0`. |
| "longer race" | `--laps 3` (up to 10). |
| "police chase", "cops" | `--police`. A police car starts behind you and chases. If it catches you, you are pulled over and lose speed. |
| "monster truck" | Set `"body": "monster-truck"` in car.json. Keep the colours and stripes. |
| "bigger wheels" | `"wheels": "big"` |
| "different city", "new track" | `--seed` with any other whole number. Each seed is a different street layout. |
| "change my colours", "add a number 7" | Edit `colors` or add `{"text": "7", "color": "white"}` to `decals`. |

Flags combine: `--night --rain --police --traffic high` is a wet night chase.

## Asks the tool does not cover

Two-player, a phone touch layout, a different camera, sound, weapons, a map editor: these need
changes to the game code itself. Say plainly that the builder does not do it. If the user still
wants it, copy the built HTML file, edit the copy (one change at a time), test it opens and
plays, and keep the original next to it. Never edit `assets/game-template.html` for one user's
tweak.

## If a rebuild fails

The tool prints every problem in car.json at once and exits with code 2. Fix those fields and
run it again. It never writes a half-built file.
