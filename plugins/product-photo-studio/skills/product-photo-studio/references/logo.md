# Logos on generated products

Image models treat a logo as a texture they are free to "improve". Letters drift, symbols get simplified, and a logo can end up mirrored or on the wrong part. Three things reduce that.

## 1. Give the model a clean PNG, not the SVG

Gemini image models accept PNG, JPEG and WEBP; SVG is rejected. Export the vector at a generous size, crop it tight with a small margin, and flatten it onto a plain background that contrasts with the mark (white for a dark logo, mid grey for a white one). A transparent PNG can arrive as black-on-black.

```bash
# Inkscape
inkscape logo.svg --export-type=png --export-width=1024 --export-background=white --export-filename=logo.png
# or resvg
resvg --width 1024 --background white logo.svg logo.png
```

Use the exact logo colour if the print should match it; otherwise export it in the colour it will have on the product.

## 2. Say where, how big and how it is made

The `replace` module needs:

| Key | Example |
|---|---|
| `surface` | the outer side of the camera-near temple arm |
| `position` | starting about 15 mm behind the hinge, centred on the height of the arm |
| `size` | about 12–15% of the visible length of the arm |
| `finish` | a crisp, slightly glossy pad print / a shallow laser engraving / a blind emboss |
| `color` | exactly the colour of the supplied artwork |
| `not_on` | parts where the model tends to put a second copy |

Describe the surface in camera terms ("camera-near", "on the right side of the image"), not wearer or product terms. The camera module must actually show that surface; if it faces away from the camera, no prompt will save the logo.

`replace` also removes the old marking from that surface. If the reference photo shows the old logo large and sharp, the model may blend the two; a reference with a plain surface works better.

## 3. When it still fails: composite instead of generating

If two or three attempts still change the letterforms, stop spending on retries:

1. Generate the image with `[logo] module = "none"` and a reference whose logo surface is plain (or add "the outer side of the temple arm is plain, with no markings" to `camera.pose_notes`).
2. Place the PNG logo on the approved render in an image editor: perspective transform onto the surface, match the curvature, multiply or overlay blend for prints, a slight inner shadow for engravings.

A composited logo is pixel-exact and reusable across a whole image series, which is usually what a brand needs.
