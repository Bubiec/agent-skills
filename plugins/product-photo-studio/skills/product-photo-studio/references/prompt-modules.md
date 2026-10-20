# Prompt modules

A prompt is assembled from one module per section, in this order:

| Section | What it controls | Modules |
|---|---|---|
| `product` | what to copy and what must not change | `product-lock` (default) |
| `camera` | angle, perspective reference, framing, focus | `reference-perspective`, `person-context`, `eyewear-three-quarter-low`, `three-quarter-studio`, `macro-detail` |
| `person` | adult subject, wearing/holding/using, scale and fit | `product-use` |
| `background` | background and light | `pure-white`, `environment` |
| `color_lock` | exact colour of one part | `translucent-tint`, `solid-finish` |
| `logo` | logo handling | `preserve`, `replace` |
| `exclusions` | what must not appear | `isolated-product`, `person-product` |

Modules are plain text files in `assets/modules/<section>/<name>.md`. The builder replaces placeholders from the job file and fails on any it cannot fill.

## Template syntax

| Syntax | Result |
|---|---|
| `{{section.key}}` | the value from the job file |
| `{{section.key\|upper}}` | upper-cased value (for headings) |
| `{{section.key\|or}}` | a list as "a, b or c" (`\|and` gives "a, b and c") |
| `{{ref.product}}`, `{{ref.camera}}`, `{{ref.person}}`, `{{ref.color_lock}}`, `{{ref.logo}}` | "Image N", numbered in the order the images are sent; omitted slots do not consume a number |
| `[[if section.key]]text` | the line is kept only when that key is set |

## Writing a new module

- **One authority per value.** The canvas, the camera, the product scale and the colour each appear in exactly one module. Contradictions between modules (a 1:1 canvas in one, 16:9 in another) are the most common reason two "identical" runs disagree.
- **State the left/right convention.** Camera modules say whether left and right are the viewer's or the wearer's. Without that, "the right lens is closest to the camera" can mean two opposite poses.
- **Describe in camera terms.** "The camera-near temple arm" survives any product; "the left temple arm" does not.
- **Say what to do before what to avoid.** Models follow positive descriptions better than long negative lists. Keep exclusions short and specific to failures you have actually seen.
- **Name near-miss colours.** For a colour lock, the useful negatives are the neighbours the model drifts to (orange drifts to amber, coral and red), not every colour there is.
- **Do not put headline text in the prompt.** If the image needs typography, add it afterwards in an editor.
