# Sketch to Race

One Claude skill that turns a photo of a car you drew into a racing game you can play in Chrome.
Free, MIT, no signup. The game needs no API key and nothing to connect.

**Nothing is posted or bought for you. The optional studio photo uses your own Higgsfield
account, and Claude asks before it spends a single credit.**

Draw a car, snap a photo, drop it into Claude. Claude reads the drawing (colour, stripes,
spoiler, wheels, plate), checks it with you, then a small Python tool builds one HTML file: a
street race where the car you drive is your car, stripes and wing included.

## Install

**Claude Code, one paste.** Paste this into Claude Code:

```
Install the Sketch to Race skill: clone https://github.com/joshpocock/sketch-to-race into ~/.claude/skills/sketch-to-race, then confirm /sketch-to-race works.
```

Or in a terminal:

```
git clone https://github.com/joshpocock/sketch-to-race ~/.claude/skills/sketch-to-race
```

**Claude.ai (website or app).** Turn on Settings, Capabilities, **Code execution and file
creation**. On this GitHub page click Code, Download ZIP. In Claude go to Customize, Skills, +,
Upload a skill, and pick the zip.

## Run it

Attach the photo of your drawing and send:

```
Use the sketch-to-race skill: turn the car in this photo into a racing game I can play in Chrome.
```

| Step | What happens |
|---|---|
| Read the sketch | Claude writes `car.json`: body, colours, stripes and where they run, spoiler, wheels, exhausts, plate |
| Check it | You see the spec as a short list and fix anything it got wrong |
| Studio photo (optional) | With the Higgsfield connector on, one clean photo of your car on a dark background, only after you say yes |
| Build | `build_game.py` writes `my-race.html` |
| Race | Double-click the file, press Enter |
| Tweak | Night, rain, more traffic, monster truck, police chase, more rivals, a new city |

## The game

- City street circuit, 2 laps, 3 rivals, traffic in three lanes
- Start countdown, speedometer, nitrous bar, lap, time, best lap and position on screen
- Finish screen with the standings, and Enter to race again
- One file, about 52 KB, no internet needed, nothing loaded from anywhere

| Key | Does |
|---|---|
| Up / Down | Gas / brake |
| Left / Right | Steer |
| Shift | Nitrous (the blue bar refills) |
| R | Back on the road |
| P | Pause |
| Enter | Start, or race again |

## One car, start to finish

The car from the demo: a silver coupe with two blue racing stripes over the hood, roof and trunk,
a big black rear wing, four exhausts and the plate RGA 2005. That spec is in
`examples/reel-car.json`. Real tool output:

```
$ python scripts/build_game.py examples/reel-car.json -o my-race.html
wrote my-race.html (52 KB, no network requests)
car:  RGA 2005 | #c3c7cc coupe | twin stripes #1f5bd6/#1f5bd6 over hood, roof, trunk | spoiler big | wheels normal | 4 exhausts | plate RGA 2005
race: 2 laps | 3 rivals | medium traffic | day | clear | seed 2136601691
Open it in Chrome (double-click the file), then press Enter to race.
```

## The tool

`scripts/build_game.py` is plain Python 3.8+ with no installs.

```
python scripts/build_game.py --example > car.json               # a starter spec
python scripts/build_game.py car.json --check                   # validate, list every problem
python scripts/build_game.py car.json -o my-race.html           # build the game
python scripts/build_game.py car.json -o night.html --night --rain --police --traffic high
python -m unittest discover -s tests                            # 20 tests
```

Options: `--laps 1-10`, `--rivals 0-7`, `--traffic none|low|medium|high|max`,
`--time day|dusk|night` (or `--night`), `--rain`, `--police`, `--seed N` for a different city.
The spec format is in `references/car-spec.md`, the tweak list in `references/tweaks.md`.

## Fine print

- Every drawing reads a little differently. Check the spec before it builds, and say what to fix.
- The game is drawn in code from your spec (a pseudo 3D racer, the old arcade kind). It is a
  lookalike of your car, not a 3D model of it.
- Keyboard only. No sound, no online play, no phone controls.
- Keep other brands' logos and characters out of your drawing.
- The tool and the game run on your computer. Your photo goes to Claude like any photo you
  attach, and the optional studio photo request goes to Higgsfield only after your yes.

Made by Josh Pocock. The step-by-step page: https://strideaiacademy.com/r/sketch-to-race

MIT licence.
