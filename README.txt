PCB Computer Vision

This repo provides starter utilities for loading and previewing the MicroPCB dataset.

Quick start
1) Download the dataset manually from Kaggle (frettapper/micropcb-images)
   and unzip it under the data/ directory.
2) Run the preview script:
   python scripts/preview_dataset.py --data-root data --output outputs/dataset_preview.png
   (use --no-overlay-bbox to disable bounding box overlays)
