# Fotogen gallery: sources and scope

The main README uses real assets from Szymon Bubała's StoreKite product-photo
video pack. The two products are Biohac Mentor and Eclipse with orange lenses.

| Files | Role | Original filenames in the video pack |
|---|---|---|
| `mentor/input-01.jpg` through `input-05.jpg` | Five phone reference views | `product_reference/mentor-1.jpg` through `mentor-5.jpg` |
| `eclipse/input-01.jpg` through `input-05.jpg` | Five phone reference views | `product_reference/eclipse-1.jpg` through `eclipse-5.jpg` |
| `mentor/packshot.jpg`, `eclipse/packshot.jpg` | Existing Gemini product-image results | `generated_result/mentor-gemini-output.jpg`, `eclipse-gemini-output.jpg` |
| `mentor/set.jpg`, `eclipse/set.jpg` | Separate-step set results from the video pack | `generated_result/mentor-set.png`, `eclipse-set.png` |
| `accessories.jpg` | Existing accessory visual used alongside product images for the sets | `generated_result/21x9-set-bottom-image.png` |
| `mentor/on-model.jpg` | Earlier portfolio series, not a result of these phone inputs | `bursztyn-coralguard-model-orange-coralguard-1.avif` |

The original Downloads pack used names such as `mentor (1).jpg`; the video
archive normalized those names to `mentor-1.jpg`. The set results were prepared
separately from the clean product images, using the accessory visual as another
reference. They should not be presented as a single-call output from the phone
photos alone. The on-model picture predates these phone inputs; its original
inputs are not in this collection.

The held views (`mentor/input-05.jpg`, `eclipse/input-01.jpg`) specify the desired
perspective of the product: orientation, visible surfaces and foreshortening.
Their role is not to request a hand in the isolated render. Product construction
is established by the other reference views. This distinction also applies to
other product categories.

These are historical workflow examples, not execution receipts for the public
`orange-lens-eyewear/job.toml`. Exact original prompts, model versions and attempt
counts are not provided by this gallery. A visual example does not prove that a
marketplace will accept an image, or that every product detail is exact.

## Image preparation

Only EXIF orientation, proportional downscaling to a maximum dimension of 960 px,
JPEG encoding and metadata removal were applied. No cropping, retouching, logo
replacement or generation was done for the README. Originals remain outside the
repository. [manifest.json](manifest.json) records source/output SHA-256 hashes,
dimensions and roles without exposing local folder paths.

To rebuild from the owner's original video pack (not distributed here):

```bash
python -m pip install Pillow
python scripts/prepare_readme_gallery.py --sources /path/to/video/01_sources --portfolio /path/to/bursztyn-coralguard-model-orange-coralguard-1.avif
```

Pillow must support AVIF for the portfolio source. The script is intended for
maintaining this gallery, not for generating new product images.

## Usage

Product photos, generated result images and Biohac branding in this folder are
included to demonstrate the workflow. They are excluded from the repository's
CC BY 4.0 content license. No permission to reuse these assets for another shop,
advertisement or endorsement is granted here. Biohac marks remain with their
owner. The documentation and image-preparation script retain the repository's
usual content and code licenses.
