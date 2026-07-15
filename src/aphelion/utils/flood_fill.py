"""
Unified flood fill implementation for Aphelion.

Provides efficient flood fill algorithm used by both Fill tool and Magic Wand selection.
"""
from collections import deque
from PySide6.QtCore import QPoint
from PySide6.QtGui import QImage, QColor
import numpy as np


def flood_fill_mask(
    image: QImage,
    seed: QPoint,
    tolerance: int = 0,
    use_alpha: bool = False
) -> QImage:
    """
    Perform flood fill and return an Alpha8 mask of the filled region.

    Uses BFS with early-out and efficient pixel access via QImage.pixel().

    Args:
        image: Source image to analyze
        seed: Starting point for flood fill
        tolerance: Color difference tolerance (0-255)
        use_alpha: If True, include alpha channel in color distance calculation

    Returns:
        QImage in Format_Alpha8 where filled pixels are white (255)
    """
    width = image.width()
    height = image.height()

    # Bounds check
    sx, sy = seed.x(), seed.y()
    if not (0 <= sx < width and 0 <= sy < height):
        # Return empty mask
        mask = QImage(width, height, QImage.Format.Format_Alpha8)
        mask.fill(0)
        return mask

    # Get target color at seed point
    target_color = image.pixelColor(sx, sy)
    tr, tg, tb, ta = target_color.red(), target_color.green(), target_color.blue(), target_color.alpha()

    # Create output mask
    mask = QImage(width, height, QImage.Format.Format_Alpha8)
    mask.fill(0)

    # BFS flood fill
    queue = deque([(sx, sy)])
    visited = set()
    visited.add((sx, sy))

    # Set seed pixel in mask
    mask.setPixelColor(sx, sy, QColor(255, 255, 255))

    # Neighbor offsets
    neighbors = [(0, 1), (0, -1), (1, 0), (-1, 0)]

    while queue:
        x, y = queue.popleft()

        for dx, dy in neighbors:
            nx, ny = x + dx, y + dy

            # Bounds check
            if not (0 <= nx < width and 0 <= ny < height):
                continue

            # Skip if already visited
            if (nx, ny) in visited:
                continue

            visited.add((nx, ny))

            # Fast pixel access using pixel() -> int (ARGB32)
            c_int = image.pixel(nx, ny)
            cr = (c_int >> 16) & 0xFF
            cg = (c_int >> 8) & 0xFF
            cb = c_int & 0xFF

            # Calculate color distance (Chebyshev distance)
            if use_alpha:
                ca = (c_int >> 24) & 0xFF
                dist = max(abs(cr - tr), abs(cg - tg), abs(cb - tb), abs(ca - ta))
            else:
                dist = max(abs(cr - tr), abs(cg - tg), abs(cb - tb))

            # Add to fill region if within tolerance
            if dist <= tolerance:
                mask.setPixelColor(nx, ny, QColor(255, 255, 255))
                queue.append((nx, ny))

    return mask


def flood_fill_image(
    image: QImage,
    seed: QPoint,
    fill_color: QColor,
    tolerance: int = 0
):
    """
    Perform in-place flood fill on an image.

    Args:
        image: Image to fill (modified in-place)
        seed: Starting point for flood fill
        fill_color: Color to fill with
        tolerance: Color difference tolerance (0-255)
    """
    mask = flood_fill_mask(image, seed, tolerance, use_alpha=False)

    # Apply fill color to masked region
    width = image.width()
    height = image.height()

    for y in range(height):
        for x in range(width):
            if mask.pixelColor(x, y).red() == 255:
                image.setPixelColor(x, y, fill_color)
