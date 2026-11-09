---
name: sketch-to-race
description: Turns a photo of a hand-drawn car into a playable racing game that opens in Chrome, with the player's car drawn in the sketch's colours, stripes and spoiler. Reads the drawing into a car spec, optionally makes a studio photo of the car with the Higgsfield connector (only after a yes, because it spends credits), then runs a real build script for a single offline HTML racer (2 laps, 3 rivals, traffic, nitrous, speedometer, position) and rebuilds it for tweaks like night, rain, more traffic, monster truck or a police chase. Use when someone attaches a car drawing and says "turn my drawing into a racing game", "make my sketch a game", "I drew a car, can I race it", "sketch to race", "make a game from this drawing", or asks to change a game it built ("make it night", "add police", "more traffic").
---

# Sketch to Race

One job: the car you drew becomes the car you race, in a game that runs offline in Chrome.
Nothing is posted, bought or shared. Higgsfield credits are only spent after you say yes.

The tools actually run: `scripts/build_game.py` is plain Python 3 (standard library only). It
checks `car.json`, fills `assets/game-template.html` and writes one HTML file with no network
requests. `scripts/`, `assets/` and `references/` sit inside this skill's own folder (usually
`~/.claude/skills/sketch-to-race/`), not the user's folder, so call the script by that full path.
If code execution is off, say so, show car.json, and tell the user to run the command below on
their own computer.

## Steps

1. **Read the sketch.** Look at the attached photo. Write `car.json` in the user's current folder
   following `references/car-spec.md`: body, main colour, stripe colours and layout (and which
   parts they cover), spoiler, wheels, exhausts, plate text, decals, and a one-line `notes`
   reading. Only record what is in the drawing. If it is uncoloured, ask for the colours in one
   question or offer defaults and label them as defaults.
2. **Confirm.** Run `python <skill>/scripts/build_game.py car.json --check`. Show the user a
   short plain list (for example: silver coupe, two blue stripes over hood, roof and trunk, big
   black wing, plate RGA 2005) and ask "Does that match your drawing?" Fix anything they correct.
3. **Studio photo (optional).** Only if the Higgsfield connector is on. Follow
   `references/higgsfield.md`: show the filled prompt, say it uses their Higgsfield credits, and
   wait for a yes before generating one image. Not connected: say so in one line and move on.
4. **Build.** Run
   `python <skill>/scripts/build_game.py car.json -o my-race.html --laps 2 --rivals 3 --traffic medium`.
   If it exits with code 2, fix every listed problem and run it again. Tell the user to
   double-click `my-race.html` (Chrome or Edge), press Enter, and race.
5. **Controls.** Arrow keys: up is gas, down is brake, left and right steer. Shift is nitrous
   (the blue bar refills). R puts the car back on the road. P pauses. Enter starts and restarts.
6. **Tweaks.** Offer three to five from `references/tweaks.md`: night mode, rain, more traffic,
   monster truck, police chase, more rivals, a new city layout. Rebuild to a new file name so
   the working version is kept. If an ask is outside the builder (sound, two players, touch
   controls), say so plainly before editing a copy of the HTML.

## Hard rules

- Never spend Higgsfield credits, or any paid service, without a yes for that exact image.
- Never post, upload, publish or share the game, the sketch or the image. Files stay on the
  user's computer.
- The game makes no network requests. Do not add CDN scripts, fonts, trackers or links to it.
- Do not change the shipped template for one user's tweak. Edit a copy of their built file.
- Keep the car the user's own. If the sketch copies a real brand's logo or a film character,
  leave the logo or character out of car.json and say why.
- Do not claim features the build does not have (sound, online play, phone controls).

## What to hand back

The confirmed car spec as a short list, the path to `car.json`, the path to the game file, the
controls, the studio image if one was made, and three to five tweak ideas as ready-to-send
lines. End with one question: **"Want a tweak, like night mode or a police chase?"**
