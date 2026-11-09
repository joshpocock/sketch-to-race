#!/usr/bin/env python3
"""Build a playable, offline racing game themed to a car spec.

    python scripts/build_game.py car.json -o my-race.html
    python scripts/build_game.py car.json -o my-race.html --laps 3 --rivals 5 --traffic high --night --rain
    python scripts/build_game.py car.json --check        # validate and print the cleaned spec
    python scripts/build_game.py --example > car.json    # a starter spec

Standard library only (Python 3.8+). The output is one HTML file with no network
requests: double-click it, and it opens in Chrome. Press Enter to race.
"""
import argparse
import html
import json
import re
import sys
import zlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
TEMPLATE = HERE.parent / "assets" / "game-template.html"

BODIES = ("coupe", "supercar", "sedan", "hatchback", "muscle", "suv", "pickup", "van", "monster-truck")
BODY_ALIASES = {
    "sports car": "supercar", "sports": "supercar", "sportscar": "supercar", "hypercar": "supercar",
    "race car": "supercar", "racecar": "supercar", "saloon": "sedan", "hatch": "hatchback",
    "muscle car": "muscle", "truck": "pickup", "pickup truck": "pickup", "monster truck": "monster-truck",
    "monster": "monster-truck", "jeep": "suv", "4x4": "suv", "minivan": "van", "bus": "van",
}
STRIPE_LAYOUTS = ("none", "single", "twin", "triple", "side", "offset")
STRIPE_ALIASES = {
    "double": "twin", "two": "twin", "dual": "twin", "racing": "twin", "one": "single", "center": "single",
    "centre": "single", "three": "triple", "rally": "offset", "sides": "side", "no": "none",
}
STRIPE_PARTS = ("hood", "roof", "trunk")
SPOILERS = ("none", "small", "big")
SPOILER_ALIASES = {
    "wing": "big", "large": "big", "gt": "big", "gt wing": "big", "huge": "big", "rear wing": "big",
    "lip": "small", "ducktail": "small", "low": "small", "no": "none",
}
WHEELS = ("normal", "big")
TRAFFIC = ("none", "low", "medium", "high", "max")
TIMES = ("day", "dusk", "night")
WEATHER = ("clear", "rain")
TOP_KEYS = {"name", "body", "colors", "colours", "stripes", "spoiler", "wheels", "exhausts", "plate",
            "decals", "notes", "race"}

NAMED_COLOURS = {
    "black": "#111111", "matte black": "#1a1a1a", "white": "#f4f4f4", "pearl white": "#efeee8",
    "silver": "#c3c7cc", "grey": "#7d8288", "gray": "#7d8288", "light grey": "#b5b9be", "light gray": "#b5b9be",
    "dark grey": "#45494e", "dark gray": "#45494e", "gunmetal": "#3c4248", "charcoal": "#2f3236",
    "red": "#d0202a", "dark red": "#8c1219", "maroon": "#6b0f1a", "crimson": "#b3122e",
    "orange": "#f07a12", "yellow": "#f5c518", "gold": "#c9a227", "lime": "#8fd400", "green": "#1f9d45",
    "dark green": "#0f5a2e", "racing green": "#0e4429", "mint": "#7fdcb4", "olive": "#6b7a2a",
    "teal": "#138a8a", "turquoise": "#2cc5c0", "cyan": "#20c4e8", "sky blue": "#5fb3f0",
    "light blue": "#7cc1f2", "blue": "#1f5bd6", "royal blue": "#2546b8", "dark blue": "#13307a",
    "navy": "#14224f", "purple": "#6a2fb0", "violet": "#8a4fd8", "pink": "#f27db4", "hot pink": "#ff3d9a",
    "magenta": "#d0218c", "brown": "#6b4429", "tan": "#c8a77a", "beige": "#d9c9a8", "cream": "#efe6cf",
    "bronze": "#a8742f", "copper": "#b5643a", "chrome": "#d6dadf",
}
HEX_RE = re.compile(r"^#?([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")
RGB_RE = re.compile(r"^rgb\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})\s*\)$")
PLATE_RE = re.compile(r"^[A-Za-z0-9 .\-]*$")
NETWORK_RE = re.compile(r"(https?:|wss?:|ftp:)//|//cdn|<link\b|\bsrc\s*=|@import|\bfetch\s*\(|XMLHttpRequest|WebSocket\s*\(", re.I)

EXAMPLE = {
    "name": "RGA 2005",
    "body": "coupe",
    "colors": {"main": "silver", "stripes": ["blue", "blue"], "spoiler": "black", "rims": "#9aa0a6"},
    "stripes": {"layout": "twin", "over": ["hood", "roof", "trunk"]},
    "spoiler": "big",
    "wheels": "normal",
    "exhausts": 4,
    "plate": "RGA 2005",
    "decals": [],
    "notes": "Silver coupe, two blue racing stripes over hood, roof and trunk, big black rear wing, four exhausts.",
}


