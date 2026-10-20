# Logos: SVG export and deterministic placement

Use `preserve` to retain an existing mark, or `replace` to ask the model to apply
supplied artwork. For faithful lettering, composite the artwork locally instead.

## Automatic SVG reference export

Install `requirements.txt`. The local renderer is `resvg-py`; no browser,
system Inkscape installation or cloud call is needed. In the job TOML:

```toml
[logo]
module = "preserve"  # or replace, with its placement fields
file = "logo.svg"
export_width = 1024
export_background = "#808080"  # useful for white artwork; default: white
```

`build_prompt.py job.toml --out out` exports to `out/references/logo.png` and
points the manifest at the PNG. A text-only build prints without rendering or
writing files. Rebuilding reuses an identical export but refuses to overwrite
a different one. Choose a new output directory when changing the logo.

Standalone transparent export:

```bash
python scripts/export_svg.py logo.svg logo.png --width 1024
```

Add `--background white` for an opaque reference. SVGs must be self-contained:
convert text to vector paths and remove external fonts, images and stylesheets.
This preserves lettering across machines. Originals are never overwritten.

## Scripted perspective placement

Start with an approved render whose target surface has no old logo. The script
does not erase old markings, find the surface automatically or simulate engraving.
Choose four pixel coordinates on the oriented base. List artwork corners in order:
**top-left, top-right, bottom-right, bottom-left**, even on a sloping surface.

Save `placement.toml` next to the files:

```toml
base = "approved-render.png"
logo = "logo.svg"  # exported transparently in memory; PNG also works
output = "branded.png"
quad = [[330, 214], [620, 176], [622, 218], [331, 256]]
blend = "normal"  # normal for opaque artwork; multiply for dark ink
opacity = 0.88
shadow_opacity = 0.15  # optional, default 0; printed ink often needs none
shadow_blur = 0.8
shadow_offset = [1, 2]
```

```bash
python scripts/composite_logo.py placement.toml
```

Paths are relative to the placement file. Coordinates refer to the base after
EXIF orientation is applied. Transparent artwork margins are cropped: the corners
bound visible artwork. The transform is a planar homography, so choose a locally
flat surface. It cannot wrap around a strongly curved arm or pass behind an
occluding part. Split or mask those cases in an image editor.

The output is lossless PNG with the base alpha channel and ICC profile retained.
Use artwork in a matching colour space (normally sRGB); automatic colour profile
conversion is not performed. Pixels outside the logo and optional shadow remain
unchanged in the oriented, decoded base. Resampling changes edge pixels as needed
for perspective. Inspect small lettering at full resolution before approval.

`branded.placement.json` records settings and input/output SHA-256 hashes.
Inputs and earlier outputs are never overwritten. Shadow is a simple drop shadow,
not a physical engraving or lighting reconstruction.

## Reproducible example

From the skill directory:

```bash
python examples/logo-placement/create_demo.py --out out/logo-demo
```

Open `out/logo-demo/comparison.png`. The example creates a synthetic slanted
surface and uses original vector artwork, with no private product references.

## Generative replacement

The `replace` module requires `surface`, `position`, `size`, `finish`, `color`
and `not_on`. Describe locations in camera terms, such as "camera-near temple
arm", and check that the camera shows it. If two or three authorized attempts
still alter lettering, use a clean surface and deterministic placement.

References: [resvg-py](https://resvg-py.readthedocs.io/en/stable/usage.html) and
[Pillow transforms](https://pillow.readthedocs.io/en/stable/reference/ImageTransform.html).
