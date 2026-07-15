"""
Central type aliases and protocols for Aphelion.

This module provides type-safe definitions used throughout the codebase.
"""

from typing import TypeAlias, Protocol, Union, Any
from PySide6.QtCore import QPoint
from PySide6.QtGui import QImage, QPainter
import numpy as np
from numpy.typing import NDArray

# NumPy array type aliases
ImageArray: TypeAlias = NDArray[np.uint8]  # (H, W, 4) BGRA format
MaskArray: TypeAlias = NDArray[np.uint8]   # (H, W) grayscale format

# Qt type aliases
BlendMode: TypeAlias = QPainter.CompositionMode
EffectConfig: TypeAlias = dict[str, Union[int, float, bool, str]]

# Protocol definitions for duck typing
class ToolProtocol(Protocol):
    """Protocol for tool implementations."""
    name: str
    icon: str
    cursor: str

    def mouse_press(self, event: Any, canvas: Any) -> None:
        """Handle mouse press event."""
        ...

    def mouse_move(self, event: Any, canvas: Any) -> None:
        """Handle mouse move event."""
        ...

    def mouse_release(self, event: Any, canvas: Any) -> None:
        """Handle mouse release event."""
        ...


class EffectProtocol(Protocol):
    """Protocol for effect implementations."""
    name: str
    category: str

    def apply(self, image: QImage, config: EffectConfig) -> QImage:
        """Apply effect to image with given configuration."""
        ...

    def create_dialog(self, parent: Any) -> tuple[bool, EffectConfig]:
        """Create configuration dialog, return (accepted, config)."""
        ...


class RenderableProtocol(Protocol):
    """Protocol for objects that can be rendered."""

    def render(self) -> QImage:
        """Render object to QImage."""
        ...
