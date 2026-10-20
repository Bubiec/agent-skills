#!/usr/bin/env python3
"""Rasterize self-contained SVG artwork locally, without a browser or cloud API."""
import argparse
from io import BytesIO
import math
from pathlib import Path
import re
import xml.etree.ElementTree as ET


def svg_png_bytes(source: Path, width: int = 1024, background: str | None = None) -> bytes:
    if not 16 <= width <= 8192:
        raise ValueError("SVG width must be between 16 and 8192 pixels")
    markup = source.read_text(encoding="utf-8-sig")
    if "<!DOCTYPE" in markup.upper() or "<!ENTITY" in markup.upper():
        raise ValueError("Use a self-contained SVG without document types or entities")
    root = ET.fromstring(markup)
    if root.tag.split("}")[-1] != "svg":
        raise ValueError("Expected an SVG root element")
    if root.get("viewBox"):
        view_box = [float(value) for value in re.split(r"[\s,]+", root.get("viewBox").strip())]
        if len(view_box) != 4 or any(not math.isfinite(value) for value in view_box) or min(view_box[2:]) <= 0:
            raise ValueError("Invalid SVG viewBox")
        if width * view_box[3] / view_box[2] > 8192:
            raise ValueError("SVG is too tall; use a smaller width")
    for element in root.iter():
        if element.tag.split("}")[-1] == "text":
            raise ValueError("Convert logo text to vector paths before export for reproducible lettering")
        for key, value in element.attrib.items():
            if key.split("}")[-1] == "href" and not value.startswith("#"):
                raise ValueError("Linked resources are unsupported; embed artwork as vector paths")
    urls = re.findall(r"url\((.*?)\)", markup, re.I)
    if "@import" in markup.lower() or any(not url.strip(" \t\r\n'\"").startswith("#") for url in urls):
        raise ValueError("External CSS/resources are unsupported")
    try:
        import resvg_py
        from PIL import Image
    except ImportError as exc:
        raise RuntimeError("Install the skill requirements (resvg-py and Pillow)") from exc
    data = resvg_py.svg_to_bytes(svg_string=markup, width=width, background=background,
                                 skip_system_fonts=True)
    with Image.open(BytesIO(data)) as image:
        if image.height > 8192:
            raise ValueError("SVG is too tall; use a smaller width")
        if not image.convert("RGBA").getchannel("A").getbbox():
            raise ValueError("SVG rendered empty; convert logo text to paths first")
    return data


def export_svg(source: Path, output: Path, width: int = 1024, background: str | None = None,
               reuse_identical: bool = False) -> Path:
    if source.resolve() == output.resolve():
        raise ValueError(f"Output must be a new file: {output}")
    data = svg_png_bytes(source, width, background)
    if output.exists():
        if reuse_identical and output.read_bytes() == data:
            return output
        raise ValueError(f"Output must be a new file: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("xb") as handle:
        handle.write(data)
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--width", type=int, default=1024)
    parser.add_argument("--background", help="CSS colour; omitted means transparent")
    args = parser.parse_args()
    try:
        print(export_svg(args.source, args.output, args.width, args.background))
    except (ValueError, RuntimeError, ET.ParseError) as exc:
        parser.exit(2, f"{exc}\n")


if __name__ == "__main__":
    main()
