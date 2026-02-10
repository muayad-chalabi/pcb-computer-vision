"""Visualization utilities for PCB images."""

from __future__ import annotations

import math
import random
from pathlib import Path
from typing import Callable, Iterable

import matplotlib.pyplot as plt
from PIL import Image, ImageDraw


def save_image_grid(
    images: Iterable[Path],
    output_path: Path,
    *,
    max_images: int = 9,
    columns: int = 3,
    overlay: Callable[[Image.Image], Image.Image] | None = None,
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
            if overlay is not None:
                image = overlay(image)
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


def overlay_bbox(
    image: Image.Image,
    bbox: tuple[int, int, int, int],
    *,
    color: str = "lime",
    width: int = 3,
) -> Image.Image:
    """Return a copy of the image with a bounding box overlay."""

    overlay_image = image.copy()
    draw = ImageDraw.Draw(overlay_image)
    draw.rectangle(bbox, outline=color, width=width)
    return overlay_image


def overlay_full_image_bbox(
    image: Image.Image,
    *,
    color: str = "lime",
    width: int = 3,
) -> Image.Image:
    """Overlay a bounding box around the full image extent."""

    width_px, height_px = image.size
    bbox = (0, 0, max(width_px - 1, 0), max(height_px - 1, 0))
    return overlay_bbox(image, bbox, color=color, width=width)
