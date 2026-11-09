"""Unit tests for scripts/build_game.py. Run: python -m unittest discover -s tests"""
import copy
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import build_game as bg  # noqa: E402

SAMPLE = {
    "name": "RGA 2005",
    "body": "coupe",
    "colors": {"main": "silver", "stripes": ["blue", "#1F5BD6"], "spoiler": "black"},
    "stripes": {"layout": "twin", "over": ["hood", "roof", "trunk"]},
    "spoiler": "big",
    "exhausts": 4,
    "plate": "RGA 2005",
}
TEMPLATE = (ROOT / "assets" / "game-template.html").read_text(encoding="utf-8")


def build(spec, **race):
    car, _ = bg.validate_spec(spec)
    return car, bg.render_html(car, bg.build_race(None, car=car, **race), TEMPLATE)


def config_of(html_text):
    m = re.search(r'<script id="race-config" type="application/json">(.*?)</script>', html_text, re.S)
    return json.loads(m.group(1))


class ColourTests(unittest.TestCase):
    def test_names_hex_and_rgb(self):
        self.assertEqual(bg.normalize_colour("silver"), "#c3c7cc")
        self.assertEqual(bg.normalize_colour("Royal-Blue"), "#2546b8")
        self.assertEqual(bg.normalize_colour("#ABC"), "#aabbcc")
        self.assertEqual(bg.normalize_colour("1f5bd6"), "#1f5bd6")
        self.assertEqual(bg.normalize_colour("rgb(255, 0, 10)"), "#ff000a")

    def test_bad_colours_raise(self):
        for bad in ("blurple", "#12345", "rgb(300,0,0)", "", None, 7):
            with self.assertRaises(bg.SpecError):
                bg.normalize_colour(bad)


class SpecTests(unittest.TestCase):
    def test_sample_is_cleaned(self):
        car, warnings = bg.validate_spec(SAMPLE)
        self.assertEqual(car["colors"]["main"], "#c3c7cc")
        self.assertEqual(car["colors"]["stripes"], ["#1f5bd6", "#1f5bd6"])
        self.assertEqual(car["colors"]["spoiler"], "#111111")
        self.assertEqual(car["stripes"], {"layout": "twin", "over": ["hood", "roof", "trunk"]})
        self.assertEqual(car["spoiler"], "big")
        self.assertEqual(car["plate"], "RGA 2005")
        self.assertEqual(warnings, [])

    def test_aliases(self):
        spec = dict(SAMPLE, body="Monster Truck", spoiler="GT wing", stripes="double")
        car, _ = bg.validate_spec(spec)
        self.assertEqual((car["body"], car["spoiler"], car["stripes"]["layout"]), ("monster-truck", "big", "twin"))

    def test_main_colour_required(self):
        spec = copy.deepcopy(SAMPLE)
        del spec["colors"]["main"]
        with self.assertRaises(bg.SpecError):
            bg.validate_spec(spec)

    def test_every_problem_is_listed(self):
        spec = dict(SAMPLE, body="spaceship", spoiler="enormous", exhausts=9, plate="WAY TOO LONG PLATE")
        with self.assertRaises(bg.SpecError) as ctx:
            bg.validate_spec(spec)
        msg = str(ctx.exception)
        for field in ("body", "spoiler", "exhausts", "plate"):
            self.assertIn(field, msg)

    def test_unknown_fields_warn_not_fail(self):
        _, warnings = bg.validate_spec(dict(SAMPLE, horsepower=900))
        self.assertTrue(any("horsepower" in w for w in warnings))

    def test_web_addresses_rejected(self):
        with self.assertRaises(bg.SpecError):
            bg.validate_spec(dict(SAMPLE, name="see https://example.com"))

    def test_name_defaults_to_plate(self):
        spec = dict(SAMPLE)
        del spec["name"]
        car, _ = bg.validate_spec(spec)
        self.assertEqual(car["name"], "RGA 2005")


