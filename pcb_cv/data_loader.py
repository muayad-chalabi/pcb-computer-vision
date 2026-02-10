"""Dataset loading helpers for PCB images."""

from __future__ import annotations

import dataclasses
from pathlib import Path
from typing import Iterable

IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".bmp", ".tiff")


@dataclasses.dataclass(frozen=True)
class DatasetConfig:
    """Configuration for locating the PCB dataset."""

    root_dir: Path

    @property
    def default_dataset_dir(self) -> Path:
        return self.root_dir / "micropcb-images"


def ensure_dataset(config: DatasetConfig) -> Path:
    """Ensure the dataset is available on disk.

    Returns the dataset directory if found successfully.
    """

    config.root_dir.mkdir(parents=True, exist_ok=True)
    dataset_dir = config.default_dataset_dir
    if _has_images(dataset_dir):
        return dataset_dir

    if _has_images(config.root_dir):
        return config.root_dir

    raise FileNotFoundError(
        "Dataset not found. Place the extracted dataset under "
        f"{config.root_dir} (or {dataset_dir}) and try again."
    )


def find_images(root_dir: Path) -> list[Path]:
    """Find image files under a root directory."""

    if not root_dir.exists():
        return []
    images: list[Path] = []
    for extension in IMAGE_EXTENSIONS:
        images.extend(root_dir.rglob(f"*{extension}"))
    return sorted(images)


def _has_images(path: Path) -> bool:
    return any(path.rglob(f"*{extension}") for extension in IMAGE_EXTENSIONS)


def iter_images(images: Iterable[Path]) -> Iterable[Path]:
    """Yield only image paths that exist on disk."""

    for image in images:
        if image.exists():
            yield image
