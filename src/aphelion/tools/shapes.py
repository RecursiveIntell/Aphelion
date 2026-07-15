from PySide6.QtCore import QPoint, QRect, Qt
from PySide6.QtGui import QPainter, QColor, QPen, QBrush
from .drag_base import DragToolBase
from ..core.document import Document


class LineTool(DragToolBase):
    """Line drawing tool with drag-to-draw interface."""

    def __init__(self, document, session):
        super().__init__(document, session)
        self.name = "Line/Curve"

    def _apply_drag(self):
        """Apply the line to the layer."""
        layer = self.document.get_active_layer()
        if not layer or not self.start_pos or not self.end_pos:
            return

        painter = QPainter(layer.image)
        if self.document.has_selection:
            painter.setClipRegion(self.document.get_selection_region())

        pen_color = self.session.primary_color
        painter.setPen(QPen(pen_color, 2))
        painter.drawLine(self.start_pos, self.end_pos)
        painter.end()

    def _draw_preview(self, painter: QPainter):
        """Draw preview line during drag."""
        painter.setPen(QPen(Qt.black, 2))
        painter.drawLine(self.start_pos, self.end_pos)

class ShapesTool(DragToolBase):
    """Shape drawing tool (rectangle, ellipse, rounded rectangle)."""

    def __init__(self, document, session):
        super().__init__(document, session)
        self.name = "Shapes"
        self.shape_type = "Rectangle"  # Rectangle, Ellipse, RoundedRect
        self.fill_mode = "Outline"  # Outline, Fill, Both

    def _apply_drag(self):
        """Apply the shape to the layer."""
        layer = self.document.get_active_layer()
        if not layer or not self.start_pos or not self.end_pos:
            return

        painter = QPainter(layer.image)
        if self.document.has_selection:
            painter.setClipRegion(self.document.get_selection_region())

        rect = self.get_drag_rect()

        # Configure pen and brush
        p_color = self.session.primary_color
        s_color = self.session.secondary_color
        pen = QPen(p_color, 2)
        brush = QBrush(s_color)

        match self.fill_mode:
            case "Outline":
                painter.setPen(pen)
                painter.setBrush(Qt.NoBrush)
            case "Fill":
                painter.setPen(Qt.NoPen)
                painter.setBrush(brush)
            case _:  # "Both"
                painter.setPen(pen)
                painter.setBrush(brush)

        # Draw shape
        match self.shape_type:
            case "Rectangle":
                painter.drawRect(rect)
            case "Ellipse":
                painter.drawEllipse(rect)
            case "RoundedRect":
                painter.drawRoundedRect(rect, 10, 10)

        painter.end()

    def _draw_preview(self, painter: QPainter):
        """Draw preview shape during drag."""
        rect = self.get_drag_rect()
        painter.setPen(Qt.black)
        painter.setBrush(Qt.NoBrush)

        match self.shape_type:
            case "Rectangle":
                painter.drawRect(rect)
            case "Ellipse":
                painter.drawEllipse(rect)
