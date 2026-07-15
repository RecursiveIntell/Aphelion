"""
Dirty region tracking for optimized canvas rendering.

Tracks which regions of the canvas need redrawing, avoiding full repaints.
"""
from dataclasses import dataclass, field
from typing import Optional
from PySide6.QtCore import QRect


@dataclass(slots=True)
class DirtyTracker:
    """
    Tracks dirty (modified) regions for optimized rendering.

    Maintains a list of rectangles that need repainting.
    """
    dirty_rects: list[QRect] = field(default_factory=list)
    is_fully_dirty: bool = False

    def mark_dirty(self, rect: QRect) -> None:
        """
        Mark a region as dirty.

        Args:
            rect: Rectangle to mark as dirty
        """
        if self.is_fully_dirty:
            return  # Already fully dirty

        # Add to dirty rects
        self.dirty_rects.append(rect)

        # If too many dirty rects, mark as fully dirty
        if len(self.dirty_rects) > 50:
            self.mark_fully_dirty()

    def mark_fully_dirty(self) -> None:
        """Mark entire canvas as dirty (full repaint needed)."""
        self.is_fully_dirty = True
        self.dirty_rects.clear()

    def get_dirty_region(self) -> Optional[QRect]:
        """
        Get the bounding rectangle of all dirty regions.

        Returns:
            Bounding QRect or None if no dirty regions
        """
        if self.is_fully_dirty:
            return None  # Caller should do full repaint

        if not self.dirty_rects:
            return None

        # Calculate bounding box of all dirty rects
        bounding = self.dirty_rects[0]
        for rect in self.dirty_rects[1:]:
            bounding = bounding.united(rect)

        return bounding

    def clear(self) -> None:
        """Clear all dirty regions."""
        self.dirty_rects.clear()
        self.is_fully_dirty = False

    def has_dirty_regions(self) -> bool:
        """Check if there are any dirty regions."""
        return self.is_fully_dirty or len(self.dirty_rects) > 0
