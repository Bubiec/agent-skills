---
name: product-photo-studio
description: Create product packshots, perspective-matched renders, colour variants, macro details and on-person images from reference photos using Gemini on Vertex AI. Use for product image generation or product logo placement, with modular prompts, request previews and local usage limits.
---

# Product Photo Studio

The supplied product photo is the source of truth. The model may change the scene, light and camera; it must not redesign the product. Prefer deterministic editing (crop, composite, masked recolour) whenever it can do the job, and use generation only for a genuinely new angle, scene, person or macro.

Separate reference roles: the product image establishes identity and construction;
a perspective image establishes the desired product view; an optional adult-person
image establishes the requested appearance/pose. A photo of a product held in a
hand can be a perspective reference without requesting a hand in the output.
Do not default to an eyewear-specific camera module for other products.

## Workflow

### 1. Interview first

Use [references/intake.md](references/intake.md) to identify missing information. Reuse answers already supplied and ask the remaining material questions together. Do not guess answers that change the product, the colour, the logo or the cost. You can build a text prompt before references arrive, but generation needs the actual files.

### 2. Write the job file

Choose a starting example and copy its `job.toml` next to the user's images:
`examples/perspective-product/` for matching a product view (including a hand-held
reference), `examples/on-person/` for wearing/holding/using a product, or
`examples/orange-lens-eyewear/` for that specific shot. Each section picks one
module from `assets/modules/<section>/`; set `module = "none"` to skip a section.
Read [references/prompt-modules.md](references/prompt-modules.md) when adding a module.

For view matching and person scenes, read [references/perspective-and-person.md](references/perspective-and-person.md).
Reuse supplied decisions and authorization; example products, dimensions and poses
are illustrative and must be replaced with the user's product facts.

### 3. Build the prompt

```bash
python scripts/build_prompt.py path/to/job.toml --out path/to/out
```

The builder numbers the reference images in the order they will be sent, fills every placeholder and stops on any missing value. Show the user the finished `prompt.txt` before going further.

### 4. Preview (free)

```bash
python scripts/generate.py --job path/to/out/job.json --output-dir path/to/out
```

This writes `request.json` and spends nothing. Report to the user: model, resolution, aspect ratio, reference images in order, the estimated output price, and today's/this month's request count against the limits.

### 5. Generate (paid, within the user's authorization)

```bash
python scripts/generate.py --job path/to/out/job.json --output-dir path/to/out --execute
```

One `--execute` reserves one paid attempt, including failed or blocked responses. SDK retries are disabled. If the user has already approved a model, resolution and number of attempts, proceed within that scope; otherwise show the concrete preview and obtain approval first. Use 2K Flash for drafts; choose Pro when the job warrants it. Live 4K needs `--allow-4k` and authorization covering 4K. Never raise request limits yourself. These are local request limits, not a cloud spending cap. First-time setup: [references/vertex-setup.md](references/vertex-setup.md).

### 6. Review

Check every result at full resolution with [references/qa.md](references/qa.md). Treat every output as a draft until the user approves it. When something is wrong, change one module at a time and note what changed, so the next run can be compared with the last one.

## Logos

Read [references/logo.md](references/logo.md) for SVG export and logo placement.
The builder automatically exports SVG logo references to PNG when `--out` is set.
For a clean approved render, prefer `scripts/composite_logo.py placement.toml` to
apply exact artwork with perspective, opacity and optional shadow. Ask for missing
surface coordinates rather than inventing a location. This local path needs no
Vertex account or generation budget. It supports flat surfaces, not automatic
curvature or occlusion reconstruction.

## Rules

- Use only product photos, logos and people the user owns or has permission to use. Do not imply endorsement by a real person.
- Images show what a product looks like; they do not prove what it does. Never write performance, medical or certification claims from a generated image.
- Keep originals untouched. Name outputs with product, variant, role and revision, for example `frame-a_orange_catalog_r3.png`.
- Never put credentials, tokens or keys in prompts, job files or output folders. Authentication is Application Default Credentials only.