class SpecError(ValueError):
    """Raised when car.json cannot be turned into a game. The message lists every problem."""


def normalize_colour(value, field="colour"):
    """Return '#rrggbb' for a hex code, rgb(...) or a common colour name. Raise SpecError otherwise."""
    if not isinstance(value, str) or not value.strip():
        raise SpecError("%s: expected a colour name or hex code, got %r" % (field, value))
    text = value.strip().lower().replace("_", " ").replace("-", " ")
    text = re.sub(r"\s+", " ", text)
    if text in NAMED_COLOURS:
        return NAMED_COLOURS[text]
    m = HEX_RE.match(value.strip())
    if m:
        digits = m.group(1).lower()
        if len(digits) == 3:
            digits = "".join(ch * 2 for ch in digits)
        return "#" + digits
    m = RGB_RE.match(text)
    if m:
        parts = [int(p) for p in m.groups()]
        if all(0 <= p <= 255 for p in parts):
            return "#%02x%02x%02x" % tuple(parts)
    raise SpecError("%s: %r is not a colour I know. Use a hex code like #1f5bd6 or a name like 'blue'." % (field, value))


def _choice(value, allowed, aliases, field, default, errors):
    if value is None:
        return default
    if not isinstance(value, str):
        errors.append("%s: expected one of %s" % (field, ", ".join(allowed)))
        return default
    key = re.sub(r"\s+", " ", value.strip().lower().replace("_", " "))
    key = aliases.get(key, key).replace(" ", "-") if key not in allowed else key
    if key in allowed:
        return key
    errors.append("%s: %r is not one of %s" % (field, value, ", ".join(allowed)))
    return default


def _text(value, field, limit, errors, pattern=None):
    if value is None:
        return ""
    if not isinstance(value, (str, int)):
        errors.append("%s: expected text" % field)
        return ""
    text = str(value).strip()
    if any(ord(ch) < 32 for ch in text):
        errors.append("%s: control characters are not allowed" % field)
    if "://" in text:
        errors.append("%s: web addresses are not allowed in the game" % field)
    if len(text) > limit:
        errors.append("%s: %r is longer than %d characters" % (field, text, limit))
    if pattern is not None and not pattern.match(text):
        errors.append("%s: use letters, numbers, spaces, dots and hyphens only" % field)
    return text


def _colour(value, field, errors, default):
    if value is None:
        return default
    try:
        return normalize_colour(value, field)
    except SpecError as exc:
        errors.append(str(exc))
        return default


