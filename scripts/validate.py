import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from ultralytics import YOLO

# Load the model
model = YOLO("runs/detect/runs/train/pcb_yolo/weights/best.pt")

# Validate the model
metrics = model.val()
print(metrics.box.map)  # mAP50-95