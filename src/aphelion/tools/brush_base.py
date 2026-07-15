"""
Abstract base class for brush-like tools (Brush, Eraser, etc.).

Provides common state management, pressure sensitivity, and command lifecycle.
"""
from abc import abstractmethod
from functools import lru_cache
from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QPainter, QPen, QColor, QImage
from .tool import Tool
from ..core.commands import CanvasCommand


class BrushBaseTool(Tool):
    """
    Base class for tools that paint continuous strokes.

    Subclasses must implement:
    - _get_color(): Return the color to paint with
    - _get_composition_mode(): Return the QPainter composition mode
    """

    def __init__(self, document, session):
        super().__init__(document, session)
        self.is_drawing: bool = False
        self.last_pos: QPoint = QPoint()
        self.current_command: CanvasCommand | None = None
        self.pressure_enabled: bool = True
        self.last_pressure: float = 1.0

    def mouse_press(self, pos: QPoint):
        """Initialize drawing state and create undo command."""
        self.is_drawing = True
        self.last_pos = pos
        self.last_pressure = 1.0

        active_layer = self.document.get_active_layer()
        if active_layer:
            target = self.session.edit_target
            if target == "mask" and not active_layer.mask:
                target = "image"  # Fallback if no mask
            self.current_command = CanvasCommand(active_layer, target=target)

    def tablet_event(self, pos: QPoint, pressure: float):
        """Handle tablet event with pressure sensitivity."""
        if not self.is_drawing:
            return
        self.last_pressure = max(0.1, pressure)
        self._draw_stroke(pos)

    def mouse_move(self, pos: QPoint):
        """Continue drawing stroke."""
        if not self.is_drawing:
            return
        self._draw_stroke(pos)

    def mouse_release(self, pos: QPoint):
        """Finalize stroke and push to history."""
        if self.is_drawing:
            self.is_drawing = False
            if self.current_command:
                self.current_command.capture_after()
                self.document.history.push(self.current_command)
                self.current_command = None

    def _draw_stroke(self, pos: QPoint):
        """Draw a stroke segment from last_pos to pos."""
        active_layer = self.document.get_active_layer()
        if not active_layer:
            return

        target = self.session.edit_target
        target_image = active_layer.image
        if target == "mask" and active_layer.mask:
            target_image = active_layer.mask

        painter = QPainter(target_image)

        # Handle selection clipping
        if self.document.has_selection and hasattr(self.document, '_cached_selection_region'):
            painter.setClipRegion(self.document._cached_selection_region)

        # Set composition mode
        painter.setCompositionMode(self._get_composition_mode())

        # Get pen with pressure-adjusted size
        base_size = self.session.brush_size
        if self.pressure_enabled:
            size = int(base_size * self.last_pressure)
        else:
            size = base_size
        size = max(1, size)

        pen = self._get_pen(size)
        painter.setPen(pen)

        painter.drawLine(self.last_pos, pos)
        painter.end()

        self.last_pos = pos
        self.document.content_changed.emit()

    @lru_cache(maxsize=32)
    def _get_pen(self, size: int) -> QPen:
        """
        Get a pen with the specified size.

        Cached for performance to avoid recreating pens.

        Args:
            size: Pen width in pixels

        Returns:
            Configured QPen
        """
        color = self._get_color()
        pen = QPen(color)
        pen.setWidth(size)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        return pen

    @abstractmethod
    def _get_color(self) -> QColor:
        """Get the color for this tool. Must be implemented by subclasses."""
        ...

    @abstractmethod
    def _get_composition_mode(self) -> QPainter.CompositionMode:
        """Get the QPainter composition mode. Must be implemented by subclasses."""
        ...
