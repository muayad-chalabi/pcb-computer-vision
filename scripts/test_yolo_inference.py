"""
Load a YOLO model and run inference on test images, displaying results in a grid.
"""

from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path

# Ensure the package is importable
sys.path.append(str(Path(__file__).resolve().parent.parent))

try:
    from ultralytics import YOLO
except ImportError:
    print("Error: 'ultralytics' package not found. Please install it with 'pip install ultralytics'.")
    # For testing purposes without the library, we might mock it, but user asked for script.
    # We will exit if not found for now.
    sys.exit(1)

from PIL import Image, ImageDraw

from pcb_cv.data_loader import DatasetConfig, load_dataset, PCBImage
from pcb_cv.visualization import save_image_grid, overlay_bbox


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Test YOLO model on PCB dataset.")
    parser.add_argument(
        "--data-root",
        type=Path,
        default=Path("data"),
        help="Directory containing the dataset.",
    )
    parser.add_argument(
        "--model-path",
        type=Path,
        default=Path("yolo/yolo11n_ft.pt"),
        help="Path to the YOLO model file.",
    )
    parser.add_argument(
        "--max-images",
        type=int,
        default=18,
        help="Number of images to test.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("outputs/yolo_test_results.png"),
        help="Where to save the result grid.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    # 1. Load Model
    if not args.model_path.exists():
        print(f"Error: Model not found at {args.model_path}")
        # Only for development: check if we are just testing the script structure
        # return
        sys.exit(1)

    print(f"Loading YOLO model from {args.model_path}...")
    model = YOLO(str(args.model_path))

    # 2. Load Dataset
    config = DatasetConfig(root_dir=args.data_root)
    print(f"Loading dataset from {config.default_dataset_dir}...")
    all_images = load_dataset(config)
    
    # Filter for test set
    test_images = [img for img in all_images if img.dataset_type == 'test']
    
    if not test_images:
        print("No test images found! Checking for any images...")
        test_images = all_images
        
    if not test_images:
        print("No images found at all.")
        sys.exit(1)

    print(f"Found {len(test_images)} test images. Selecting {args.max_images}...")
    
    # Sample random images
    selected_images = random.sample(test_images, min(len(test_images), args.max_images))

    # 3. Define Overlay Function
    def prediction_overlay(image: Image.Image, item: PCBImage) -> Image.Image:
        # Run inference on the image
        # We can pass the PIL image directly to YOLO
        results = model(image, verbose=False)
        
        # Helper to draw on the image
        overlay_img = image.copy()
        draw = ImageDraw.Draw(overlay_img)
        
        # Ground Truth (Green)
        if item.bbox:
             overlay_img = overlay_bbox(overlay_img, item.bbox, color="lime", width=3, label=item.class_name)
        
        # Predictions (Red)
        for result in results:
            names = result.names
            boxes = result.boxes
            for box in boxes:
                # box.xyxy format: x1, y1, x2, y2
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                conf = box.conf[0].item()
                cls = int(box.cls[0].item())
                class_name = names[cls] if names and cls in names else str(cls)
                
                label = f"{class_name} {conf:.2f}"
                
                # Convert to our bbox format (x, y, w, h) or just draw xyxy
                # Visualization util takes (left, top, w, h)
                w = x2 - x1
                h = y2 - y1
                bbox_tuple = (x1, y1, w, h)
                
                overlay_img = overlay_bbox(overlay_img, bbox_tuple, color="red", width=3, label=label )
                
        return overlay_img

    # 4. Generate Grid
    print("Running inference and generating grid...")
    output_path = save_image_grid(
        selected_images,
        args.output,
        max_images=args.max_images,
        columns=3,
        overlay=prediction_overlay,
        get_image_path=lambda x: x.path,
        get_title=lambda x: f"{x.class_name}\n({x.filename})"
    )
    
    print(f"Saved inference results to {output_path}")


if __name__ == "__main__":
    main()
