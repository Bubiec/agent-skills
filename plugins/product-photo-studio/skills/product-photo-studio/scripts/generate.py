#!/usr/bin/env python3
"""Generate or edit product images with Gemini image models on Vertex AI.

Preview is the default: the script writes request.json and spends nothing.
A paid request needs --execute, is recorded in a local usage ledger and is
blocked once the daily or monthly request limit is reached. Live 4K needs
--allow-4k as well. Authentication uses Application Default Credentials;
this script never reads or stores keys or tokens.
"""
import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

MODE_RULES = {
    # "none" sends the prompt as written; build_prompt.py already includes the product lock.
    "none": "",
    "product": (
        "Preserve the referenced product exactly: geometry, materials, logos, markings, colours, "
        "transparency, reflections, proportions and accessories. Change only the requested scene "
        "or composition. Do not add text or redesign the product."
    ),
    "person": (
        "Show an adult person using the referenced product naturally. Preserve the product exactly, "
        "including its geometry, logos, markings, colours, transparency and reflections. Keep anatomy "
        "and product contact physically plausible."
    ),
    "macro": (
        "Create a photographic macro of the requested area of the referenced product. Preserve its "
        "construction, logo artwork, engraved text, material transitions, colour and edge thickness. "
        "Do not invent screws, seams, textures or branding."
    ),
}

MAX_REFERENCES = {
    "gemini-3.1-flash-image": 14,
    "gemini-3-pro-image": 14,
}

# Approximate output-image prices, verified 2026-10-20 against Vertex pricing.
# Input and text/reasoning tokens cost extra. This is not a billing cap.
OUTPUT_PRICE_USD = {
    "gemini-3.1-flash-image": {"512": 0.045, "1K": 0.067, "2K": 0.101, "4K": 0.15},
    "gemini-3-pro-image": {"1K": 0.134, "2K": 0.134, "4K": 0.24},
}

ASPECT_RATIOS = ["1:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9", "21:9"]
IMAGE_SIZES = ["512", "1K", "2K", "4K"]


def default_ledger_path() -> Path:
    if os.name == "nt" and os.environ.get("LOCALAPPDATA"):
        base = Path(os.environ["LOCALAPPDATA"])
    else:
        base = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local" / "state"))
    return base / "product-photo-studio" / "usage.jsonl"


