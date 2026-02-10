PCB Computer Vision

This repo provides starter utilities for loading and previewing the MicroPCB dataset.

Quick start
1) Download the dataset manually from Kaggle (frettapper/micropcb-images)
   and unzip it under the data/ directory, OR configure the Kaggle CLI.
2) Run the preview script:
   python scripts/preview_dataset.py --data-root data --output outputs/dataset_preview.png

If the Kaggle CLI is installed and configured, the script will download and unzip
 the dataset automatically.
