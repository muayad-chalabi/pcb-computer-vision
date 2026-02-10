"""Visualization utilities for PCB images."""

from __future__ import annotations

import math
import random
from pathlib import Path
from typing import Iterable

import matplotlib.pyplot as plt
from PIL import Image


def save_image_grid(
    images: Iterable[Path],
    output_path: Path,
    *,
    max_images: int = 9,
    columns: int = 3,
    seed: int | None = 42,
) -> Path:
    """Save a grid of images to disk for quick inspection."""

    image_list = [path for path in images]
    if not image_list:
        raise ValueError("No images found to visualize.")

    if seed is not None:
        random.Random(seed).shuffle(image_list)

    selected = image_list[:max_images]
    rows = math.ceil(len(selected) / columns)

    fig, axes = plt.subplots(rows, columns, figsize=(4 * columns, 4 * rows))
    axes_list = axes.ravel().tolist() if hasattr(axes, "ravel") else [axes]

    for ax, image_path in zip(axes_list, selected, strict=False):
        with Image.open(image_path) as image:
            ax.imshow(image)
        ax.set_title(image_path.name)
        ax.axis("off")

    for ax in axes_list[len(selected) :]:
        ax.axis("off")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
    return output_path
