"""Smudge Tool - Push and blend pixels like finger painting."""
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QImage, QColor, QPainter, QPen
from .tool import Tool
from ..core.commands import CanvasCommand


class SmudgeTool(Tool):
    """Smudge pixels by pushing and blending colors."""
    name = "Smudge"
    icon = "brush"  # Reuse brush icon for now
    shortcut = "U"
    
    def __init__(self, session):
        super().__init__(session)
        self._drawing = False
        self._last_pos = None
        self._original_image = None
        self._strength = 0.5  # How much to blend (0-1)
        
    def activate(self):
        pass
        
    def deactivate(self):
        pass
    
    def mouse_press(self, event, canvas):
        if event.button() == Qt.MouseButton.LeftButton:
            doc = self.session.active_document
            if not doc or not doc.active_layer:
                return
            
            layer = doc.active_layer
            self._original_image = layer.image.copy()
            self._drawing = True
            
            pos = canvas.widget_to_image(event.position().toPoint())
            self._last_pos = pos
            
            # Sample initial color at position
            if 0 <= pos.x() < layer.image.width() and 0 <= pos.y() < layer.image.height():
                self._carry_color = layer.image.pixelColor(pos.x(), pos.y())
            else:
                self._carry_color = QColor(0, 0, 0, 0)
    
    def mouse_move(self, event, canvas):
        if not self._drawing:
            return
            
        doc = self.session.active_document
        if not doc or not doc.active_layer:
            return
            
        layer = doc.active_layer
        pos = canvas.widget_to_image(event.position().toPoint())
        
        if self._last_pos:
            self._smudge_line(layer.image, self._last_pos, pos)
            canvas.update()
        
        self._last_pos = pos
    
    def mouse_release(self, event, canvas):
        if event.button() == Qt.MouseButton.LeftButton and self._drawing:
            self._drawing = False
            
            doc = self.session.active_document
            if doc and doc.active_layer and self._original_image:
                cmd = CanvasCommand(
                    doc.active_layer,
                    self._original_image,
                    "Smudge"
                )
                doc.history.push(cmd)
            
            self._original_image = None
            self._last_pos = None
    
    def _smudge_line(self, image: QImage, start: QPoint, end: QPoint):
        """Smudge along a line from start to end."""
        brush_size = self.session.brush_size
        strength = self._strength
        
        # Bresenham's line
        x0, y0 = start.x(), start.y()
        x1, y1 = end.x(), end.y()
        
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        
        while True:
            self._smudge_brush(image, x0, y0, brush_size, strength)
            
            if x0 == x1 and y0 == y1:
                break
            
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy
    
    def _smudge_brush(self, image: QImage, cx: int, cy: int, size: int, strength: float):
        """Apply smudge at a single point with given brush size."""
        radius = size // 2
        width = image.width()
        height = image.height()
        
        # Average colors in brush area
        r_sum, g_sum, b_sum, a_sum = 0, 0, 0, 0
        count = 0
        
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                if dx * dx + dy * dy <= radius * radius:
                    nx, ny = cx + dx, cy + dy
                    if 0 <= nx < width and 0 <= ny < height:
                        c = image.pixelColor(nx, ny)
                        r_sum += c.red()
                        g_sum += c.green()
                        b_sum += c.blue()
                        a_sum += c.alpha()
                        count += 1
        
        if count == 0:
            return
        
        # Calculate average
        avg_r = r_sum // count
        avg_g = g_sum // count
        avg_b = b_sum // count
        avg_a = a_sum // count
        
        # Blend carry color with average
        new_r = int(self._carry_color.red() * strength + avg_r * (1 - strength))
        new_g = int(self._carry_color.green() * strength + avg_g * (1 - strength))
        new_b = int(self._carry_color.blue() * strength + avg_b * (1 - strength))
        new_a = int(self._carry_color.alpha() * strength + avg_a * (1 - strength))
        
        # Update carry color
        self._carry_color = QColor(new_r, new_g, new_b, new_a)
        
        # Apply to pixels in brush
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                if dx * dx + dy * dy <= radius * radius:
                    nx, ny = cx + dx, cy + dy
                    if 0 <= nx < width and 0 <= ny < height:
                        # Blend original pixel with carry color
                        orig = image.pixelColor(nx, ny)
                        blend = 0.3  # How much to change each pixel
                        
                        final_r = int(orig.red() * (1 - blend) + self._carry_color.red() * blend)
                        final_g = int(orig.green() * (1 - blend) + self._carry_color.green() * blend)
                        final_b = int(orig.blue() * (1 - blend) + self._carry_color.blue() * blend)
                        final_a = int(orig.alpha() * (1 - blend) + self._carry_color.alpha() * blend)
                        
                        image.setPixelColor(nx, ny, QColor(final_r, final_g, final_b, final_a))
