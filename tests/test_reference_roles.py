"""Reference roles must survive prompt building and a credential-free preview."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "plugins/product-photo-studio/skills/product-photo-studio"


class ReferenceRoleTests(unittest.TestCase):
    def build(self, base, text):
        job = base / "job.toml"
        job.write_text(text, encoding="utf-8")
        return subprocess.run([
            sys.executable, str(SKILL / "scripts/build_prompt.py"), str(job),
            "--out", str(base / "built"),
        ], capture_output=True, text=True, encoding="utf-8")

    def test_all_roles_stay_ordered_through_generator_preview(self):
        text = (SKILL / "examples/on-person/job.toml").read_text(encoding="utf-8")
        text = text.replace('module = "person-context"',
                            'module = "reference-perspective"\nreference = "refs/view.jpg"')
        text += '''
[color_lock]
module = "solid-finish"
part = "canvas"
color = "blue"
description = "the approved blue sample"
reference = "refs/colour.jpg"
avoid = ["purple", "green"]

[logo]
module = "preserve"
file = "refs/logo.png"
'''
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            (base / "refs").mkdir()
            names = ["product.jpg", "view.jpg", "person.jpg", "colour.jpg", "logo.png"]
            for name in names:
                # Preview hashes files but does not decode or send them to a model.
                (base / "refs" / name).write_bytes(name.encode())
            result = self.build(base, text)
            self.assertEqual(result.returncode, 0, result.stderr)
            manifest = json.loads((base / "built/job.json").read_text())
            self.assertEqual([r["slot"] for r in manifest["references"]],
                             ["product", "camera", "person", "color_lock", "logo"])
            prompt = (base / "built/prompt.txt").read_text(encoding="utf-8")
            self.assertNotIn("{{", prompt)
            # Inspect role-specific content, not just the header's image numbering.
            camera = prompt.split("CAMERA: MATCH THE PRODUCT PERSPECTIVE REFERENCE")[1].split("PERSON AND PRODUCT INTERACTION")[0]
            person = prompt.split("PERSON AND PRODUCT INTERACTION")[1].split("SCENE AND LIGHT")[0]
            self.assertIn("Image 2", camera)
            self.assertIn("Image 3", person)
            preview = subprocess.run([
                sys.executable, "-S", str(SKILL / "scripts/generate.py"),
                "--job", str(base / "built/job.json"), "--output-dir", str(base / "preview"),
                "--usage-ledger", str(base / "usage.jsonl"),
            ], capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(preview.returncode, 0, preview.stderr)
            request = json.loads((base / "preview/request.json").read_text())
            self.assertEqual([Path(r["path"]).name for r in request["references"]], names)
            self.assertEqual(request["aspect_ratio"], "4:5")
            self.assertFalse(request["execute_requested"])
            self.assertFalse((base / "usage.jsonl").exists())

    def test_fixed_camera_recipe_cannot_override_a_view_reference(self):
        text = (SKILL / "examples/perspective-product/job.toml").read_text(encoding="utf-8")
        with tempfile.TemporaryDirectory() as folder:
            result = self.build(Path(folder), text.replace('module = "reference-perspective"',
                                                           'module = "three-quarter-studio"'))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("conflicting fixed camera angle", result.stderr)
            self.assertFalse((Path(folder) / "built/job.json").exists())

    def test_person_scene_rejects_exclusions_that_forbid_people(self):
        text = (SKILL / "examples/on-person/job.toml").read_text(encoding="utf-8")
        with tempfile.TemporaryDirectory() as folder:
            result = self.build(Path(folder), text.replace('module = "person-product"',
                                                           'module = "isolated-product"'))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("forbids people and hands", result.stderr)
            self.assertFalse((Path(folder) / "built/job.json").exists())

    def test_view_matching_requires_a_view_reference(self):
        text = (SKILL / "examples/perspective-product/job.toml").read_text(encoding="utf-8")
        with tempfile.TemporaryDirectory() as folder:
            result = self.build(Path(folder), text.replace('reference = "refs/perspective.jpg"', ''))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("requires reference", result.stderr)

    def test_generic_examples_build_without_person_reference_or_brand_assumptions(self):
        for example in ("perspective-product", "on-person"):
            text = (SKILL / "examples" / example / "job.toml").read_text(encoding="utf-8")
            text = text.replace('reference = "refs/person.jpg"', '')
            with self.subTest(example=example), tempfile.TemporaryDirectory() as folder:
                result = self.build(Path(folder), text)
                self.assertEqual(result.returncode, 0, result.stderr)
                prompt = (Path(folder) / "built/prompt.txt").read_text(encoding="utf-8")
                self.assertNotIn("{{", prompt)
                self.assertNotIn("Biohac", prompt)
                self.assertNotIn("eyeglasses", prompt)
                manifest = json.loads((Path(folder) / "built/job.json").read_text())
                self.assertNotIn("person", [r["slot"] for r in manifest["references"]])


if __name__ == "__main__":
    unittest.main()
