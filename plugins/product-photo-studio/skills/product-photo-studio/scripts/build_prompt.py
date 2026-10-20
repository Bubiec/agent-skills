#!/usr/bin/env python3
"""Assemble an image-generation prompt from a job file and prompt modules.

The job file (TOML) names one module per section and fills its placeholders.
The builder numbers the reference images in the order they will be sent,
so modules can say "Image 2" without guessing.

Template syntax inside modules:
  {{section.key}}          value from the job file
  {{section.key|upper}}    upper-cased value
  {{section.key|or}}       list joined as "a, b or c" (|and gives "a, b and c")
  {{ref.product}}          "Image N" for a reference image (product, color_lock, logo)
  [[if section.key]]text   line kept only when that key is set and non-empty
"""
import argparse
import json
import re
import sys
import tomllib
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
MODULES_DIR = SKILL_DIR / "assets" / "modules"

# Section order in the final prompt. Each section is optional except product.
SECTIONS = ["product", "camera", "person", "background", "color_lock", "logo", "exclusions"]
DEFAULT_MODULES = {"product": "product-lock"}

# Reference images, in the order they are sent to the model.
REFERENCE_SLOTS = [
    ("product", "reference", "the product. Copy it exactly."),
    ("camera", "reference", "product perspective only: match viewpoint, orientation and foreshortening. Product identity comes from the product reference. Do not copy hands, people or background unless requested in the PERSON section."),
    ("person", "reference", "approved adult-person reference: use the requested appearance and pose for the PERSON section. Product identity comes from the product reference."),
    ("color_lock", "reference", "colour sample. Take only the colour from it, not its shape, background or lighting."),
    ("logo", "file", "logo artwork. Reproduce it exactly; it is an approved mark, not a design suggestion."),
]
ACCEPTED_IMAGE_TYPES = {".png", ".jpg", ".jpeg", ".webp"}

PLACEHOLDER = re.compile(r"\{\{\s*([a-z_]+(?:\.[a-z_]+)+)\s*(?:\|\s*([a-z]+)\s*)?\}\}")
CONDITION = re.compile(r"^\[\[if\s+([a-z_]+(?:\.[a-z_]+)+)\]\]")


def human_join(items: list, word: str) -> str:
    items = [str(item) for item in items]
    if len(items) <= 1:
        return "".join(items)
    return f"{', '.join(items[:-1])} {word} {items[-1]}"


def lookup(values: dict, dotted: str):
    node = values
    for part in dotted.split("."):
        if not isinstance(node, dict) or part not in node:
            return None
        node = node[part]
    return node


def render_value(value, filter_name: str | None) -> str:
    if filter_name == "or":
        return human_join(value if isinstance(value, list) else [value], "or")
    if filter_name == "and":
        return human_join(value if isinstance(value, list) else [value], "and")
    text = ", ".join(map(str, value)) if isinstance(value, list) else str(value)
    if filter_name == "upper":
        return text.upper()
    if filter_name:
        raise SystemExit(f"Unknown filter |{filter_name}")
    return text


def render(template: str, values: dict, source: str, missing: list[str]) -> str:
    lines = []
    for line in template.splitlines():
        condition = CONDITION.match(line)
        if condition:
            if lookup(values, condition.group(1)) in (None, "", []):
                continue
            line = line[condition.end():]

        def substitute(match: re.Match) -> str:
            value = lookup(values, match.group(1))
            if value in (None, "", []):
                missing.append(f"{source}: {match.group(1)}")
                return match.group(0)
            return render_value(value, match.group(2))

        lines.append(PLACEHOLDER.sub(substitute, line))
    return "\n".join(lines).strip()


