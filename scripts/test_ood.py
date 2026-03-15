"""
Run YOLO inference on out-of-dataset images.
Filters images by a phrase (e.g., "rgb") and saves predictions.
"""

import argparse
import sys
from pathlib import Path
from PIL import Image

# Ensure the package is importable
sys.path.append(str(Path(__file__).resolve().parent.parent))

from pcb_cv.visualization import overlay_bbox

try:
    from ultralytics import YOLO
except ImportError:
    print("Error: 'ultralytics' package not found. Please install it with 'pip install ultralytics'.")
    sys.exit(1)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run YOLO on out-of-dataset images.")
    parser.add_argument(
        "--model",
        type=Path,
        required=True,
        help="Path to the trained YOLO model (e.g., yolo/yolo11n_ft.pt).",
    )
    parser.add_argument(
        "--source-dir",
        type=Path,
        required=True,
        help="Directory containing input images.",
    )
    parser.add_argument(
        "--filter",
        type=str,
        default="rgb",
        help="Phrase to filter filenames by (default: 'rgb'). Only .png files are processed.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("outputs/out-of-dataset"),
        help="Directory to save results.",
    )
    parser.add_argument(
        "--conf",
        type=float,
        default=0.25,
        help="Confidence threshold.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if not args.model.exists():
        print(f"Error: Model not found at {args.model}")
        sys.exit(1)

    if not args.source_dir.exists():
        print(f"Error: Source directory not found at {args.source_dir}")
        sys.exit(1)

    # load model
    print(f"Loading model {args.model}...")
    model = YOLO(str(args.model))

    # Find images
    images = sorted(list(args.source_dir.rglob(f"*{args.filter}*.png")))
    if not images:
        print(f"No images found in {args.source_dir} matching *{args.filter}*.png")
        sys.exit(0)

    print(f"Found {len(images)} images. Processing...")

    # Ensure output directory exists
    args.output_dir.mkdir(parents=True, exist_ok=True)

    for img_path in images:
        print(f"Processing {img_path.name}...")
        
        # Run inference
        results = model.predict(str(img_path), conf=args.conf, verbose=False)
        result = results[0]
        
        # Load original image for visualization using PIL (to match our other scripts)
        # We could use result.plot() but we want to maintain the style (red boxes)
        # and result.plot() might use different colors/styles.
        # However, result.plot() is very convenient. 
        # Let's stick to the user's requested style: simple visualizer
        
        with Image.open(img_path) as img:
            img = img.convert("RGB") # Ensure RGB
            overlay_img = img.copy()
            
            names = result.names
            boxes = result.boxes
            
            for box in boxes:
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                conf = box.conf[0].item()
                cls = int(box.cls[0].item())
                class_name = names[cls] if names and cls in names else str(cls)
                
                label = f"{class_name} {conf:.2f}"
                
                w = x2 - x1
                h = y2 - y1
                # visualization util takes (left, top, w, h)
                bbox_tuple = (x1, y1, w, h)
                
                overlay_img = overlay_bbox(overlay_img, bbox_tuple, color="red", width=3, label=label)
            
            # Save result
            out_file = args.output_dir / f"pred_{img_path.name}"
            overlay_img.save(out_file)

    print(f"Done! Results saved to {args.output_dir}")


if __name__ == "__main__":
    main()
