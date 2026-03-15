"""Dataset loading helpers for PCB images."""

from __future__ import annotations

<<<<<<< HEAD
import csv
import dataclasses
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".bmp", ".tiff")

# Mapping from first character of filename to class name (as per README.txt)
PCB_CLASSES = {
    'A': 'Raspberry Pi A+',
    'B': 'Arduino Mega 2560 (Blue)',
    'C': 'Arduino Mega 2560 (Black)',
    'D': 'Arduino Mega 2560 (Black and Yellow)',
    'E': 'Arduino Due',
    'F': 'Beaglebone Black',
    'G': 'Arduino Uno (Green)',
    'H': 'Raspberry Pi 3 B+',
    'I': 'Raspberry Pi 1 B+',
    'J': 'Arduino Uno Camera Shield',
    'K': 'Arduino Uno (Black)',
    'L': 'Arduino Uno WiFi Shield',
    'M': 'Arduino Leonardo',
}

ROTATION_CODES = {
    'A': 'Wide left rotation',
    'B': 'Shallow left rotation',
    'C': 'Neutral rotation',
    'D': 'Shallow right rotation',
    'E': 'Wide right rotation',
}


@dataclasses.dataclass(frozen=True)
class PCBImage:
    """Represents a single image record in the PCB dataset."""
    path: Path
    filename: str
    dataset_type: str  # 'train' or 'test'
    bbox: Optional[Tuple[int, int, int, int]] = None  # (Left, Top, Width, Height)
    image_size: Optional[Tuple[int, int]] = None  # (Width, Height)

    @property
    def class_code(self) -> str:
        return self.filename[0]

    @property
    def class_name(self) -> str:
        return PCB_CLASSES.get(self.class_code, "Unknown")

    @property
    def rotation_code(self) -> str:
        return self.filename[1]

    @property
    def rotation_desc(self) -> str:
        return ROTATION_CODES.get(self.rotation_code, "Unknown")

    def get_yolo_bbox(self, class_map: Dict[str, int]) -> Tuple[int, float, float, float, float]:
        """Convert bbox to YOLO format: (class_id, x_center, y_center, width, height) normalized.

        Requires self.image_size to be set.
        """
        if self.bbox is None:
            raise ValueError(f"No bounding box available for {self.filename}")
        if self.image_size is None:
            raise ValueError(f"Image size not available for {self.filename}")

        class_id = class_map.get(self.class_code)
        if class_id is None:
             raise ValueError(f"Class code {self.class_code} not in class_map")

        left, top, w, h = self.bbox
        img_w, img_h = self.image_size

        x_center = (left + w / 2) / img_w
        y_center = (top + h / 2) / img_h
        norm_w = w / img_w
        norm_h = h / img_h

        return (class_id, x_center, y_center, norm_w, norm_h)


@dataclasses.dataclass(frozen=True)
class DatasetConfig:
    """Configuration for locating the PCB dataset."""

    root_dir: Path
=======
import dataclasses
import os
import shutil
import subprocess
from pathlib import Path
from typing import Iterable

DATASET_SLUG = "frettapper/micropcb-images"

IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".bmp", ".tiff")


@dataclasses.dataclass(frozen=True)
class DatasetConfig:
    """Configuration for locating and downloading the PCB dataset."""

    root_dir: Path
    dataset_slug: str = DATASET_SLUG
>>>>>>> main

    @property
    def default_dataset_dir(self) -> Path:
        return self.root_dir / "micropcb-images"


def ensure_dataset(config: DatasetConfig) -> Path:
    """Ensure the dataset is available on disk.

<<<<<<< HEAD
    Returns the dataset directory if found successfully.
=======
    Returns the dataset directory if found or downloaded successfully.
>>>>>>> main
    """

    config.root_dir.mkdir(parents=True, exist_ok=True)
    dataset_dir = config.default_dataset_dir
<<<<<<< HEAD
    if _has_images(dataset_dir) or (dataset_dir / "train_bboxes.csv").exists():
=======
    if _has_images(dataset_dir):
>>>>>>> main
        return dataset_dir

    if _has_images(config.root_dir):
        return config.root_dir

