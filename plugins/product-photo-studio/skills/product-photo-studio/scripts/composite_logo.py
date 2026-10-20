#!/usr/bin/env python3
"""Project logo artwork onto a user-specified planar quadrilateral. No generation."""
import argparse
import hashlib
from io import BytesIO
import json
import math
from pathlib import Path
import tomllib

from PIL import Image, ImageChops, ImageFilter, ImageOps
from export_svg import svg_png_bytes


def perspective_coefficients(quad, size):
    """Solve the inverse homography required by Pillow (output -> artwork)."""
    width, height = size
    source = [(0, 0), (width, 0), (width, height), (0, height)]
    rows = []
    for (x, y), (u, v) in zip(quad, source):
        rows += [[x, y, 1, 0, 0, 0, -u*x, -u*y, u],
                 [0, 0, 0, x, y, 1, -v*x, -v*y, v]]
    for col in range(8):
        pivot = max(range(col, 8), key=lambda row: abs(rows[row][col]))
        rows[col], rows[pivot] = rows[pivot], rows[col]
        divisor = rows[col][col]
        if abs(divisor) < 1e-10:
            raise ValueError("Degenerate quadrilateral")
        rows[col] = [value / divisor for value in rows[col]]
        for row in range(8):
            if row != col:
                factor = rows[row][col]
                rows[row] = [a - factor*b for a, b in zip(rows[row], rows[col])]
    return tuple(row[8] for row in rows)


def validate_quad(quad, size):
    if len(quad) != 4 or any(len(point) != 2 for point in quad):
        raise ValueError("quad needs four [x,y] points: top-left, top-right, bottom-right, bottom-left")
    if any(not math.isfinite(value) for point in quad for value in point):
        raise ValueError("Coordinates must be finite")
    if any(not (0 <= x <= size[0] and 0 <= y <= size[1]) for x, y in quad):
        raise ValueError("All corners must be inside the EXIF-oriented base image")
    crosses = []
    for i in range(4):
        a, b, c = quad[i], quad[(i+1) % 4], quad[(i+2) % 4]
        crosses.append((b[0]-a[0])*(c[1]-b[1]) - (b[1]-a[1])*(c[0]-b[0]))
    if not all(value > 1e-6 for value in crosses):
        raise ValueError("Use a convex, non-mirrored quad in top-left, top-right, bottom-right, bottom-left order")


def composite(base, artwork, quad, opacity=1.0, blend="normal", shadow_opacity=0.0,
              shadow_blur=1.0, shadow_offset=(1.0, 1.0)):
    base = base.convert("RGBA")
    validate_quad(quad, base.size)
    if blend not in {"normal", "multiply"}:
        raise ValueError("blend must be normal or multiply")
    if not 0 <= opacity <= 1 or not 0 <= shadow_opacity <= 1:
        raise ValueError("Opacity values must be between 0 and 1")
    if not math.isfinite(shadow_blur) or not 0 <= shadow_blur <= 64:
        raise ValueError("shadow_blur must be between 0 and 64 pixels")
    if len(shadow_offset) != 2 or any(not math.isfinite(x) or abs(x) > 256 for x in shadow_offset):
        raise ValueError("shadow_offset needs two finite values within +/-256 pixels")
    art = artwork.convert("RGBA")
    bbox = art.getchannel("A").getbbox()
    if not bbox:
        raise ValueError("Logo artwork is empty")
    art = art.crop(bbox)
    # Premultiplied alpha avoids dark fringes on rotated or translucent edges.
    warped = art.convert("RGBa").transform(base.size, Image.Transform.PERSPECTIVE,
        perspective_coefficients(quad, art.size), Image.Resampling.BICUBIC).convert("RGBA")
    mask = warped.getchannel("A").point(lambda a: round(a * opacity))
    original_alpha = base.getchannel("A")
    rgb = base.convert("RGB")
    if shadow_opacity:
        shadow = mask.transform(base.size, Image.Transform.AFFINE,
            (1, 0, -shadow_offset[0], 0, 1, -shadow_offset[1]), Image.Resampling.BICUBIC)
        shadow = shadow.filter(ImageFilter.GaussianBlur(shadow_blur))
        shadow = ImageChops.multiply(shadow.point(lambda a: round(a * shadow_opacity)), original_alpha)
        rgb = Image.composite(Image.new("RGB", base.size, "black"), rgb, shadow)
    target = warped.convert("RGB")
    if blend == "multiply":
        target = ImageChops.multiply(rgb, target)
    result = Image.composite(target, rgb, ImageChops.multiply(mask, original_alpha))
    result.putalpha(original_alpha)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("job", type=Path, help="Placement TOML; paths relative to this file")
    args = parser.parse_args()
    with args.job.open("rb") as handle:
        job = tomllib.load(handle)
    base_dir = args.job.resolve().parent
    base_path, logo_path, output = [(base_dir / job[key]).resolve() for key in ("base", "logo", "output")]
    report = output.with_suffix(".placement.json")
    if output.suffix.lower() != ".png":
        parser.error("Output must be lossless PNG")
    if output in {base_path, logo_path} or output.exists() or report.exists():
        parser.error("Choose a new output path; inputs and earlier outputs are never overwritten")
    try:
        if logo_path.suffix.lower() == ".svg":
            artwork = Image.open(BytesIO(svg_png_bytes(logo_path, job.get("svg_width", 1024))))
        else:
            artwork = Image.open(logo_path)
        with Image.open(base_path) as raw, artwork:
            base = ImageOps.exif_transpose(raw)
            result = composite(base, artwork, job["quad"], **{key: job[key] for key in
                ("opacity", "blend", "shadow_opacity", "shadow_blur", "shadow_offset") if key in job})
            output.parent.mkdir(parents=True, exist_ok=True)
            with output.open("xb") as handle:
                result.save(handle, format="PNG", icc_profile=raw.info.get("icc_profile"))
        record = {"settings": job, "inputs": {str(path): hashlib.sha256(path.read_bytes()).hexdigest()
                  for path in (base_path, logo_path)}, "output_sha256": hashlib.sha256(output.read_bytes()).hexdigest()}
        with report.open("x", encoding="utf-8") as handle:
            json.dump(record, handle, indent=2)
        print(output)
    except (ValueError, RuntimeError) as exc:
        parser.exit(2, f"{exc}\n")


if __name__ == "__main__":
    main()
