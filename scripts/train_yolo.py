"""
Fine-tune a YOLO model on the PCB dataset.
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
    parser = argparse.ArgumentParser(description="Train YOLO model on PCB dataset.")
    parser.add_argument(
        "--data",
        type=Path,
        default=Path("yolo_dataset/dataset.yaml"),
        help="Path to dataset.yaml.",
    )
    parser.add_argument(
        "--model",
        type=Path,
        default=Path("yolo/yolo26n.pt"),
        help="Path to base model.",
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=50,
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
        default=640,
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
    
    if not args.data.exists():
        print(f"Error: Dataset config not found at {args.data}")
        print("Did you run 'scripts/prepare_yolo_data.py'?")
        sys.exit(1)

    print(f"Loading model {args.model}...")
    # Load a model
    model = YOLO(str(args.model))  # load a pretrained model (recommended for training)

    # Check device and warn if using CPU for large models
    # Check device and warn if using CPU for large models
    # Ultralytics auto-selects GPU if available, so we check torch availability
    import torch
    if not torch.cuda.is_available() and (not args.device or args.device == "cpu"):
        print("\n" + "="*60)
        print("WARNING: Training on CPU detected.")
        if "x.pt" in str(args.model) or "l.pt" in str(args.model) or "m.pt" in str(args.model):
            print(f"You are training a large model ({args.model.name}) on CPU. This will be extremely slow.")
            print("Consider using a smaller model (e.g., yolo11n.pt or yolo11s.pt) for testing.")
            print("Or use a GPU if available.")
        print("="*60 + "\n")
    else:
        print(f"CUDA is available: {torch.cuda.get_device_name(0)}")

    print("Starting training...")
    # Train the model
    results = model.train(
        data=str(args.data.resolve()),
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        device=args.device,
        project="runs/train",
        name="pcb_yolo",
        workers=0,  # Single worker to avoid PyTorch Windows multiprocessing issues
        exist_ok=True, # Overwrite existing experiment
    )
    
    # Save the final model to the requested location
    # The best model is typically at runs/train/pcb_yolo/weights/best.pt
    best_weights = Path("runs/detect/runs/train/pcb_yolo/weights/best.pt")
    if best_weights.exists():
        original_name = args.model.stem
        target_path = args.model.parent / f"{original_name}_ft.pt"
        
        print(f"Copying best model to {target_path}...")
        shutil.copy2(best_weights, target_path)
        print("Training complete!")
    else:
        print("Warning: Could not find best.pt to copy.")


if __name__ == "__main__":
    main()
