#!/usr/bin/env python3
"""Create an original synthetic surface and composite the included vector mark."""
import argparse
from pathlib import Path
import subprocess
import sys
from PIL import Image, ImageDraw

EXAMPLE = Path(__file__).resolve().parent
SCRIPTS = EXAMPLE.parents[1] / "scripts"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True, help="New output directory")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    base = Image.new("RGB", (1000, 440), "#f3f4f6")
    draw = ImageDraw.Draw(base)
    draw.polygon([(80,230), (810,135), (822,220), (84,315)], fill="#303740")
    draw.line([(80,230), (810,135), (822,220)], fill="#657080", width=4)
    draw.line([(84,315), (822,220)], fill="#151b23", width=5)
    base.save(args.out / "base.png")
    (args.out / "logo.svg").write_bytes((EXAMPLE / "demo-logo.svg").read_bytes())
    placement = '''base = "base.png"
logo = "logo.svg"
output = "branded.png"
# Artwork corners: top-left, top-right, bottom-right, bottom-left.
quad = [[330, 214], [620, 176], [622, 218], [331, 256]]
blend = "normal"
opacity = 0.88
shadow_opacity = 0.3
shadow_blur = 0.8
shadow_offset = [1, 2]
'''
    (args.out / "placement.toml").write_text(placement, encoding="utf-8")
    subprocess.run([sys.executable, str(SCRIPTS / "composite_logo.py"), str(args.out / "placement.toml")], check=True)
    comparison = Image.new("RGB", (1000, 880), "white")
    comparison.paste(base, (0,0))
    with Image.open(args.out / "branded.png") as branded:
        comparison.paste(branded.convert("RGB"), (0,440))
    draw = ImageDraw.Draw(comparison)
    draw.text((35,35), "BEFORE: synthetic flat surface", fill="black", font_size=24)
    draw.text((35,475), "AFTER: SVG logo + perspective + shadow", fill="black", font_size=24)
    comparison.save(args.out / "comparison.png")


if __name__ == "__main__":
    main()
