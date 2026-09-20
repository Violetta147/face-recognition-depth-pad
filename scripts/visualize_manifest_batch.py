"""Create a privacy-local contact sheet from manifest samples for a report demo."""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
from PIL import Image, ImageDraw, ImageOps


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("manifest")
parser.add_argument("--data-root", required=True)
parser.add_argument("--split", choices=["train", "val", "test"], default="val")
parser.add_argument("--count", type=int, default=12)
parser.add_argument("--output", default="reports/manifest-batch.png")
args = parser.parse_args()

frame = pd.read_csv(args.manifest, keep_default_na=False)
frame = frame[frame["split"] == args.split]
if frame.empty:
    raise SystemExit(f"manifest has no rows for split={args.split}")

# Select evenly across both labels without changing the experiment data.
per_label = max(1, args.count // 2)
selected = pd.concat(
    [group.head(per_label) for _, group in frame.groupby("label", sort=True)],
    ignore_index=True,
).head(args.count)

tile_width, tile_height, caption_height = 240, 180, 42
columns = 4
rows = (len(selected) + columns - 1) // columns
sheet = Image.new("RGB", (columns * tile_width, rows * (tile_height + caption_height)), "white")
draw = ImageDraw.Draw(sheet)
root = Path(args.data_root)

for index, row in enumerate(selected.itertuples(index=False)):
    image = Image.open(root / str(row.image_path)).convert("RGB")
    image = ImageOps.fit(image, (tile_width, tile_height), method=Image.Resampling.LANCZOS)
    x = (index % columns) * tile_width
    y = (index // columns) * (tile_height + caption_height)
    sheet.paste(image, (x, y))
    label = "LIVE" if int(row.label) == 1 else "ATTACK"
    draw.text((x + 6, y + tile_height + 4), f"{label}  {row.video_id}", fill="black")
    draw.text((x + 6, y + tile_height + 21), str(row.sample_id), fill="#555555")

destination = Path(args.output)
destination.parent.mkdir(parents=True, exist_ok=True)
sheet.save(destination)
print(f"wrote {len(selected)} samples to {destination}")
