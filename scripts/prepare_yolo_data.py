"""
Convert the PCB dataset to YOLO format for training.
Creates a folder structure:
yolo_dataset/
  images/
    train/
    test/
  labels/
    train/
    test/
  dataset.yaml
"""

from __future__ import annotations

import argparse
import shutil
import sys
import yaml
from pathlib import Path

# Ensure the package is importable
sys.path.append(str(Path(__file__).resolve().parent.parent))

from pcb_cv.data_loader import DatasetConfig, load_dataset, PCBImage, PCB_CLASSES

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare YOLO dataset.")
    parser.add_argument(
        "--data-root",
        type=Path,
        default=Path("data"),
        help="Root directory of the raw dataset.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("yolo_dataset"),
        help="Where to create the YOLO dataset.",
    )
    return parser.parse_args()

def main() -> None:
    args = parse_args()
    
    # 1. Load Data
    config = DatasetConfig(root_dir=args.data_root)
    print(f"Loading dataset from {config.default_dataset_dir}...")
    images = load_dataset(config)
    
    if not images:
        print("No images found.")
        sys.exit(1)

    # 2. Create Directory Structure
    for split in ["train", "test"]:
        (args.output_dir / "images" / split).mkdir(parents=True, exist_ok=True)
        (args.output_dir / "labels" / split).mkdir(parents=True, exist_ok=True)

    # 3. Create Class Mapping
    # Sort classes alphabetically or by some ID to ensure consistency
    # PCB_CLASSES is a dict {char: name}
    # We need a stable ID for YOLO. Let's sort by char code (A, B, C...)
    sorted_chars = sorted(PCB_CLASSES.keys())
    class_map = {char: i for i, char in enumerate(sorted_chars)}
    
    print("Class Mapping:")
    for char, i in class_map.items():
        print(f"  {char}: {i} ({PCB_CLASSES[char]})")

    # 4. Process Images
    print("Processing images...")
    count = 0
    for img in images:
        if not img.bbox:
            continue
            
        split = img.dataset_type
        # Copy image
        src_path = img.path
        dst_image_path = args.output_dir / "images" / split / img.filename
        
        # We can symlink to save space, but copy is safer for some OS/filesystems
        if not dst_image_path.exists():
            shutil.copy2(src_path, dst_image_path)
            
        # Create Label File
        # YOLO format: class_id x_center y_center width height (normalized)
        label_path = args.output_dir / "labels" / split / (img.path.stem + ".txt")
        
        try:
            # get_yolo_bbox returns (class_id, x, y, w, h)
            # using our class_map
            yolo_data = img.get_yolo_bbox(class_map)
            
            # Write to file
            with open(label_path, "w") as f:
                # We only have one object per image in this dataset, but typically we append
                # yolo_data is a tuple
                cls_id, x, y, w, h = yolo_data
                f.write(f"{cls_id} {x:.6f} {y:.6f} {w:.6f} {h:.6f}\n")
                
            count += 1
            if count % 100 == 0:
                print(f"Processed {count} images...", end="\r")
                
        except ValueError as e:
            print(f"Skipping {img.filename}: {e}")
            continue

    print(f"\nProcessed {count} images total.")

    # 5. Create dataset.yaml
    # Ultralytics defines dataset structure in YAML
    # paths can be absolute or relative to where training starts
    # We will use absolute paths to be safe
    
    yaml_content = {
        "path": str(args.output_dir.resolve()),
        "train": "images/train",
        "val": "images/test", # Use test as val for this example, or split train further
        "test": "images/test",
        "names": {i: PCB_CLASSES[char] for char, i in class_map.items()}
    }
    
    yaml_path = args.output_dir / "dataset.yaml"
    with open(yaml_path, "w") as f:
        yaml.dump(yaml_content, f, sort_keys=False)
        
    print(f"Created {yaml_path}")
    print("Ready for training!")

if __name__ == "__main__":
    main()
