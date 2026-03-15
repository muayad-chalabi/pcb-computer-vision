"""Preview PCB dataset images."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

# Ensure the package is importable
sys.path.append(str(Path(__file__).resolve().parent.parent))

from pcb_cv.data_loader import DatasetConfig, load_dataset, PCBImage
from pcb_cv.visualization import save_image_grid, overlay_item_bbox


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
        "--no-overlay-bbox",
        action="store_false",
        dest="overlay_bbox",
        help="Disable bounding box overlays.",
    )
    # Default is True for overlay_bbox
    parser.set_defaults(overlay_bbox=True)
    
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = DatasetConfig(root_dir=args.data_root)
    
    print(f"Loading dataset from {config.default_dataset_dir}...")
    images = load_dataset(config)
    
    if not images:
        raise SystemExit(f"No images found under {config.default_dataset_dir}")
    
    print(f"Found {len(images)} images.")
    
    def overlay_adapter(image, item):
        if args.overlay_bbox and isinstance(item, PCBImage) and item.bbox:
             # We can add label text if we want
             return overlay_item_bbox(image, item, color="lime", width=5)
        return image

    output_path = save_image_grid(
        images,
        args.output,
        max_images=args.max_images,
        columns=args.columns,
        overlay=overlay_adapter if args.overlay_bbox else None,
        get_image_path=lambda x: x.path
    )
    print(f"Saved preview grid to {output_path}")


if __name__ == "__main__":
    main()
