from PySide6.QtGui import QPainter, QPen, QColor
from PySide6.QtCore import Qt, QPoint
from .brush_base import BrushBaseTool


class EraserTool(BrushBaseTool):
    """Eraser tool with pressure sensitivity."""

    def __init__(self, document, session):
        super().__init__(document, session)
        self.name = "Eraser"

    def _get_color(self) -> QColor:
        """Return opaque black color (alpha will be used for DestinationOut)."""
        return QColor(0, 0, 0, 255)

    def _get_composition_mode(self) -> QPainter.CompositionMode:
        """Return DestinationOut to erase pixels."""
        return QPainter.CompositionMode.CompositionMode_DestinationOut