def validate_spec(raw):
    """Check a car spec and return (car, warnings). Raises SpecError listing every problem."""
    if not isinstance(raw, dict):
        raise SpecError("car.json must be a JSON object, like the one from --example")
    errors, warnings = [], []
    for key in raw:
        if key not in TOP_KEYS:
            warnings.append("ignored unknown field %r" % key)

    colours = raw.get("colors", raw.get("colours"))
    if not isinstance(colours, dict):
        errors.append("colors: needed, with at least colors.main (the body colour)")
        colours = {}
    if "main" not in colours:
        errors.append("colors.main: needed (the main body colour)")
    main = _colour(colours.get("main"), "colors.main", errors, "#c3c7cc")

    body = _choice(raw.get("body"), BODIES, BODY_ALIASES, "body", "coupe", errors)

    stripes_raw = raw.get("stripes", "none")
    over = list(STRIPE_PARTS)
    if isinstance(stripes_raw, dict):
        layout = _choice(stripes_raw.get("layout", "none"), STRIPE_LAYOUTS, STRIPE_ALIASES, "stripes.layout", "none", errors)
        if "over" in stripes_raw:
            parts = stripes_raw.get("over")
            if not isinstance(parts, list) or not all(isinstance(p, str) for p in parts):
                errors.append("stripes.over: expected a list such as [\"hood\", \"roof\", \"trunk\"]")
            else:
                over = []
                for p in parts:
                    p = p.strip().lower()
                    p = {"boot": "trunk", "bonnet": "hood", "top": "roof"}.get(p, p)
                    if p not in STRIPE_PARTS:
                        errors.append("stripes.over: %r is not one of %s" % (p, ", ".join(STRIPE_PARTS)))
                    elif p not in over:
                        over.append(p)
    else:
        layout = _choice(stripes_raw, STRIPE_LAYOUTS, STRIPE_ALIASES, "stripes", "none", errors)

    stripe_colours = colours.get("stripes", colours.get("stripe"))
    if stripe_colours is None:
        stripe_list = ["#f4f4f4"]
        if layout != "none":
            warnings.append("no stripe colour given, using white")
    else:
        if isinstance(stripe_colours, str):
            stripe_colours = [stripe_colours]
        if not isinstance(stripe_colours, list) or not stripe_colours:
            errors.append("colors.stripes: expected a colour or a list of colours")
            stripe_list = ["#f4f4f4"]
        else:
            stripe_list = [_colour(c, "colors.stripes[%d]" % i, errors, "#f4f4f4") for i, c in enumerate(stripe_colours[:4])]

    spoiler = _choice(raw.get("spoiler", "none"), SPOILERS, SPOILER_ALIASES, "spoiler", "none", errors)
    spoiler_colour = _colour(colours.get("spoiler"), "colors.spoiler", errors, "#111111" if spoiler == "big" else main)
    wheels = _choice(raw.get("wheels", "normal"), WHEELS, {"large": "big", "huge": "big", "standard": "normal"}, "wheels", "normal", errors)
    rims = _colour(colours.get("rims"), "colors.rims", errors, "#b8bcc2")
    glass = _colour(colours.get("glass"), "colors.glass", errors, "#1d2731")

    exhausts = raw.get("exhausts", 2)
    if isinstance(exhausts, bool) or not isinstance(exhausts, int) or not 0 <= exhausts <= 4:
        errors.append("exhausts: expected a whole number from 0 to 4")
        exhausts = 2

    plate = _text(raw.get("plate"), "plate", 10, errors, PLATE_RE).upper()
    name = _text(raw.get("name"), "name", 24, errors)
    if not name:
        name = plate or ("%s %s" % (_colour_word(main), body.replace("-", " "))).upper()

    decals = []
    decals_raw = raw.get("decals", [])
    if not isinstance(decals_raw, list):
        errors.append("decals: expected a list like [{\"text\": \"05\", \"color\": \"white\"}]")
        decals_raw = []
    if len(decals_raw) > 3:
        errors.append("decals: three at most")
    for i, d in enumerate(decals_raw[:3]):
        if isinstance(d, str):
            d = {"text": d}
        if not isinstance(d, dict):
            errors.append("decals[%d]: expected {\"text\": ..., \"color\": ...}" % i)
            continue
        text = _text(d.get("text"), "decals[%d].text" % i, 8, errors)
        if text:
            decals.append({"text": text, "color": _colour(d.get("color", d.get("colour")), "decals[%d].color" % i, errors, "#f4f4f4")})

    notes = _text(raw.get("notes"), "notes", 400, errors)

    if errors:
        raise SpecError("car.json has %d problem(s):\n  - %s" % (len(errors), "\n  - ".join(errors)))
    car = {
        "name": name, "body": body,
        "colors": {"main": main, "stripes": stripe_list, "spoiler": spoiler_colour, "rims": rims, "glass": glass},
        "stripes": {"layout": layout, "over": over}, "spoiler": spoiler, "wheels": wheels,
        "exhausts": exhausts, "plate": plate, "decals": decals, "notes": notes,
    }
    return car, warnings


def _colour_word(hex_code):
    for word, code in NAMED_COLOURS.items():
        if code == hex_code:
            return word
    return "custom"


def build_race(raw_race, laps=None, rivals=None, traffic=None, time=None, weather=None, police=None, seed=None, car=None):
    """Merge race settings from car.json with command-line overrides. Raises SpecError."""
    raw_race = raw_race if isinstance(raw_race, dict) else {}
    errors = []

    def pick(cli, key, default):
        return cli if cli is not None else raw_race.get(key, default)

    race = {
        "laps": pick(laps, "laps", 2), "rivals": pick(rivals, "rivals", 3),
        "traffic": pick(traffic, "traffic", "medium"), "time": pick(time, "time", "day"),
        "weather": pick(weather, "weather", "clear"), "police": bool(pick(police, "police", False)),
    }
    if isinstance(race["laps"], bool) or not isinstance(race["laps"], int) or not 1 <= race["laps"] <= 10:
        errors.append("laps: 1 to 10")
    if isinstance(race["rivals"], bool) or not isinstance(race["rivals"], int) or not 0 <= race["rivals"] <= 7:
        errors.append("rivals: 0 to 7")
    for key, allowed in (("traffic", TRAFFIC), ("time", TIMES), ("weather", WEATHER)):
        if race[key] not in allowed:
            errors.append("%s: one of %s" % (key, ", ".join(allowed)))
    seed_value = pick(seed, "seed", None)
    if seed_value is None:
        basis = json.dumps(car or {}, sort_keys=True).encode("utf-8")
        seed_value = zlib.crc32(basis) % 2147483647
    if isinstance(seed_value, bool) or not isinstance(seed_value, int) or seed_value < 0:
        errors.append("seed: a whole number, 0 or more")
        seed_value = 1
    race["seed"] = int(seed_value) % 2147483647
    if errors:
        raise SpecError("race settings: " + "; ".join(errors))
    return race


