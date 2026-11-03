"""Checklist card limits, escaping and duplex placement."""
import json
from pathlib import Path
import sys
import unittest

SKILL = Path(__file__).resolve().parents[1] / "plugins/checklist-card/skills/checklist-card"
sys.path.insert(0, str(SKILL / "scripts"))
from make_card import build, position, validate, WIDTH

EXAMPLE = json.loads((SKILL / "examples/card.json").read_text(encoding="utf-8"))


class ChecklistCardTests(unittest.TestCase):
    def test_example_builds_front_and_back(self):
        result = build(EXAMPLE)
        self.assertEqual(result.count('class="sheet"'), 2)
        self.assertIn("Before leaving home", result)

    def test_copies_flow_to_new_sheets(self):
        self.assertEqual(build(EXAMPLE, 5).count('class="sheet"'), 4)

    def test_rejects_what_does_not_fit_and_reports_all(self):
        problems = validate({"cards": [{"title": "x" * 50, "steps": ["a"] * 6}]})
        self.assertEqual(len(problems), 3)
        with self.assertRaises(ValueError):
            build({"cards": [{"title": "ok", "steps": ["x" * 61]}]})

    def test_escapes_content(self):
        self.assertNotIn("<b>", build({"cards": [{"title": "<b>", "steps": ["<b>"]}]}))

    def test_back_mirrors_front_on_long_edge(self):
        for index in range(4):
            front_x, front_y = position(index, False)
            back_x, back_y = position(index, True)
            self.assertEqual(front_x + back_x + WIDTH, 210)
            self.assertEqual(front_y, back_y)


if __name__ == "__main__":
    unittest.main()
