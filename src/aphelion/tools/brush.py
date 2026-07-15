from PySide6.QtGui import QPainter, QPen, QColor
from PySide6.QtCore import Qt, QPoint, QLine
from .brush_base import BrushBaseTool


class BrushTool(BrushBaseTool):
    """Brush tool with pressure sensitivity and anti-aliased strokes."""

    def __init__(self, document, session):
        super().__init__(document, session)
        self.name = "Brush"

    def _get_color(self) -> QColor:
        """Return the primary color for painting."""
        return self.session.primary_color

    def _get_composition_mode(self) -> QPainter.CompositionMode:
        """Return standard source-over blending."""
        return QPainter.CompositionMode.CompositionMode_SourceOver