<<<<<<< HEAD
    raise FileNotFoundError(
        "Dataset not found. Place the extracted dataset under "
        f"{config.root_dir} (or {dataset_dir}) and try again."
    )


def load_dataset(config: DatasetConfig) -> List[PCBImage]:
    """Load the dataset including bounding boxes and metadata."""
    dataset_dir = ensure_dataset(config)
    
    # Load raw image paths first
    image_files = find_images(dataset_dir)
    image_map = {p.name: p for p in image_files}
    
    records: List[PCBImage] = []

    # Load sizes
    size_map: Dict[str, Tuple[int, int]] = {}
    for split_name in ["train", "test"]:
        size_csv = dataset_dir / f"{split_name}_sizes.csv"
        if size_csv.exists():
             with open(size_csv, "r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Robust filename extraction
                    filename = row.get("Image", row.get("Image "))
                    if not filename:
                        for k, v in row.items():
                             if "image" in k.lower():
                                 filename = v
                                 break
                    
                    if filename:
                        try:
                            w = int(row["Width"])
                            h = int(row["Height"])
                            size_map[filename] = (w, h)
                        except (ValueError, KeyError):
                            pass

    # Process train and test CSVs for bboxes
    for split_name in ["train", "test"]:
        bbox_csv = dataset_dir / f"{split_name}_bboxes.csv"
        
        if not bbox_csv.exists():
            print(f"Warning: {bbox_csv} not found. Skipping {split_name} metadata.")
            continue
            
        with open(bbox_csv, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                filename = row.get("Image", row.get("Image "))
                if not filename:
                    for k, v in row.items():
                         if "image" in k.lower():
                             filename = v
                             break
                
                if not filename:
                    continue

                if filename not in image_map:
                    continue
                
                try:
                    left = int(row["Left"])
                    top = int(row["Top"])
                    width = int(row["Width"])
                    height = int(row["Height"])
                    bbox = (left, top, width, height)
                except (ValueError, KeyError):
                    print(f"Warning: Could not parse bbox for {filename}")
                    bbox = None

                records.append(PCBImage(
                    path=image_map[filename],
                    filename=filename,
                    dataset_type=split_name,
                    bbox=bbox,
                    image_size=size_map.get(filename)
                ))
    
    # If no CSVs matched, maybe just return raw images?
    if not records and image_files:
        print("Warning: No metadata found matching images. Returning raw images as records without bboxes.")
        for p in image_files:
             records.append(PCBImage(
                path=p,
                filename=p.name,
                dataset_type="unknown",
            ))

    return records


=======
    kaggle_path = shutil.which("kaggle")
    if kaggle_path is None:
        raise FileNotFoundError(
            "Dataset not found and Kaggle CLI is unavailable. "
            "Install kaggle and configure credentials, or place the dataset under "
            f"{config.root_dir}."
        )

    _download_dataset(config, kaggle_path)

    if _has_images(dataset_dir):
        return dataset_dir
    if _has_images(config.root_dir):
        return config.root_dir

    raise FileNotFoundError(
        "Dataset download completed but images were not found. "
        "Check the extracted directory structure under "
        f"{config.root_dir}."
    )


>>>>>>> main
def find_images(root_dir: Path) -> list[Path]:
    """Find image files under a root directory."""

    if not root_dir.exists():
        return []
    images: list[Path] = []
    for extension in IMAGE_EXTENSIONS:
        images.extend(root_dir.rglob(f"*{extension}"))
    return sorted(images)


<<<<<<< HEAD
=======
def _download_dataset(config: DatasetConfig, kaggle_path: str) -> None:
    env = os.environ.copy()
    env.setdefault("KAGGLE_CONFIG_DIR", str(Path.home() / ".kaggle"))
    command = [
        kaggle_path,
        "datasets",
        "download",
        "-d",
        config.dataset_slug,
        "-p",
        str(config.root_dir),
        "--unzip",
    ]
    subprocess.run(command, check=True, env=env)


>>>>>>> main
def _has_images(path: Path) -> bool:
    return any(path.rglob(f"*{extension}") for extension in IMAGE_EXTENSIONS)


def iter_images(images: Iterable[Path]) -> Iterable[Path]:
    """Yield only image paths that exist on disk."""

    for image in images:
        if image.exists():
            yield image
