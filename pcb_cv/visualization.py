"""Visualization utilities for PCB images."""

from __future__ import annotations

import math
import random
from pathlib import Path
<<<<<<< HEAD
from typing import Any, Callable, Iterable, Union

import matplotlib.pyplot as plt
from PIL import Image, ImageDraw
from PIL import ImageFont



def save_image_grid(
    items: Iterable[Any],
    output_path: Path,
    *,
    get_image_path: Callable[[Any], Path] = lambda x: x if isinstance(x, Path) else x.path,
    get_title: Callable[[Any], str] | None = None,
    max_images: int = 9,
    columns: int = 3,
    overlay: Callable[[Image.Image, Any], Image.Image] | None = None,
    seed: int | None = 42,
) -> Path:
    """Save a grid of images to disk for quick inspection.
    
    Args:
        items: List of items to visualize (Paths, or objects like PCBImage).
        output_path: Where to save the grid.
        get_image_path: Function to extract Path from an item. Defaults to identity or .path attr.
        get_title: Function to extract title from an item. Defaults to filename.
        max_images: Max number of images.
        columns: Grid columns.
        overlay: Optional function to draw on the PIL image. Receives (image, item).
        seed: Random seed for shuffling.
    """

    item_list = list(items)
    if not item_list:
        raise ValueError("No items found to visualize.")

    if seed is not None:
        random.Random(seed).shuffle(item_list)

    selected = item_list[:max_images]
    rows = math.ceil(len(selected) / columns)

    # Handle single image case or small sets
    if rows == 0:
        return output_path

    fig, axes = plt.subplots(rows, columns, figsize=(4 * columns, 4 * rows))
    
    # Ensure axes is always a list/array we can zip
    if rows == 1 and columns == 1:
        axes_list = [axes]
    else:
        axes_list = axes.ravel().tolist()

    for ax, item in zip(axes_list, selected):
        image_path = get_image_path(item)
        try:
            with Image.open(image_path) as image:
                if overlay is not None:
                    image = overlay(image, item)
                ax.imshow(image)
                
                if get_title:
                    ax.set_title(get_title(item))
                else:
                    ax.set_title(image_path.name)
        except Exception as e:
            print(f"Error loading {image_path}: {e}")
            ax.text(0.5, 0.5, "Error", ha='center', va='center')
        
        ax.axis("off")

    # Turn off remaining axes
    for ax in axes_list[len(selected):]:
=======
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
>>>>>>> main
        ax.axis("off")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
    return output_path
<<<<<<< HEAD


def overlay_bbox(
    image: Image.Image,
    bbox: tuple[int, int, int, int],  # Left, Top, Width, Height
    *,
    color: str = "lime",
    width: int = 3,
    label: str | None = None
) -> Image.Image:
    """Return a copy of the image with a bounding box overlay."""

    overlay_image = image.copy()
    draw = ImageDraw.Draw(overlay_image)
    
    left, top, w, h = bbox
    # PIL rectangle is [x0, y0, x1, y1]
    right = left + w
    bottom = top + h
    
    draw.rectangle([left, top, right, bottom], outline=color, width=width)
    
    if label:
        # Load a font (try default or fallback)
        font_size = 40
        try:
            # Try to load a font, preferably arial or similar
            font = ImageFont.truetype("arial.ttf", font_size)
        except OSError:
            try:
                 font = ImageFont.truetype("DejaVuSans.ttf", font_size)
            except OSError:
                 font = ImageFont.load_default()

        # Calculate text size
        if hasattr(draw, "textbbox"):
             left_text, top_text, right_text, bottom_text = draw.textbbox((0, 0), label, font=font)
             text_width = right_text - left_text
             text_height = bottom_text - top_text
        else:
             text_width, text_height = draw.textsize(label, font=font)

        # Position text
        text_x = left
        text_y = top - text_height - 5
        if text_y < 0:
            text_y = top + 5

        # Draw background rectangle
        draw.rectangle(
            [text_x, text_y, text_x + text_width + 4, text_y + text_height + 4],
            fill=color
        )
        
        # Draw text (white or black depending on color? For now just white or black fixed)
        text_color = "black" if color in ["lime", "yellow", "cyan"] else "white"
        draw.text((text_x + 2, text_y + 2), label, fill=text_color, font=font)
        
    return overlay_image


def overlay_item_bbox(
    image: Image.Image,
    item: Any,
    *,
    color: str = "lime",
    width: int = 3,
) -> Image.Image:
    """Adapter to overlay bbox from a PCBImage-like object."""
    if hasattr(item, "bbox") and item.bbox:
        return overlay_bbox(image, item.bbox, color=color, width=width)
    return image
=======
>>>>>>> main
