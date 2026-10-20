# Intake questions

Ask these in one message, grouped, with the default in brackets so the user can answer "defaults" for anything they do not care about. Write every answer into the job file. Do not generate until the blockers (marked ●) are answered.

## Product
1. ● What is the product, in plain words? ("a pair of glasses", "a ceramic mug"). This goes into the prompt as the product noun.
2. ● Where is the product reference photo? It should be sharp, evenly lit, the whole product in frame, ideally on a plain background. One clean photo beats five mediocre ones.
3. Which details must survive exactly? (hinges, stitching, buttons, engraving...). These go into `product.details`.
4. Which materials should read clearly in the reflections? [taken from the photo]

## Image
5. What is the image for? [catalog main image on white]. Other options: colour variant, macro detail, lifestyle scene, social post.
6. Aspect ratio and resolution? [1:1, 2K]
7. Which camera angle? [the closest existing camera module]. If the user has a reference image with the angle they want, ask for it.
8. Where will it be published? Marketplaces and ad catalogs have their own main-image rules (white background, no text, no badges); check them before choosing the composition.

If a supplied photo is meant to define the product's final perspective, record it
as `camera.reference` with `camera.module = "reference-perspective"`. A product
held in a hand may be such a view reference: match the product's angle and
foreshortening, keeping the hand only if requested in the output. Establish its
role from the brief; clarify when the intended result is ambiguous.

For a person scene, establish adult subject, wearing/holding/using interaction,
crop, setting and physical scale/fit. Ask for known dimensions if required for a
credible result, and an authorized appearance/pose reference only when needed.
Record these in `[person]`; choose the camera for the brief, not the product
category of the bundled example. See [perspective-and-person.md](perspective-and-person.md).

## Colour lock (skip if the colour is already correct in the photo)
9. Which part must have an exact colour? (lenses, fabric, glaze...)
10. Is there a colour sample image? Without one, describe the colour in words and list the near-miss colours to avoid.
11. Is the part translucent or solid? This picks `translucent-tint` or `solid-finish`.

## Logo
12. ● Does the image need a logo? [no change: keep what is on the product]
    - keep it as it is on the photo → `preserve` (a high-resolution logo file still helps)
    - put a different or cleaner logo on the product → `replace`
13. If yes: where on the product, how big, which finish (print, engraving, embossing, label) and which colour?
14. Is the logo file SVG? The builder exports it automatically with `--out` (see `logo.md`). For local placement, ask for the clean base image and four target corners; SVG can be used directly.

## Budget and account
15. ● Is a Google Cloud project with Vertex AI and billing ready? If not, walk through `vertex-setup.md` first.
16. How many paid attempts are acceptable for this job? [3 at 2K on Flash, then Pro for the final]
17. Should the daily and monthly request limits stay at the defaults? [yes: 10 per day, 50 per month]

## Rights
18. ● Does the user own, or have permission to use, the product photos, the logo and any person shown?
