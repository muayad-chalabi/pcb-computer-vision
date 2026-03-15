PCB Computer Vision

This repo provides starter utilities for loading and previewing the MicroPCB dataset.

Quick start
1) Download the dataset manually from Kaggle (frettapper/micropcb-images)
   and unzip it under the data/ directory.
2) Run the preview script:
   python scripts/preview_dataset.py --data-root data --output outputs/dataset_preview.png
   (use --no-overlay-bbox to disable bounding box overlays)

Transfer Learning (YOLO Fine-tuning)
------------------------------------
This repository supports fine-tuning a YOLO model on the PCB dataset.
The process involves replacing the original classification head (trained on 80 COCO classes)
with a new head for our 13 PCB component classes. The backbone and other layers
are fine-tuned to adapt to this specific domain.

1) Prepare the Data:
   Convert the dataset to YOLO format (images/labels folders and dataset.yaml):
   python scripts/prepare_yolo_data.py

2) Train the Model:
   Start fine-tuning (default model: yolo/yolo26x.pt):
   python scripts/train_yolo.py --epochs 50

   The final model will be saved to:
   yolo/yolo26x_ft.pt

3) Run Inference with Fine-tuned Model:
   python scripts/test_yolo_inference.py --model-path yolo/yolo26x_ft.pt

Transfer Learning (YOLO Classification Fine-tuning)
---------------------------------------------------
This supports fine-tuning a YOLO classification model on the PCB dataset.

1) Prepare the Classification Data:
   Creates a YOLO classification dataset structure from the detection dataset:
   python scripts/prepare_classification_data.py

2) Train the Classification Model:
   Start fine-tuning (default model: yolov8n-cls.pt):
   python scripts/train_classification.py --epochs 10

Out-of-Distribution (OOD) Testing
---------------------------------
Run YOLO inference on out-of-dataset images (e.g. your own photos), filtering by a keyword like 'rgb':
python scripts/test_ood.py --model yolo/yolo26x_ft.pt --source-dir path/to/ood_images

Rectangle Detection (Classical CV & Depth)
------------------------------------------
Detect rectangles in an image and generate confidence scores based on orthogonality, aspect ratio, edge strength, and rectangularity. If an aligned depth map is provided, depth-based features (planarity and elevation) are actively used to improve detection in low contrast areas.

Run the detector:
python scripts/detect_rectangles.py --source data/zed_snapshots
