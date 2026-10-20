# Agent skills

Skills for AI agents that read `SKILL.md` (Claude Code, Codex and others), taken from my day-to-day work building and running AI-managed online stores at [StoreKite](https://storekite.ai). Each one is something I actually use, cleaned of anything specific to my clients.

| Skill | What it does |
|---|---|
| [product-photo-studio](plugins/product-photo-studio/skills/product-photo-studio/SKILL.md) | Product images from a real product photo with Gemini on Vertex AI: an intake interview, a modular prompt builder with colour and logo locks, free request previews, local request limits and a review checklist. |

## Fotogen / Product Photo Studio

**Real product photos in. Packshots, product sets and images for your store out.**

Fotogen is the product-photo workflow I use for my own store, Biohac. The reusable
public skill is called `product-photo-studio`. Start with photos that show the
actual product, choose the image you need, then review the result against those
references before using it.

The skill works with different product categories. The glasses below are real
examples, not a restriction on what you can photograph.

**Give each reference a role:** a product photo defines what to preserve; a
perspective photo defines the product view to reproduce; an optional adult-person
reference defines the requested appearance/pose. An **in-hand perspective shot**
can establish the angle and foreshortening for an isolated render. It does not
ask the model to include the hand in the final image.

[Real examples](#real-examples-input--output) · [Available options](#available-options) · [Try it](#try-it) · [Install](#install) · [Video walkthrough](https://www.youtube.com/watch?v=lbtC4doWymo)

### Real examples: input → output

These are the actual Mentor and Eclipse assets used in my StoreKite video,
including the phone photos on cardboard. They come from the working Fotogen
workflow, before this public skill was packaged. They are not sample outputs
from the bundled `job.toml`, nor a promise that one call reproduces them exactly.

#### Mentor: phone photos → clean product image

**Input:** five views of the same tortoiseshell frame with orange lenses.
The side close-up supplies the logo and hinge detail; the other views show
the front, back, temples and lens tint.

| Front | Logo / hinge | Back | Side | Perspective reference (held) |
|---|---|---|---|---|
| <img src="docs/gallery/mentor/input-01.jpg" alt="Input: Mentor front view photographed on cardboard" width="180"> | <img src="docs/gallery/mentor/input-02.jpg" alt="Input: close-up of the Biohac logo and Mentor hinge" width="180"> | <img src="docs/gallery/mentor/input-03.jpg" alt="Input: Mentor rear view on cardboard" width="180"> | <img src="docs/gallery/mentor/input-04.jpg" alt="Input: Mentor temple and side profile on cardboard" width="180"> | <img src="docs/gallery/mentor/input-05.jpg" alt="Perspective reference: Mentor held at the desired product angle, not a request to include the hand" width="180"> |

**Output:** an isolated product image and, in a separate step, a set composition.
The set uses the product image plus an existing accessory visual, shown below.

| Product image | Product + accessories, separate step |
|---|---|
| <img src="docs/gallery/mentor/packshot.jpg" alt="Output: isolated Mentor product image on a light background" width="420"> | <img src="docs/gallery/mentor/set.jpg" alt="Output: Mentor set composition with bamboo case, cloth and pouch" width="420"> |

Example request to the agent:

> Use these photos of my Mentor glasses to make a clean catalog image. Keep the
> frame shape, tortoiseshell pattern, orange lens tint and Biohac marking. Show
> me the prompt and request preview first. Then prepare a separate set image
> using the supplied accessory visual.

#### Eclipse: a different frame, the same workflow

**Input:** five views of the round metal frame. These references establish a
different bridge, nose pads and thin temples; the agent should preserve those
details rather than reuse the Mentor shape.

| Perspective reference (held) | Front | Three-quarter | Side | Back |
|---|---|---|---|---|
| <img src="docs/gallery/eclipse/input-01.jpg" alt="Perspective reference: Eclipse held at the desired product angle, not a request to include the hand" width="180"> | <img src="docs/gallery/eclipse/input-02.jpg" alt="Input: round Eclipse frame from the front on cardboard" width="180"> | <img src="docs/gallery/eclipse/input-03.jpg" alt="Input: Eclipse bridge, nose pads and lenses at an angle" width="180"> | <img src="docs/gallery/eclipse/input-04.jpg" alt="Input: Eclipse thin metal temples from the side" width="180"> | <img src="docs/gallery/eclipse/input-05.jpg" alt="Input: Eclipse viewed from behind" width="180"> |

| Output: isolated product | Output: set with accessories, separate step |
|---|---|
| <img src="docs/gallery/eclipse/packshot.jpg" alt="Output: isolated Eclipse product image with round orange lenses" width="420"> | <img src="docs/gallery/eclipse/set.jpg" alt="Output: Eclipse with bamboo case, cloth and pouch" width="420"> |

#### Additional input for the sets: the accessory visual

Both set examples use this existing visual of the bamboo case, cloth and pouch
alongside the product image. It is an additional composition reference, not an
accessory pack inferred from the five photos of the glasses.

<img src="docs/gallery/accessories.jpg" alt="Additional supplied visual: bamboo case, cleaning cloth and drawstring pouch" width="600">

#### On-model imagery: an earlier portfolio example

<img src="docs/gallery/mentor/on-model.jpg" alt="Earlier portfolio result: an adult wearing Mentor glasses with orange lenses" width="360">

This existing Mentor image shows another use of the workflow. **It belongs to
an earlier photo series and was not generated from the five phone inputs above.**
Its original inputs are not included here. The public generator offers a
`person` mode for adult-person scenes; use an approved product reference and
check the fit, contact points, anatomy and product details in every result.

#### What to check before using the output

Compare the result with the original: frame silhouette, bridge, hinges, temple
thickness, lens colour and transparency, logo spelling and accessory count.
Prompt locks guide the model; they do not guarantee fidelity. A logo that looks
plausible at thumbnail size can still be wrong. For exact artwork on a flat
surface, use the [local logo placement workflow](#local-logo-placement-no-image-generation).

Gallery previews are resized, metadata-free copies with no cropping or
retouching. [Source notes and image hashes](docs/gallery/README.md) document the
examples. No new images were generated to build this gallery.

### Available options

| What you want | What you supply / choose | What is included today |
|---|---|---|
| Clean catalog image | Product reference, required details, angle | Product lock, white-background module, studio and eyewear camera modules; see both packshots above |
| Match a specific perspective | Product reference plus the view to reproduce, including a photo held in hand | `reference-perspective` camera module: product orientation, visible faces and foreshortening; no hand in the result unless requested |
| A different crop or format | Intended placement and aspect ratio | Square, portrait, landscape and wide output ratios; choose each request's format |
| Colour variant | The exact part and a colour sample or description | Translucent-tint and solid-finish prompt modules; review colour against the sample |
| Macro / construction detail | Product reference and the area to show | Macro camera module and generator `macro` mode; do not invent hidden construction |
| Product with accessories | Approved product image, accessory references and exact contents | Custom composition prompt; the set examples above are a separate workflow step, not an automatic bundle preset |
| Adult wearing / holding / using the product | Product reference, interaction, scale/fit and optional authorized adult reference | `product-use` person module, `person-context` camera and `person-product` exclusions; also available through direct generator `person` mode |
| Lifestyle or social image | Product, scene, light, composition and target format | `environment` background module or custom prompt; combine with a person when requested |
| Keep or replace a logo | Logo file, location, size, finish and colour | `preserve` / `replace` prompt modules; SVG reference export; local perspective placement on flat surfaces |

**Controls you can set:**

| Control | Choices |
|---|---|
| Generation model | `gemini-3.1-flash-image` or `gemini-3-pro-image` on Vertex AI |
| Output ratio | `1:1`, `2:3`, `3:2`, `3:4`, `4:3`, `4:5`, `5:4`, `9:16`, `16:9`, `21:9` |
| Resolution | `1K`, `2K`, `4K`; Flash also accepts `512`. Paid 4K requires explicit authorization and `--allow-4k` |
| Camera module | `reference-perspective`, `person-context`, `three-quarter-studio`, `eyewear-three-quarter-low`, `macro-detail` |
| Background module | `pure-white`, `environment` (scene and light from your brief) |
| Person module | `product-use`: adult subject, wearing/holding/using, scale/fit and optional appearance/pose reference |
| Colour module | `translucent-tint`, `solid-finish`, or skip the section |
| Logo module | `preserve`, `replace`, or skip the section; a local compositor is also included |
| Direct generator mode | `product`, `person`, `macro`, `none`; built jobs use `none` because their prompts already contain the locks |
| References | The job builder has product, perspective, person, colour-sample and logo slots; direct generation also accepts repeated `--reference` |
| Attempts | One `--execute` makes one paid attempt; the agent can plan more within your approved budget |

See the [module guide](plugins/product-photo-studio/skills/product-photo-studio/references/prompt-modules.md)
for the exact fields, and the [perspective/person guide](plugins/product-photo-studio/skills/product-photo-studio/references/perspective-and-person.md)
for reference roles and natural product interaction. Set compositions remain
custom instructions; the repository does not include a preset for the accessory
sets shown above. Marketplace
or ad-catalog acceptance needs its own check before publication.

### Try it

After [installing the skill](#install), give the agent your references and a concrete request:

> Use product-photo-studio to make a square product image from my photos. Keep
> the product geometry and branding. Ask about any missing colour or logo
> decisions, then show the prompt and a free request preview before generating.

For a different use, change the requested result:

- **Detail:** “Show a close-up of this hinge. Keep the construction and logo exactly as in the reference.”
- **Perspective:** “Use this product photo for construction and the photo held in my hand for the final view. Match that angle and foreshortening on white, without the hand.”
- **On a person:** “Show an adult wearing this shoulder bag, 4:5. Preserve its construction and size; keep the strap resting naturally on the shoulder.”
- **Set:** “Use this approved product image and these accessory references for a set image. Include exactly the listed items.”
- **Wide image:** “Place this product in a 21:9 composition with empty space above it. I will add the headline afterwards.”

The agent clarifies the product, references, output, logo and budget, then chooses
the included modules or writes a custom prompt. Setup and paid generation require
your own Vertex AI project. A **free preview is a JSON request, not a free image**.

To inspect a request using the included gallery, run this from the repository
root. It needs Python 3.11+ but no credentials or image-generation dependencies:

```bash
python plugins/product-photo-studio/skills/product-photo-studio/scripts/generate.py --mode product --prompt "Clean studio packshot on white. Preserve the round metal frame and orange lens tint. Use the first image for the front and the second for the side construction." --reference docs/gallery/eclipse/input-02.jpg --reference docs/gallery/eclipse/input-04.jpg --aspect-ratio 1:1 --image-size 2K --output-dir out/eclipse-preview
```

Open `out/eclipse-preview/request.json` to see the prompt, ordered references,
model, output estimate and request limits. This command does not generate an image.
Use your own product references for commercial work.

## Install

**Claude Code**

```
/plugin marketplace add Bubiec/agent-skills
/plugin install product-photo-studio@bubiec
```

**Codex**: copy `plugins/product-photo-studio/skills/product-photo-studio` into `~/.codex/skills/`.

**Any other agent**: copy the skill folder into your project and add one line to your `AGENTS.md` (or equivalent) pointing product-image tasks at its `SKILL.md`.

## product-photo-studio in one minute

```
intake questions → job.toml → build_prompt.py → prompt.txt → generate.py (preview, free) → generate.py --execute (paid) → review
```

- **The agent interviews you first**: product, reference photo, which colour must be exact, logo or no logo, budget, rights. Existing answers are reused; missing product and budget decisions are clarified.
- **Prompts are assembled from modules**, one per concern: product lock, camera, background, colour lock, logo, exclusions. One value lives in one place, so two runs never contradict each other. Reference images are numbered automatically ("Image 2 is the colour sample").
- **Logos get their own module**: keep or replace a mark, automatically export SVG references to PNG, or apply the artwork locally with a four-corner perspective transform, opacity, multiply blending and optional shadow.
- **Money is guarded in layers**: preview by default, `--execute` for every paid call, local daily and monthly request limits, an extra flag for 4K, and a setup guide for a dedicated project with quotas.

See [examples/orange-lens-eyewear](plugins/product-photo-studio/skills/product-photo-studio/examples/orange-lens-eyewear) for a full job file and the prompt it produces.

Two generic starting jobs are also included, each with its built prompt:
[perspective-product](plugins/product-photo-studio/skills/product-photo-studio/examples/perspective-product)
(a mug, using a separate view reference) and
[on-person](plugins/product-photo-studio/skills/product-photo-studio/examples/on-person)
(a shoulder bag worn by an adult). Supply your own references and replace the
illustrative product facts with your brief. Both can be built with `build_prompt.py`.

### Local logo placement, no image generation

```bash
cd plugins/product-photo-studio/skills/product-photo-studio
python -m pip install -r requirements.txt
python examples/logo-placement/create_demo.py --out out/logo-demo
```

The demo builds a synthetic surface and places the included vector mark. For your
own render, specify four surface corners in `placement.toml`, then run
`python scripts/composite_logo.py placement.toml`. SVG rendering and compositing
run locally without credentials or paid API calls. See the [logo guide](plugins/product-photo-studio/skills/product-photo-studio/references/logo.md).

![Synthetic surface before and after perspective logo placement](plugins/product-photo-studio/skills/product-photo-studio/examples/logo-placement/comparison.png)

## Security

Local counters are not a billing cap. They apply only to processes sharing the same ledger; other machines and tools are outside their scope. SDK retries are disabled and failed attempts still count.

No credentials live in this repository or in any job file. Image generation authenticates with Google Application Default Credentials on your machine. Every push is scanned for secrets.

## License

- Code (`*.py`, workflows): [MIT](LICENSE).
- Prompts, modules, documentation and code examples: [CC BY 4.0](LICENSE-CONTENT.md). Use them, change them, sell what you make with them; credit "Szymon Bubała, github.com/Bubiec/agent-skills".
- The Biohac product photos, result images and branding in `docs/gallery/` are demonstration assets, excluded from that content license. See [gallery usage notes](docs/gallery/README.md#usage).

## About

I'm Szymon Bubała. I build and run AI-managed e-commerce stores myself, a few stores a year: [storekite.ai](https://storekite.ai). If you want this kind of setup working in your own store rather than assembling it yourself, that's what I do.

## Local checks

Requires Python 3.11 or newer. Request previews use only the standard library;
SVG and compositing tests require Pillow and resvg-py. Install the skill requirements
for the full workflow (including paid generation).

```bash
python -m pip install -r plugins/product-photo-studio/skills/product-photo-studio/requirements.txt
python -m unittest discover -s tests -v
claude plugin validate .
gitleaks dir . --redact --no-banner
```

The bundled `orange-lens-eyewear` job contains no product, colour or logo reference images. Supply
your own files in its ignored `refs/` folder. The logo demo contains only original
synthetic artwork. A preview means inspecting a JSON request, not generating a free
image. Keep each generation in a new output directory so earlier requests and
images remain reviewable.
