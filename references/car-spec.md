# car.json: reading a sketch into a spec

The game draws the player car from behind (chase camera), so the things that show are the body
shape, the main colour, stripes over the roof and trunk, the spoiler, the wheels, the exhausts,
the plate and up to two decals. Write only what you can see in the drawing. If a detail is
unclear, pick the simplest reading and say so when you show the spec.

## Fields

| Field | Values | Notes |
|---|---|---|
| `name` | up to 24 characters | Shown on the title screen. Defaults to the plate text. |
| `body` | `coupe`, `supercar`, `sedan`, `hatchback`, `muscle`, `suv`, `pickup`, `van`, `monster-truck` | Common words also work: "sports car", "truck", "monster truck", "jeep". |
| `colors.main` | colour name or hex | Required. The body colour. |
| `colors.stripes` | one colour or a list (up to 4) | Each stripe band takes the next colour in the list. |
| `colors.spoiler` | colour | Defaults to black for a big wing, body colour for a small one. |
| `colors.rims`, `colors.glass` | colour | Optional. |
| `stripes` | `none`, `single`, `twin`, `triple`, `side`, `offset`, or `{"layout": ..., "over": ["hood", "roof", "trunk"]}` | Two stripes down the middle is `twin`. A line along the doors is `side`. One stripe off-centre is `offset`. |
| `spoiler` | `none`, `small`, `big` | "wing", "GT wing" mean `big`. "lip", "ducktail" mean `small`. |
| `wheels` | `normal`, `big` | `big` lifts the car and fattens the tyres. |
| `exhausts` | 0 to 4 | Count the pipes if the sketch shows them, else 2. |
| `plate` | up to 10 letters, numbers, spaces, dots, hyphens | Printed on the rear plate. |
| `decals` | up to 3 items `{"text": "05", "color": "white"}` | Text up to 8 characters. The first two show on the rear. |
| `notes` | free text, up to 400 characters | Your one-line reading of the sketch. Not used by the game. |
| `race` | `{"laps": 2, "rivals": 3, "traffic": "medium", "time": "day", "weather": "clear", "police": false, "seed": 1}` | Optional. Command-line flags override it. |

Colour names the tool knows: black, matte black, white, pearl white, silver, grey, light grey,
dark grey, gunmetal, charcoal, red, dark red, maroon, crimson, orange, yellow, gold, lime, green,
dark green, racing green, mint, olive, teal, turquoise, cyan, sky blue, light blue, blue, royal
blue, dark blue, navy, purple, violet, pink, hot pink, magenta, brown, tan, beige, cream, bronze,
copper, chrome. Anything else: use a hex code such as `#1f5bd6`, or `rgb(31, 91, 214)`.

## Reading a pencil or pen sketch

- An uncoloured sketch has no colour. Ask the user for the colours in one question, or offer a
  default (silver body, black wing) and say it is a default.
- Two parallel lines down the bonnet and roof are `twin` stripes. Shading between them means
  filled stripes; ask the colour if it is not written or coloured in.
- A plank on two posts above the trunk is a `big` spoiler. A small upturn at the trunk edge is
  `small`.
- Very large wheels or a lifted body read as `monster-truck` or `wheels: "big"`.
- Text on the plate: copy it exactly, uppercase. If it is unreadable, leave `plate` empty.

## Example (the car from the demo)

```json
{
  "name": "RGA 2005",
  "body": "coupe",
  "colors": {"main": "silver", "stripes": ["blue", "blue"], "spoiler": "black"},
  "stripes": {"layout": "twin", "over": ["hood", "roof", "trunk"]},
  "spoiler": "big",
  "exhausts": 4,
  "plate": "RGA 2005",
  "notes": "Silver coupe, two blue racing stripes over hood, roof and trunk, big black rear wing."
}
```

`python scripts/build_game.py car.json --check` validates a spec, lists every problem at once and
prints the cleaned version without writing a game.
