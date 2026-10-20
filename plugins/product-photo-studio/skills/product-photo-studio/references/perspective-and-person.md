# Perspective and person scenes

These are independent controls, usable with different product categories. A cup,
shoe, bag, watch or item of clothing is not an eyewear job. Choose the interaction
and target view from the brief, not from the demonstration gallery.

## Assign reference roles before writing the prompt

| Job field | What it supplies | What it does not decide |
|---|---|---|
| `product.reference` | Product identity, construction, markings, materials | Final camera viewpoint when another view is requested |
| `camera.reference` | Desired product orientation relative to the camera, visible faces and foreshortening | Product identity, background, presence of a hand or person |
| `person.reference` (optional) | Authorized adult appearance and pose requested in the brief | Product identity or replacement branding |

The builder numbers these roles automatically before colour and logo references.
The same file can serve two roles when appropriate; keep both roles explicit.
For multiple construction views beyond the builder's product slot, the direct
generator accepts repeated `--reference` arguments with roles described in the prompt.

## Match a product view

Set `[camera] module = "reference-perspective"`, `reference` and `framing`.
Describe only additional requested composition constraints in `pose_notes`.
Do not combine the reference with a conflicting fixed 30-degree or 85 mm camera
recipe: matching its visible faces and foreshortening is the point of this mode.

A photo taken while holding the object is often the clearest way to specify
that view. Transfer the object's tilt, roll and orientation relative to the
camera; remove the hand for an isolated render. To keep a hand holding the
product in the final image, explicitly add a person interaction. Do not infer
the intended output from the presence of a hand in an input photo alone.

Compare the result with the target view as well as the identity reference:
which surfaces are visible, how much of the top/underside is shown, how near
and far edges shorten, and whether the product has been mirrored or flattened.

## Show an adult wearing, holding or using a product

Set `[person] module = "product-use"` and supply:

- `description`: adult subject, relevant appearance and clothing;
- `interaction`: how the item is worn, carried, gripped or used;
- `scale`: known dimensions/fit or an approved scale relationship. Ask when scale
  matters and the references/brief do not establish it; do not invent measurements;
- `reference`: optional authorized adult image. Omit it when generating an
  unspecified adult; do not imply a particular person's endorsement.

Use `camera/person-context` with `view`, `framing` and `focus`, or
`camera/reference-perspective` when a reference determines the product's view.
Use `background/environment` with `scene` and `light` for a setting. Use
`exclusions/person-product` instead of `isolated-product`, which forbids people.
For a hand-only final crop, state that framing explicitly and describe the grip.

Keep the product's construction and real scale while allowing natural cloth
drape, flexible straps or articulation. Check support, contact, fit, occlusion,
anatomy and visible branding. If a target angle is incompatible with natural
wear or the requested crop, resolve that choice with the user before spending
on a render. This is prompt guidance, not a guarantee of person identity across
a series; each image needs review.

Both new examples contain text-only illustrative briefs and no reference photos.
Build them with `scripts/build_prompt.py` just like the eyewear example, then
inspect a free request preview after supplying the files. Existing paid-call
authorization and request limits still apply; changing the scene does not grant
additional attempts.
