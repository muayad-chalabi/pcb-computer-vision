"""Preview PCB dataset images."""

from __future__ import annotations

import argparse
from pathlib import Path

from pcb_cv.data_loader import DatasetConfig, ensure_dataset, find_images
from pcb_cv.visualization import overlay_full_image_bbox, save_image_grid


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Preview PCB dataset images.")
    parser.add_argument(
        "--data-root",
        type=Path,
        default=Path("data"),
        help="Directory containing or to download the dataset.",
    )
    parser.add_argument(
        "--max-images",
        type=int,
        default=9,
        help="Number of images to include in the preview grid.",
    )
    parser.add_argument(
        "--columns",
        type=int,
        default=3,
        help="Number of columns in the preview grid.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("outputs") / "dataset_preview.png",
        help="Where to save the preview image.",
    )
    parser.add_argument(
        "--overlay-bbox",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Overlay a bounding box on each image.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = DatasetConfig(root_dir=args.data_root)
    dataset_dir = ensure_dataset(config)
    images = find_images(dataset_dir)
    if not images:
        raise SystemExit(f"No images found under {dataset_dir}")
    overlay = overlay_full_image_bbox if args.overlay_bbox else None
    output_path = save_image_grid(
        images,
        args.output,
        max_images=args.max_images,
        columns=args.columns,
        overlay=overlay,
    )
    print(f"Saved preview grid to {output_path}")


if __name__ == "__main__":
    main()
