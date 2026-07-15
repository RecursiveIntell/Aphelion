"""
Abstract base class for drag-based tools (Shapes, Gradient, Selection).

Provides common drag state management and command lifecycle.
"""
from abc import abstractmethod
from PySide6.QtCore import QPoint, QRect
from PySide6.QtGui import QPainter
from .tool import Tool
from ..core.commands import CanvasCommand


class DragToolBase(Tool):
    """
    Base class for tools that use drag gestures.

    Provides:
    - start_pos/end_pos state management
    - is_dragging flag
    - Command creation and history management
    - Preview overlay support

    Subclasses must implement:
    - _apply_drag(): Apply the drag operation to the layer/document
    - _draw_preview(): Draw preview overlay during drag (optional)
    """

    def __init__(self, document, session):
        super().__init__(document, session)
        self.start_pos: QPoint | None = None
        self.end_pos: QPoint | None = None
        self.is_dragging: bool = False
        self._current_command: CanvasCommand | None = None

    def mouse_press(self, pos: QPoint):
        """Begin drag operation."""
        self.start_pos = pos
        self.end_pos = pos
        self.is_dragging = True

        # Create undo command if applicable
        layer = self.document.get_active_layer()
        if layer and self._should_create_command():
            self._current_command = CanvasCommand(layer, target=self._get_command_target())

    def mouse_move(self, pos: QPoint):
        """Update drag end position."""
        if self.is_dragging:
            self.end_pos = pos
            self.document.content_changed.emit()

    def mouse_release(self, pos: QPoint):
        """Complete drag operation and apply changes."""
        if not self.is_dragging:
            return

        self.end_pos = pos
        self.is_dragging = False

        # Apply the drag operation
        self._apply_drag()

        # Push command to history if we created one
        if self._current_command:
            self._current_command.capture_after()
            self.document.history.push(self._current_command)
            self._current_command = None

        self.document.content_changed.emit()

        # Cleanup
        self.start_pos = None
        self.end_pos = None

    def draw_overlay(self, painter: QPainter):
        """Draw preview overlay during drag."""
        if self.is_dragging and self.start_pos and self.end_pos:
            self._draw_preview(painter)

    def get_drag_rect(self) -> QRect:
        """Get the normalized rectangle from start to end pos."""
        if not self.start_pos or not self.end_pos:
            return QRect()
        return QRect(self.start_pos, self.end_pos).normalized()

    @abstractmethod
    def _apply_drag(self):
        """
        Apply the drag operation to the layer/document.
        Called on mouse_release after the drag is complete.
        """
        ...

    def _draw_preview(self, painter: QPainter):
        """
        Draw preview overlay during drag. Override in subclasses.
        Default implementation does nothing.
        """
        pass

    def _should_create_command(self) -> bool:
        """
        Whether to create an undo command for this drag.
        Override in subclasses that don't modify layers.
        """
        return True

    def _get_command_target(self) -> str:
        """
        Get the target for the undo command ('image' or 'mask').
        Override in subclasses if needed.
        """
        return self.session.edit_target if self.session else "image"
