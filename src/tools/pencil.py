from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QPainter, QColor
from .tool import Tool
from ..core.commands import CanvasCommand


class PencilTool(Tool):
    """Pencil tool - 1px hard-edge drawing with no anti-aliasing."""
    
    def __init__(self, document, session):
        super().__init__(document, session)
        self.name = "Pencil"
        self.is_drawing = False
        self.last_pos = None
        self.current_command = None
    
    def mouse_press(self, pos: QPoint):
        self.is_drawing = True
        self.last_pos = pos
        
        layer = self.document.get_active_layer()
        if layer:
            self.current_command = CanvasCommand(layer)
            # Draw single pixel on press
            self._draw_pixel(layer, pos)
    
    def mouse_move(self, pos: QPoint):
        if not self.is_drawing:
            return
        
        layer = self.document.get_active_layer()
        if not layer:
            return
        
        # Bresenham's line algorithm for pixel-perfect lines
        self._draw_line(layer, self.last_pos, pos)
        self.last_pos = pos
        self.document.content_changed.emit()
    
    def mouse_release(self, pos: QPoint):
        if self.is_drawing and self.current_command:
            self.current_command.capture_after()
            self.document.history.push(self.current_command)
            self.current_command = None
        self.is_drawing = False
    
    def _draw_pixel(self, layer, pos: QPoint):
        """Draw a single pixel."""
        if 0 <= pos.x() < layer.image.width() and 0 <= pos.y() < layer.image.height():
            # Check selection
            if self.document.has_selection:
                region = self.document.get_selection_region()
                if not region.contains(pos):
                    return
            layer.image.setPixelColor(pos, self.session.primary_color)
            self.document.content_changed.emit()
    
    def _draw_line(self, layer, p1: QPoint, p2: QPoint):
        """Bresenham's line algorithm for pixel-perfect lines."""
        x1, y1 = p1.x(), p1.y()
        x2, y2 = p2.x(), p2.y()
        
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx - dy
        
        while True:
            self._draw_pixel(layer, QPoint(x1, y1))
            
            if x1 == x2 and y1 == y2:
                break
            
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x1 += sx
            if e2 < dx:
                err += dx
                y1 += sy
