# Reviewing generated product images

Review at full resolution, next to the references. A result that looks great but changes the product is a failure, not a creative alternative.

## Reject when

- the product shape, proportions, part count or construction differ from the reference (extra or missing hinges, doubled straps, merged parts, different thickness);
- the colour-locked part has a different hue, density or transparency than the sample, or differs between parts (left and right lens, two sides of a bag);
- the logo is redrawn, misspelled, mirrored, resized, duplicated or on the wrong part;
- text, badges, watermarks or props appear that nobody asked for;
- the background is not uniform or shows an edge, floor or shadow when the job asked for pure white;
- a person shows implausible anatomy or product contact (glasses floating off the ears, fingers through a handle).

## Comparison prompt

To get a second opinion from a vision model, ask for a comparison, never a redesign:

> Compare the candidate image with every supplied reference. List each discrepancy in product shape, parts, logo, text, colour, transparency, reflections, background and, if present, human anatomy. Give the location of each discrepancy. Do not suggest creative alternatives and do not rate the image's aesthetics.

## After review

- Fix one module at a time: perspective problems live in `camera`, colour drift in `color_lock`, extra objects in `exclusions`. Changing everything at once makes it impossible to learn what worked.
- Keep the job file, `prompt.txt` and `request.json` of every run with its output. They are the record of what produced which image.
- Mark an image as approved only after the user says so.
