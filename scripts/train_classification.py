"""
Fine-tune a YOLO classification model on the PCB dataset.
"""

import argparse
import shutil
import sys
from pathlib import Path

try:
    from ultralytics import YOLO
except ImportError:
    print("Error: 'ultralytics' package not found. Please install it with 'pip install ultralytics'.")
    sys.exit(1)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train YOLO classification model on PCB dataset.")
    parser.add_argument(
        "--data",
        type=Path,
        default=Path("yolo_classification_dataset"),
        help="Path to classification dataset directory.",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="yolov8n-cls.pt",
        help="Base classification model (e.g., yolov8n-cls.pt).",
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=10,
        help="Number of training epochs.",
    )
    parser.add_argument(
        "--batch",
        type=int,
        default=16,
        help="Batch size.",
    )
    parser.add_argument(
        "--imgsz",
        type=int,
        default=224,
        help="Image size.",
    )
    parser.add_argument(
        "--device",
        default="",
        help="Device to run on, i.e. 0 or 0,1,2,3 or cpu.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    
    data_path = args.data.resolve()
    if not data_path.exists():
        print(f"Error: Dataset directory not found at {data_path}")
        print("Did you run 'scripts/prepare_classification_data.py'?")
        sys.exit(1)

    print(f"Loading model {args.model}...")
    model = YOLO(args.model)

    import torch
    if not torch.cuda.is_available() and (not args.device or args.device == "cpu"):
        print("\n" + "="*60)
        print("WARNING: Training on CPU detected.")
        print("="*60 + "\n")
    elif torch.cuda.is_available():
        print(f"CUDA is available: {torch.cuda.get_device_name(0)}")

    print("Starting training...")
    # Train the model
    results = model.train(
        data=str(data_path),
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        device=args.device,
        project="runs/classify",
        name="pcb_classify",
        workers=0,  # Windows compatibility
        exist_ok=True,
    )
    
    # Save best model reference
    best_weights = Path("runs/classify/pcb_classify/weights/best.pt")
    if best_weights.exists():
        target_path = Path("yolo") / f"{Path(args.model).stem}_pcb_cls.pt"
        target_path.parent.mkdir(exist_ok=True)
        
        print(f"Copying best model to {target_path}...")
        shutil.copy2(best_weights, target_path)
        print("Training complete!")
    else:
        print("Warning: Could not find best.pt to copy.")


if __name__ == "__main__":
    main()
