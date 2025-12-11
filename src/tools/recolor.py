"""
Recolor Tool for Aphelion.
Replaces colors matching the clicked color with the primary color.
"""
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QColor
from .tool import Tool
from ..core.commands import CanvasCommand


class RecolorTool(Tool):
    name = "Recolor"
    
    def __init__(self, document, session):
        super().__init__(document, session)
        self.tolerance = 32
        self.drawing = False
        self._cmd = None
        self._target_color = None
    
    def set_tolerance(self, value):
        """Set color matching tolerance (0-255)"""
        self.tolerance = max(0, min(255, value))
    
    def mouse_press(self, pos: QPoint):
        if not self.document:
            return
        layer = self.document.get_active_layer()
        if not layer:
            return
            
        self.drawing = True
        self._cmd = CanvasCommand(layer)
        
        x, y = pos.x(), pos.y()
        if 0 <= x < layer.image.width() and 0 <= y < layer.image.height():
            self._target_color = layer.image.pixelColor(x, y)
        
        self._recolor_at(pos, layer)
    
    def mouse_move(self, pos: QPoint):
        if not self.drawing or not self.document:
            return
        layer = self.document.get_active_layer()
        if layer:
            self._recolor_at(pos, layer)
    
    def mouse_release(self, pos: QPoint):
        if not self.drawing or not self.document:
            return
            
        self.drawing = False
        
        if self._cmd:
            self._cmd.capture_after()
            self.document.history.push(self._cmd)
        
        self.document.content_changed.emit()
        self._target_color = None
    
    def _recolor_at(self, pos: QPoint, layer):
        """Recolor pixels near the given position"""
        if not self._target_color:
            return
            
        image = layer.image
        x, y = pos.x(), pos.y()
        
        if x < 0 or x >= image.width() or y < 0 or y >= image.height():
            return
        
        replacement = self.session.primary_color
        brush_size = 10
        
        for dy in range(-brush_size, brush_size + 1):
            for dx in range(-brush_size, brush_size + 1):
                px = x + dx
                py = y + dy
                
                if px < 0 or px >= image.width() or py < 0 or py >= image.height():
                    continue
                
                if dx*dx + dy*dy > brush_size*brush_size:
                    continue
                
                pixel = image.pixelColor(px, py)
                
                if self._color_matches(pixel, self._target_color):
                    new_color = QColor(
                        replacement.red(),
                        replacement.green(),
                        replacement.blue(),
                        pixel.alpha()
                    )
                    image.setPixelColor(px, py, new_color)
    
    def _color_matches(self, c1: QColor, c2: QColor) -> bool:
        """Check if two colors match within tolerance"""
        dr = abs(c1.red() - c2.red())
        dg = abs(c1.green() - c2.green())
        db = abs(c1.blue() - c2.blue())
        return dr <= self.tolerance and dg <= self.tolerance and db <= self.tolerance
