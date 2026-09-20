"""Render RGB, pseudo-depth, mask and histogram panels from a depth ledger."""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image, ImageDraw, ImageOps


def histogram(values: np.ndarray, size: int) -> Image.Image:
    canvas = Image.new("RGB", (size, size), "white")
    draw = ImageDraw.Draw(canvas)
    bins = np.linspace(0.0, 1.0, 25)
    counts, _ = np.histogram(values.ravel(), bins=bins)
    peak = max(int(counts.max()), 1)
    left, bottom = 22, size - 22
    draw.line((left, 8, left, bottom), fill="#777777")
    draw.line((left, bottom, size - 8, bottom), fill="#777777")
    width = size - left - 10
    height = bottom - 12
    for index, value in enumerate(counts):
        x0 = left + int(index * width / len(counts))
        x1 = left + int((index + 1) * width / len(counts)) - 1
        y0 = bottom - int(value / peak * height)
        draw.rectangle((x0, y0, x1, bottom), fill="#2878B5")
    return canvas


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ledger", required=True)
    parser.add_argument("--count", type=int, default=12)
    parser.add_argument("--output", default="reports/depth-target-contact-sheet.png")
    args = parser.parse_args()

    ledger = pd.read_csv(args.ledger, keep_default_na=False, dtype={"sample_id": str})
    required = {"sample_id", "label", "image_path", "output_path", "status", "last_error"}
    missing = sorted(required.difference(ledger.columns))
    if missing:
        raise SystemExit(f"ledger is missing columns: {missing}")
    complete = ledger[ledger["status"].isin(["complete_bona_fide", "complete_attack_zero"])]
    if complete.empty:
        raise SystemExit("ledger has no complete depth targets")
    per_label = max(1, args.count // 2)
    selected = pd.concat(
        [group.head(per_label) for _, group in complete.groupby("label", sort=True)],
        ignore_index=True,
    ).head(args.count)

    panel = 180
    caption = 44
    case_width = panel * 4
    columns = 2
    rows = (len(selected) + columns - 1) // columns
    sheet = Image.new("RGB", (case_width * columns, rows * (panel + caption)), "white")
    draw = ImageDraw.Draw(sheet)

    for index, row in enumerate(selected.itertuples(index=False)):
        image_path = Path(str(row.image_path))
        output_path = Path(str(row.output_path))
        if not image_path.is_file() or not output_path.is_file():
            raise SystemExit(f"missing artifact for {row.sample_id}: {image_path} / {output_path}")
        rgb = ImageOps.fit(Image.open(image_path).convert("RGB"), (panel, panel))
        depth = np.asarray(np.load(output_path, allow_pickle=False), dtype=np.float32)
        if depth.ndim != 2 or not np.isfinite(depth).all():
            raise SystemExit(f"invalid depth artifact for {row.sample_id}")
        clipped = np.clip(depth, 0.0, 1.0)
        depth_image = Image.fromarray((clipped * 255).astype(np.uint8), mode="L").resize(
            (panel, panel), Image.Resampling.NEAREST
        ).convert("RGB")
        mask_image = Image.fromarray(((np.abs(depth) > 1e-6) * 255).astype(np.uint8), mode="L").resize(
            (panel, panel), Image.Resampling.NEAREST
        ).convert("RGB")
        panels = [rgb, depth_image, mask_image, histogram(clipped, panel)]
        base_x = (index % columns) * case_width
        base_y = (index // columns) * (panel + caption)
        for panel_index, panel_image in enumerate(panels):
            sheet.paste(panel_image, (base_x + panel_index * panel, base_y))
        label = "LIVE" if int(row.label) == 1 else "ATTACK"
        draw.text((base_x + 6, base_y + panel + 4), f"{label} | {row.sample_id}", fill="black")
        draw.text((base_x + 6, base_y + panel + 22), "RGB | target depth | mask | histogram", fill="#555555")

    destination = Path(args.output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(destination)
    print(f"wrote {len(selected)} cases to {destination}")


if __name__ == "__main__":
    main()