def module_path(section: str, name: str) -> Path:
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name):
        raise SystemExit(f"Invalid module name: {name}")
    candidates = [MODULES_DIR / section / f"{name}.md", MODULES_DIR / f"{name}.md"]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    available = sorted(p.stem for p in (MODULES_DIR / section).glob("*.md")) if (MODULES_DIR / section).is_dir() else []
    raise SystemExit(f"No module '{name}' for [{section}]. Available: {', '.join(available) or 'none'}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build an image prompt from a job file and prompt modules")
    parser.add_argument("job", type=Path, help="Job file (TOML)")
    parser.add_argument("--out", type=Path, help="Folder for prompt.txt and job.json (default: print only)")
    args = parser.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    job_file = args.job.resolve()
    with job_file.open("rb") as handle:
        values = tomllib.load(handle)
    base = job_file.parent

    camera_module = lookup(values, "camera.module")
    if camera_module == "reference-perspective" and not lookup(values, "camera.reference"):
        raise SystemExit("[camera] reference-perspective requires reference: supply the target product-view image")
    if lookup(values, "camera.reference") and camera_module in (None, "three-quarter-studio", "eyewear-three-quarter-low", "macro-detail", "person-context"):
        raise SystemExit("[camera] reference requires module = 'reference-perspective' to avoid a conflicting fixed camera angle")
    person_module = lookup(values, "person.module")
    if lookup(values, "person.reference") and not person_module:
        raise SystemExit("[person] reference requires a person module, such as 'product-use'")
    if person_module and person_module != "none" and lookup(values, "exclusions.module") == "isolated-product":
        raise SystemExit("[person] product-use conflicts with [exclusions] isolated-product, which forbids people and hands; use person-product instead")

    references, ref_labels, warnings = [], {}, []
    for section, key, role in REFERENCE_SLOTS:
        raw = lookup(values, f"{section}.{key}")
        if not raw or lookup(values, f"{section}.module") == "none":
            continue
        path = (base / raw).resolve()
        if path.suffix.lower() == ".svg":
            if section != "logo":
                raise SystemExit(f"{raw}: only logo references can use SVG; use a raster image for [{section}]")
            if not args.out:
                # A text-only preview neither loads the renderer nor writes files.
                warnings.append("SVG logo will be exported automatically when --out is supplied")
            else:
                from export_svg import export_svg
                target = args.out / "references" / "logo.png"
                try:
                    path = export_svg(path, target, lookup(values, "logo.export_width") or 1024,
                                      lookup(values, "logo.export_background") or "white", reuse_identical=True).resolve()
                except (ValueError, RuntimeError) as exc:
                    raise SystemExit(str(exc)) from exc
        if path.suffix.lower() not in ACCEPTED_IMAGE_TYPES and path.suffix.lower() != ".svg":
            raise SystemExit(f"{raw}: use PNG, JPEG or WEBP")
        if not path.is_file():
            warnings.append(f"reference not found yet: {raw}")
        references.append({"slot": section, "path": str(path), "role": role})
        ref_labels[section] = f"Image {len(references)}"
    if "product" not in ref_labels:
        raise SystemExit("[product] reference is required: the model needs the real product to copy")
    values["ref"] = ref_labels

    header = ["REFERENCE IMAGES (in the order supplied)"]
    header += [f"- Image {i}: {ref['role']}" for i, ref in enumerate(references, start=1)]
    parts = ["\n".join(header)]
    missing: list[str] = []
    for section in SECTIONS:
        name = lookup(values, f"{section}.module") or DEFAULT_MODULES.get(section)
        if not name or name == "none":
            continue
        path = module_path(section, name)
        parts.append(render(path.read_text(encoding="utf-8"), values, f"{section}/{name}", missing))
    if missing:
        raise SystemExit("Missing values in the job file:\n  " + "\n  ".join(missing))

    prompt = "\n\n".join(parts) + "\n"

    for warning in warnings:
        print(f"warning: {warning}", file=sys.stderr)
    if not args.out:
        sys.stdout.write(prompt)
        return

    args.out.mkdir(parents=True, exist_ok=True)
    prompt_file = args.out / "prompt.txt"
    prompt_file.write_text(prompt, encoding="utf-8")
    job = lookup(values, "job") or {}
    manifest = {
        "name": job.get("name", job_file.stem),
        "model": job.get("model", "gemini-3.1-flash-image"),
        "aspect_ratio": job.get("aspect_ratio", "1:1"),
        "image_size": job.get("image_size", "2K"),
        "prompt_file": str(prompt_file.resolve()),
        "references": references,
    }
    (args.out / "job.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"prompt": str(prompt_file), "job": str(args.out / "job.json"), "references": len(references)}, indent=2))


if __name__ == "__main__":
    main()