class RaceTests(unittest.TestCase):
    def test_defaults_match_the_reel(self):
        race = bg.build_race(None, car={"a": 1})
        self.assertEqual((race["laps"], race["rivals"], race["traffic"], race["time"], race["weather"], race["police"]),
                         (2, 3, "medium", "day", "clear", False))

    def test_seed_is_stable_per_car(self):
        self.assertEqual(bg.build_race(None, car={"a": 1})["seed"], bg.build_race(None, car={"a": 1})["seed"])

    def test_bounds(self):
        for bad in ({"laps": 0}, {"laps": 11}, {"rivals": 8}, {"traffic": "jam"}, {"time": "noon"}):
            with self.assertRaises(bg.SpecError):
                bg.build_race(bad, car={})

    def test_cli_overrides_spec(self):
        race = bg.build_race({"laps": 5, "traffic": "low"}, laps=3, car={})
        self.assertEqual((race["laps"], race["traffic"]), (3, "low"))


class OutputTests(unittest.TestCase):
    def test_output_contains_the_spec(self):
        car, out = build(SAMPLE)
        cfg = config_of(out)
        self.assertEqual(cfg["car"], car)
        self.assertEqual(cfg["race"]["laps"], 2)
        self.assertIn("RGA 2005 | Sketch to Race", out)
        self.assertNotIn("__RACE_CONFIG__", out)

    def test_no_network_urls(self):
        _, out = build(SAMPLE, traffic="high", time="night", weather="rain", police=True)
        self.assertIsNone(re.search(r"https?://|wss?://|//cdn|<link\b|\bsrc\s*=", out, re.I))

    def test_text_cannot_break_out_of_the_script(self):
        spec = dict(SAMPLE, name="</script><b>hi", decals=[{"text": "<i>", "color": "red"}])
        _, out = build(spec)
        self.assertEqual(out.count("</script>"), 2)
        self.assertEqual(config_of(out)["car"]["name"], "</script><b>hi")
        self.assertIn("&lt;/script&gt;", out.split("</title>")[0])

    def test_template_that_loads_from_the_web_is_refused(self):
        car, _ = bg.validate_spec(SAMPLE)
        bad = TEMPLATE.replace("</head>", '<script src="https://cdn.example.com/x.js"></script></head>')
        with self.assertRaises(bg.SpecError):
            bg.render_html(car, bg.build_race(None, car=car), bad)


class CliTests(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run([sys.executable, str(ROOT / "scripts" / "build_game.py")] + list(args),
                              capture_output=True, text=True)

    def test_build_and_check(self):
        with tempfile.TemporaryDirectory() as tmp:
            spec = Path(tmp) / "car.json"
            spec.write_text(json.dumps(SAMPLE), encoding="utf-8")
            out = Path(tmp) / "race.html"
            res = self.run_cli(str(spec), "-o", str(out), "--laps", "2", "--rivals", "3", "--traffic", "medium")
            self.assertEqual(res.returncode, 0, res.stderr)
            self.assertTrue(out.exists())
            self.assertIn("twin stripes", res.stdout)
            res = self.run_cli(str(spec), "--check", "--night", "--police")
            self.assertEqual(res.returncode, 0, res.stderr)
            self.assertIn('"police": true', res.stdout)

    def test_bad_spec_exits_2(self):
        with tempfile.TemporaryDirectory() as tmp:
            spec = Path(tmp) / "car.json"
            spec.write_text(json.dumps(dict(SAMPLE, body="spaceship")), encoding="utf-8")
            res = self.run_cli(str(spec), "-o", str(Path(tmp) / "x.html"))
            self.assertEqual(res.returncode, 2)
            self.assertIn("body", res.stderr)
            self.assertFalse((Path(tmp) / "x.html").exists())

    def test_example_round_trips(self):
        res = self.run_cli("--example")
        self.assertEqual(res.returncode, 0)
        bg.validate_spec(json.loads(res.stdout))


if __name__ == "__main__":
    unittest.main()
