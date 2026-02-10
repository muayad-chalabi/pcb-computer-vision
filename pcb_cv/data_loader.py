"""Dataset loading helpers for PCB images."""

from __future__ import annotations

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

    @property
    def default_dataset_dir(self) -> Path:
        return self.root_dir / "micropcb-images"


def ensure_dataset(config: DatasetConfig) -> Path:
    """Ensure the dataset is available on disk.

    Returns the dataset directory if found or downloaded successfully.
    """

    config.root_dir.mkdir(parents=True, exist_ok=True)
    dataset_dir = config.default_dataset_dir
    if _has_images(dataset_dir):
        return dataset_dir

    if _has_images(config.root_dir):
        return config.root_dir

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


def find_images(root_dir: Path) -> list[Path]:
    """Find image files under a root directory."""

    if not root_dir.exists():
        return []
    images: list[Path] = []
    for extension in IMAGE_EXTENSIONS:
        images.extend(root_dir.rglob(f"*{extension}"))
    return sorted(images)


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


def _has_images(path: Path) -> bool:
    return any(path.rglob(f"*{extension}") for extension in IMAGE_EXTENSIONS)


def iter_images(images: Iterable[Path]) -> Iterable[Path]:
    """Yield only image paths that exist on disk."""

    for image in images:
        if image.exists():
            yield image
