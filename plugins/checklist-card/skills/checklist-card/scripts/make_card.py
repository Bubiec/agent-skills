#!/usr/bin/env python3
"""Build a printable A4 HTML sheet of 5-step double-sided checklist cards. Standard library only."""
import argparse
import html
import json
from pathlib import Path
import sys

WIDTH, HEIGHT = 76, 86
CLIP_W, CLIP_H = 16, 4
ROWS = 5
PER_PAGE = 4
# Row centres from the card's bottom edge and the back labels, mm.
CENTERS = [62.5, 48.5, 34.5, 20.5, 6.5]
TITLE_BOTTOM, TITLE_TOP = 69.5, 81.5
BACK_TITLE_Y, BACK_PULL_Y = 60, 17
MAX_TITLE, MAX_STEP, MAX_BACK, MAX_BACK_WORD = 44, 60, 24, 12
FILLS = ["#e2f3eb", "#e8f0f8", "#eee8f7", "#faedde", "#f4e5ea"]
CSS = """@page{size:A4 portrait;margin:0}*{box-sizing:border-box}body{margin:0;font-family:Arial,Helvetica,sans-serif;color:#20343b;print-color-adjust:exact;-webkit-print-color-adjust:exact}
.sheet{position:relative;width:210mm;height:297mm;overflow:hidden;break-after:page}.card{position:absolute;width:76mm;height:86mm}.cut{position:absolute;inset:0;width:100%;height:100%;overflow:visible;fill:none;stroke:#667;stroke-width:.18;stroke-dasharray:.8 .6}
.title{position:absolute;left:2mm;width:72mm;display:flex;align-items:center;justify-content:center;text-align:center;font:700 13pt/1.1 Arial,sans-serif}
.row{position:absolute;left:2mm;width:72mm;height:10mm;display:flex;align-items:center;padding:0 2mm 0 4mm;border:.2mm solid #667;border-radius:4.5mm;font:700 10pt/1.15 Arial,sans-serif}
.back{position:absolute;left:29mm;width:18mm;height:14mm;display:flex;align-items:center;justify-content:center;text-align:center;font:700 9.5pt/1.1 Arial,sans-serif}
.scale{position:absolute;bottom:10mm;left:20mm;width:100mm;border-top:.25mm solid #20343b;font-size:8pt;padding-top:1mm}"""


def validate(job):
    """Return every problem at once, so wording can be fixed in one pass."""
    problems = []
    cards = job.get("cards") if isinstance(job, dict) else None
    if not isinstance(cards, list) or not cards:
        return ["job needs a non-empty cards list"]
    for number, card in enumerate(cards, 1):
        title = card.get("title", "")
        back = card.get("back_title") or title
        steps = card.get("steps", [])
        if not title or len(title) > MAX_TITLE:
            problems.append(f"card {number}: title needs 1-{MAX_TITLE} characters")
        if len(back) > MAX_BACK or any(len(word) > MAX_BACK_WORD for word in back.split()):
            problems.append(f"card {number}: back title over {MAX_BACK} characters or a word over {MAX_BACK_WORD}: set a shorter back_title")
        if not isinstance(steps, list) or len(steps) > ROWS:
            problems.append(f"card {number}: at most {ROWS} steps, got {len(steps)}: group them or split the card")
            continue
        for row, step in enumerate(steps, 1):
            if len(step) > MAX_STEP:
                problems.append(f"card {number} step {row}: over {MAX_STEP} characters")
    return problems


def cut_line():
    return (f'<svg class="cut" viewBox="0 0 {WIDTH} {HEIGHT}"><path d="M{CLIP_W} 0H{WIDTH - CLIP_W}V{CLIP_H}H{WIDTH}'
            f'V{HEIGHT}H0V{CLIP_H}H{CLIP_W}Z"/></svg>')


def position(index, back):
    x = 20 + 88 * (index % 2)
    # A long-edge flip mirrors the sheet horizontally.
    return (210 - x - WIDTH if back else x), 25 + (HEIGHT + 6) * (index // 2)


def front(card):
    parts = [cut_line(), f'<div class="title" style="top:{HEIGHT - TITLE_TOP}mm;height:{TITLE_TOP - TITLE_BOTTOM}mm">{html.escape(card["title"])}</div>']
    steps = card.get("steps", [])
    for row, center in enumerate(CENTERS):
        text = html.escape(steps[row]) if row < len(steps) else ""
        parts.append(f'<div class="row" style="top:{HEIGHT - center - 5}mm;background:{FILLS[row]}"><span>{text}</span></div>')
    return "".join(parts)


def rear(card, pull):
    name = html.escape(card.get("back_title") or card["title"])
    return (cut_line() + f'<div class="back" style="top:{HEIGHT - BACK_TITLE_Y - 7}mm">{name}</div>'
            f'<div class="back" style="top:{HEIGHT - BACK_PULL_Y - 7}mm">{html.escape(pull)}</div>')


def sheet(cards, back, pull):
    body = []
    for index, card in enumerate(cards):
        x, y = position(index, back)
        inner = rear(card, pull) if back else front(card)
        body.append(f'<article class="card" style="left:{x}mm;top:{y}mm">{inner}</article>')
    return f'<section class="sheet">{"".join(body)}<div class="scale">100 mm</div></section>'


def build(job, copies=1):
    problems = validate(job)
    if problems:
        raise ValueError("\n".join(problems))
    pull = job.get("pull", "\u2191 Pull out")
    cards = [card for card in job["cards"] for _ in range(copies)]
    pages = []
    for start in range(0, len(cards), PER_PAGE):
        chunk = cards[start:start + PER_PAGE]
        pages += [sheet(chunk, False, pull), sheet(chunk, True, pull)]
    return f'<!doctype html><html><head><meta charset="utf-8"><title>Checklist cards</title><style>{CSS}</style></head><body>{"".join(pages)}</body></html>'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("job", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--copies", type=int, default=1)
    args = parser.parse_args()
    if not 1 <= args.copies <= 24:
        parser.error("--copies must be 1-24")
    try:
        result = build(json.loads(args.job.read_text(encoding="utf-8")), args.copies)
    except ValueError as error:
        sys.exit(str(error))
    args.output.write_text(result, encoding="utf-8")
    print(f"Wrote {args.output}. Print A4, double-sided, long edge, 100%.")


if __name__ == "__main__":
    main()