def read_ledger(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    entries = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise SystemExit(f"Invalid usage ledger at {path}:{number}; repair it before continuing") from exc
        if not isinstance(value, dict) or value.get("event") not in {"attempted", "completed"} or not value.get("created_at"):
            raise SystemExit(f"Invalid usage ledger entry at {path}:{number}")
        entries.append(value)
    return entries


def attempted_counts(path: Path, now: datetime) -> tuple[int, int]:
    day_prefix = now.strftime("%Y-%m-%d")
    month_prefix = now.strftime("%Y-%m")
    attempts = [entry for entry in read_ledger(path) if entry.get("event") == "attempted"]
    daily = sum(str(entry.get("created_at", "")).startswith(day_prefix) for entry in attempts)
    monthly = sum(str(entry.get("created_at", "")).startswith(month_prefix) for entry in attempts)
    return daily, monthly


def append_ledger(path: Path, entry: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def reserve_attempt(path: Path, daily_limit: int, monthly_limit: int, entry: dict) -> None:
    """Atomically count and reserve before sending, including concurrent processes."""
    path.parent.mkdir(parents=True, exist_ok=True)
    lock = path.with_name(path.name + ".lock")
    try:
        lock.mkdir()
    except FileExistsError as exc:
        raise SystemExit(f"Usage ledger locked: {lock}. Retry later; after a crash, verify no process is using it before removing the empty lock folder.") from exc
    try:
        now = datetime.now(timezone.utc)
        daily, monthly = attempted_counts(path, now)
        if daily >= daily_limit:
            raise SystemExit(f"Daily request limit reached: {daily}/{daily_limit} (UTC)")
        if monthly >= monthly_limit:
            raise SystemExit(f"Monthly request limit reached: {monthly}/{monthly_limit} (UTC)")
        append_ledger(path, {**entry, "event": "attempted", "created_at": now.isoformat()})
    finally:
        lock.rmdir()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def extension_for_mime(mime: str | None) -> str:
    return {"image/jpeg": ".jpg", "image/webp": ".webp"}.get(mime or "", ".png")


def load_job(path: Path | None) -> dict:
    if not path:
        return {}
    job = json.loads(path.read_text(encoding="utf-8"))
    job["references"] = [Path(ref["path"]) for ref in job.get("references", [])]
    job["prompt_file"] = Path(job["prompt_file"]) if job.get("prompt_file") else None
    return job


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate product images with Gemini on Vertex AI (preview by default)")
    parser.add_argument("--job", type=Path, help="job.json written by build_prompt.py")
    parser.add_argument("--mode", choices=MODE_RULES, help="Rule prepended to the prompt (default: none with --job, else product)")
    parser.add_argument("--prompt")
    parser.add_argument("--prompt-file", type=Path)
    parser.add_argument("--reference", action="append", type=Path, default=[], help="Reference image; repeat in the order the prompt expects")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--model", choices=MAX_REFERENCES)
    parser.add_argument("--aspect-ratio", choices=ASPECT_RATIOS)
    parser.add_argument("--image-size", choices=IMAGE_SIZES)
    parser.add_argument("--project", default=os.environ.get("GOOGLE_CLOUD_PROJECT"))
    parser.add_argument("--location", default=os.environ.get("GOOGLE_CLOUD_LOCATION", "global"))
    execution = parser.add_mutually_exclusive_group()
    execution.add_argument("--execute", action="store_true", help="Perform one live, paid request")
    execution.add_argument("--dry-run", action="store_true", help="Explicit preview; preview is also the default")
    parser.add_argument("--daily-request-limit", type=int, default=int(os.environ.get("PHOTO_STUDIO_DAILY_LIMIT", "10")))
    parser.add_argument("--monthly-request-limit", type=int, default=int(os.environ.get("PHOTO_STUDIO_MONTHLY_LIMIT", "50")))
    parser.add_argument("--usage-ledger", type=Path, default=default_ledger_path())
    parser.add_argument("--allow-4k", action="store_true", help="Required together with --execute for a live 4K request")
    args = parser.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    job = load_job(args.job)
    model = args.model or job.get("model") or "gemini-3.1-flash-image"
    aspect_ratio = args.aspect_ratio or job.get("aspect_ratio") or "1:1"
    image_size = args.image_size or job.get("image_size") or "2K"
    mode = args.mode or ("none" if args.job else "product")
    references = [path.resolve() for path in (args.reference or job.get("references", []))]
    prompt_file = args.prompt_file or job.get("prompt_file")

    if model not in MAX_REFERENCES:
        raise SystemExit(f"Unsupported model {model}. Choose one of: {', '.join(MAX_REFERENCES)}")
    if aspect_ratio not in ASPECT_RATIOS or image_size not in IMAGE_SIZES:
        raise SystemExit("Unsupported aspect ratio or image size")
    if args.prompt and args.prompt_file:
        raise SystemExit("Provide only one prompt override")
    if args.prompt:
        prompt_file = None
    if bool(args.prompt) == bool(prompt_file):
        raise SystemExit("Provide exactly one prompt: --prompt, --prompt-file or --job")
    body = (args.prompt or Path(prompt_file).read_text(encoding="utf-8")).strip()
    if not body:
        raise SystemExit("Prompt must not be empty")
    prompt = f"{MODE_RULES[mode]}\n\nRequested result:\n{body}" if MODE_RULES[mode] else body

    missing = [str(path) for path in references if not path.is_file()]
    if missing:
        raise SystemExit(f"Missing reference files: {missing}")
    if len(references) > MAX_REFERENCES[model]:
        raise SystemExit(f"{model} accepts at most {MAX_REFERENCES[model]} reference images")
    if model != "gemini-3.1-flash-image" and image_size == "512":
        raise SystemExit("512 output is available only on gemini-3.1-flash-image")
    if args.daily_request_limit < 1 or args.monthly_request_limit < 1:
        raise SystemExit("Request limits must be positive integers")

    now = datetime.now(timezone.utc)
    daily_attempts, monthly_attempts = attempted_counts(args.usage_ledger, now)
    estimated_output_usd = OUTPUT_PRICE_USD.get(model, {}).get(image_size)

    request = {
        "provider": "google-vertex-ai",
        "model": model,
        "project": args.project,
        "location": args.location,
        "mode": mode,
        "aspect_ratio": aspect_ratio,
        "image_size": image_size,
        "prompt": prompt,
        "references": [
            {"path": str(path), "sha256": sha256(path), "bytes": path.stat().st_size} for path in references
        ],
        "created_at": now.isoformat(),
        "execute_requested": args.execute,
        "estimated_output_usd": estimated_output_usd,
        "estimate_scope": "output image only; input images and text are charged separately",
        "usage_ledger": str(args.usage_ledger.resolve()),
        "usage_before_request": {
            "daily_attempts": daily_attempts,
            "daily_limit": args.daily_request_limit,
            "monthly_attempts": monthly_attempts,
            "monthly_limit": args.monthly_request_limit,
        },
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    request_path = args.output_dir / "request.json"
    request_path.write_text(json.dumps(request, ensure_ascii=False, indent=2), encoding="utf-8")
    if not args.execute:
        print(json.dumps({"dry_run": True, "request": str(request_path), **request}, ensure_ascii=False, indent=2))
        return
    if not args.project:
        raise SystemExit("Set GOOGLE_CLOUD_PROJECT or pass --project")
    if image_size == "4K" and not args.allow_4k:
        raise SystemExit("Live 4K is blocked by default. Approve a 2K draft first, then add --allow-4k.")
    if daily_attempts >= args.daily_request_limit:
        raise SystemExit(f"Daily request limit reached: {daily_attempts}/{args.daily_request_limit} (UTC)")
    if monthly_attempts >= args.monthly_request_limit:
        raise SystemExit(f"Monthly request limit reached: {monthly_attempts}/{args.monthly_request_limit} (UTC)")

    try:
        from google import genai
        from google.genai import types
        from PIL import Image
    except ImportError as exc:
        raise SystemExit("Install dependencies: python -m pip install -r requirements.txt") from exc

    contents = [Image.open(path) for path in references]
    contents.append(prompt)
    client = genai.Client(
        vertexai=True, project=args.project, location=args.location,
        http_options=types.HttpOptions(retry_options=types.HttpRetryOptions(attempts=1)),
    )
    config = types.GenerateContentConfig(
        response_modalities=[types.Modality.TEXT, types.Modality.IMAGE],
        image_config=types.ImageConfig(aspect_ratio=aspect_ratio, image_size=image_size),
    )
    reserve_attempt(
        args.usage_ledger,
        args.daily_request_limit,
        args.monthly_request_limit,
        {
            "event": "attempted",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "model": model,
            "image_size": image_size,
            "estimated_output_usd": estimated_output_usd,
            "request": str(request_path.resolve()),
        },
    )
    response = client.models.generate_content(model=model, contents=contents, config=config)

    outputs, text_parts, image_index = [], [], 0
    for candidate in response.candidates or []:
        if not candidate.content:
            continue
        for part in candidate.content.parts or []:
            if part.text:
                text_parts.append(part.text)
            elif part.inline_data and part.inline_data.data:
                image_index += 1
                output_path = args.output_dir / f"generated-{image_index:02d}{extension_for_mime(part.inline_data.mime_type)}"
                output_path.write_bytes(part.inline_data.data)
                outputs.append(str(output_path.resolve()))
    if text_parts:
        (args.output_dir / "response.txt").write_text("\n\n".join(text_parts), encoding="utf-8")
    request["outputs"] = outputs
    request_path.write_text(json.dumps(request, ensure_ascii=False, indent=2), encoding="utf-8")
    if not outputs:
        print("No image returned; check response.txt for safety feedback", file=sys.stderr)
        raise SystemExit(1)
    append_ledger(
        args.usage_ledger,
        {
            "event": "completed",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "model": model,
            "image_size": image_size,
            "outputs": len(outputs),
            "request": str(request_path.resolve()),
        },
    )
    print(json.dumps({"request": str(request_path), "outputs": outputs}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
