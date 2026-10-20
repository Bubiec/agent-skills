"""Real raster exports and projective transforms, without cloud calls."""
from io import BytesIO
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from PIL import Image, ImageChops

SKILL = Path(__file__).resolve().parents[1] / "plugins/product-photo-studio/skills/product-photo-studio"
sys.path.insert(0, str(SKILL / "scripts"))
from export_svg import svg_png_bytes, export_svg
from composite_logo import composite, perspective_coefficients

SVG = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 50"><path fill="#e22" d="M0 0H100V50H0Z"/></svg>'


class LogoTests(unittest.TestCase):
    def test_svg_transparency_background_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as folder:
            source, output = Path(folder)/"logo.svg", Path(folder)/"logo.png"
            source.write_text(SVG.replace('M0 0H100V50H0Z', 'M10 10H90V40H10Z'), encoding="utf-8")
            export_svg(source, output, width=200)
            with Image.open(output) as result:
                self.assertEqual(result.size, (200, 100))
                self.assertEqual(result.convert("RGBA").getpixel((0, 0))[3], 0)
            white = Image.open(BytesIO(svg_png_bytes(source, 200, "white")))
            self.assertEqual(white.convert("RGBA").getpixel((0, 0)), (255, 255, 255, 255))
            with self.assertRaisesRegex(ValueError, "new file"):
                export_svg(source, output)

    def test_svg_rejects_external_resources_and_unoutlined_text(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder)/"logo.svg"
            for extra in ('<image href="https://example.com/private.png"/>', '<text>BRAND</text>'):
                source.write_text(SVG.replace('</svg>', extra + '</svg>'), encoding="utf-8")
                with self.assertRaises(ValueError):
                    svg_png_bytes(source)

    def test_homography_maps_all_corners(self):
        quad = [(20, 30), (180, 10), (160, 90), (30, 80)]
        a,b,c,d,e,f,g,h = perspective_coefficients(quad, (100, 50))
        for (x,y), (u,v) in zip(quad, [(0,0), (100,0), (100,50), (0,50)]):
            self.assertAlmostEqual((a*x+b*y+c)/(g*x+h*y+1), u)
            self.assertAlmostEqual((d*x+e*y+f)/(g*x+h*y+1), v)

    def test_warp_preserves_outside_pixels_alpha_and_orientation(self):
        base = Image.new("RGBA", (220, 120), (120, 140, 160, 180))
        logo = Image.new("RGBA", (100, 50), "red")
        logo.paste("blue", (50, 0, 100, 50))
        result = composite(base, logo, [(20,30), (180,10), (160,90), (30,80)])
        self.assertEqual(result.getpixel((0,0)), base.getpixel((0,0)))
        self.assertIsNone(ImageChops.difference(result.getchannel("A"), base.getchannel("A")).getbbox())
        self.assertGreater(result.getpixel((50,45))[0], result.getpixel((50,45))[2])
        self.assertGreater(result.getpixel((140,45))[2], result.getpixel((140,45))[0])
        difference = ImageChops.difference(base.convert("RGB"), result.convert("RGB"))
        x0,y0,x1,y1 = difference.getbbox()
        self.assertTrue(19 <= x0 < x1 <= 181 and 9 <= y0 < y1 <= 91)

    def test_multiply_opacity_shadow_and_invalid_quad(self):
        base = Image.new("RGBA", (100,100), (200,200,200,255))
        logo = Image.new("RGBA", (10,10), (128,128,128,255))
        quad = [(20,20), (60,20), (60,60), (20,60)]
        result = composite(base, logo, quad, blend="multiply", opacity=0.5,
                           shadow_opacity=0.2, shadow_offset=(5,5))
        self.assertLess(result.getpixel((40,40))[0], 200)
        self.assertLess(result.getpixel((62,40))[0], 200)
        self.assertEqual(result.getpixel((0,0)), base.getpixel((0,0)))
        self.assertIsNone(ImageChops.difference(base, composite(base, logo, quad, opacity=0)).getbbox())
        for invalid in ([(0,0)]*4, [(20,20), (20,60), (60,60), (60,20)]):
            with self.assertRaises(ValueError):
                composite(base, logo, invalid)

    def test_builder_exports_svg_and_cli_composites_with_provenance(self):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            (base/"logo.svg").write_text(SVG, encoding="utf-8")
            Image.new("RGB", (220,120), "white").save(base/"base.png")
            (base/"job.toml").write_text('''[product]
noun="mug"
reference="base.png"
details="handle"
[logo]
module="preserve"
file="logo.svg"
''', encoding="utf-8")
            command = [sys.executable, str(SKILL/"scripts/build_prompt.py"), "job.toml", "--out", "out"]
            for _ in range(2):
                result = subprocess.run(command, capture_output=True, cwd=base)
                self.assertEqual(result.returncode, 0, result.stderr)
            manifest = json.loads((base/"out/job.json").read_text())
            self.assertTrue(Path(manifest["references"][1]["path"]).is_file())
            self.assertTrue(Path(manifest["references"][1]["path"]).is_absolute())
            self.assertEqual(Path(manifest["references"][1]["path"]).suffix, ".png")
            (base/"placement.toml").write_text('''base="base.png"
logo="logo.svg"
output="branded.png"
quad=[[20,30],[180,10],[160,90],[30,80]]
blend="multiply"
''', encoding="utf-8")
            command = [sys.executable, str(SKILL/"scripts/composite_logo.py"), str(base/"placement.toml")]
            result = subprocess.run(command, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((base/"branded.placement.json").is_file())
            self.assertNotEqual(subprocess.run(command, capture_output=True).returncode, 0)


if __name__ == "__main__":
    unittest.main()