def render_html(car, race, template_text):
    """Fill the template. The config is JSON with every '<' escaped, so text can never close the script tag."""
    if "__RACE_CONFIG__" not in template_text or "__RACE_TITLE__" not in template_text:
        raise SpecError("the game template is missing its placeholders")
    config = json.dumps({"car": car, "race": race}, ensure_ascii=True, sort_keys=True)
    config = config.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    title = html.escape("%s | Sketch to Race" % car["name"])
    out = template_text.replace("__RACE_CONFIG__", config).replace("__RACE_TITLE__", title)
    hit = NETWORK_RE.search(out)
    if hit:
        raise SpecError("refusing to write a game that would load something from the network (%r)" % hit.group(0))
    return out


def describe(car, race):
    stripes = car["stripes"]["layout"]
    if stripes != "none":
        stripes = "%s stripes %s over %s" % (stripes, "/".join(car["colors"]["stripes"]), ", ".join(car["stripes"]["over"]))
    else:
        stripes = "no stripes"
    return (
        "car:  %s | %s %s | %s | spoiler %s | wheels %s | %d exhausts | plate %s\n"
        "race: %d laps | %d rivals | %s traffic | %s | %s%s | seed %d"
        % (car["name"], car["colors"]["main"], car["body"], stripes, car["spoiler"], car["wheels"],
           car["exhausts"], car["plate"] or "none", race["laps"], race["rivals"], race["traffic"],
           race["time"], race["weather"], " | police chase" if race["police"] else "", race["seed"])
    )


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Build a single-file offline racing game from a car spec (car.json).",
        epilog="Example: python scripts/build_game.py car.json -o my-race.html --laps 2 --rivals 3 --traffic medium",
    )
    parser.add_argument("spec", nargs="?", help="path to car.json")
    parser.add_argument("-o", "--out", default="my-race.html", help="output HTML file (default my-race.html)")
    parser.add_argument("--laps", type=int, help="1 to 10 (default 2)")
    parser.add_argument("--rivals", type=int, help="0 to 7 (default 3)")
    parser.add_argument("--traffic", choices=TRAFFIC, help="default medium")
    parser.add_argument("--time", choices=TIMES, help="day, dusk or night (default day)")
    parser.add_argument("--night", action="store_true", help="same as --time night")
    parser.add_argument("--rain", action="store_true", help="wet roads, rain and less grip")
    parser.add_argument("--police", action="store_true", help="add a police car that chases you")
    parser.add_argument("--seed", type=int, help="change the city layout (any whole number)")
    parser.add_argument("--check", action="store_true", help="validate car.json and print the cleaned spec, write nothing")
    parser.add_argument("--example", action="store_true", help="print a starter car.json and exit")
    parser.add_argument("--template", default=str(TEMPLATE), help=argparse.SUPPRESS)
    args = parser.parse_args(argv)

    if args.example:
        print(json.dumps(EXAMPLE, indent=2))
        return 0
    if not args.spec:
        parser.error("give the path to car.json (or use --example to get one)")
    try:
        raw = json.loads(Path(args.spec).read_text(encoding="utf-8"))
    except FileNotFoundError:
        print("error: %s not found" % args.spec, file=sys.stderr)
        return 2
    except (ValueError, UnicodeDecodeError) as exc:
        print("error: %s is not valid JSON (%s)" % (args.spec, exc), file=sys.stderr)
        return 2
    try:
        car, warnings = validate_spec(raw)
        race = build_race(
            raw.get("race") if isinstance(raw, dict) else None, laps=args.laps, rivals=args.rivals,
            traffic=args.traffic, time="night" if args.night else args.time,
            weather="rain" if args.rain else None, police=True if args.police else None,
            seed=args.seed, car=car,
        )
    except SpecError as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 2
    for w in warnings:
        print("note: %s" % w)
    if args.check:
        print(json.dumps({"car": car, "race": race}, indent=2))
        print(describe(car, race))
        return 0
    try:
        template_text = Path(args.template).read_text(encoding="utf-8")
        out_html = render_html(car, race, template_text)
    except (OSError, SpecError) as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 2
    out = Path(args.out)
    if out.parent and not out.parent.exists():
        out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(out_html, encoding="utf-8")
    print("wrote %s (%d KB, no network requests)" % (out, (len(out_html.encode("utf-8")) + 1023) // 1024))
    print(describe(car, race))
    print("Open it in Chrome (double-click the file), then press Enter to race.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
