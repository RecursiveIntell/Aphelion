from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QPainter, QColor, QLinearGradient
from .tool import Tool
from ..core.document import Document
from ..core.commands import CanvasCommand
from ..utils.flood_fill import flood_fill_mask

class PaintBucketTool(Tool):
    def __init__(self, document, session):
        super().__init__(document, session)
        self.name = "Paint Bucket"

    @property
    def tolerance(self):
        """Get tolerance from session."""
        return self.session.tolerance if self.session else 32

    def mouse_press(self, pos: QPoint):
        layer = self.document.get_active_layer()
        if not layer: return
        
        # Check bounds
        if pos.x() < 0 or pos.x() >= layer.image.width() or pos.y() < 0 or pos.y() >= layer.image.height():
            return
        
        # Prepare undo
        cmd = CanvasCommand(layer)
        
        # Use shared flood fill implementation
        fill_color = self.session.primary_color
        mask = flood_fill_mask(layer.image, pos, self.tolerance, use_alpha=False)

        # Apply fill color to masked region
        width = layer.image.width()
        height = layer.image.height()
        for y in range(height):
            for x in range(width):
                if mask.pixelColor(x, y).red() == 255:
                    layer.image.setPixelColor(x, y, fill_color)
        
        cmd.capture_after()
        self.document.history.push(cmd)
        self.document.content_changed.emit()

    def mouse_move(self, pos: QPoint):
        pass

    def mouse_release(self, pos: QPoint):
        pass

