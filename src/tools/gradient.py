"""
Gradient Tool for Aphelion.
Supports linear, radial, conical, diamond, and reflected gradients.
"""
from PySide6.QtCore import Qt, QPoint, QPointF
from PySide6.QtGui import QImage, QColor, QPainter, QLinearGradient, QRadialGradient, QConicalGradient
from .tool import Tool
from ..core.commands import CanvasCommand
import math


class GradientTool(Tool):
    name = "Gradient"
    icon = "gradient"
    shortcut = "G"
    
    # Gradient types
    LINEAR = 0
    RADIAL = 1
    CONICAL = 2
    DIAMOND = 3
    REFLECTED = 4
    
    GRADIENT_NAMES = ["Linear", "Radial", "Conical", "Diamond", "Reflected"]
    
    def __init__(self, session):
        super().__init__(session)
        self.gradient_type = self.LINEAR
        self.start_point = None
        self.end_point = None
        self.drawing = False
        self._original_image = None
    
    def set_gradient_type(self, gtype):
        """Set gradient type: LINEAR, RADIAL, CONICAL, DIAMOND, or REFLECTED"""
        self.gradient_type = gtype
    
    def activate(self):
        pass
    
    def deactivate(self):
        pass
    
    def mouse_press(self, event, canvas):
        if event.button() != Qt.MouseButton.LeftButton:
            return
            
        doc = self.session.active_document
        if not doc or not doc.active_layer:
            return
        
        pos = canvas.widget_to_image(event.position().toPoint())
        self.start_point = pos
        self.end_point = pos
        self.drawing = True
        self._original_image = doc.active_layer.image.copy()
    
    def mouse_move(self, event, canvas):
        if self.drawing:
            self.end_point = canvas.widget_to_image(event.position().toPoint())
            canvas.update()
    
    def mouse_release(self, event, canvas):
        if event.button() != Qt.MouseButton.LeftButton or not self.drawing:
            return
            
        doc = self.session.active_document
        if not doc or not doc.active_layer:
            return
        
        self.end_point = canvas.widget_to_image(event.position().toPoint())
        self.drawing = False
        
        # Apply gradient to layer
        self._draw_gradient(doc.active_layer.image)
        
        # Push undo command
        if self._original_image:
            cmd = CanvasCommand(doc.active_layer, self._original_image, "Gradient")
            doc.history.push(cmd)
        
        doc.content_changed.emit()
        canvas.update()
        
        self.start_point = None
        self.end_point = None
        self._original_image = None
    
    def _draw_gradient(self, image: QImage):
        """Draw the gradient on an image"""
        if not self.start_point or not self.end_point:
            return
        
        # Get colors from session
        primary = self.session.primary_color
        secondary = self.session.secondary_color
        
        painter = QPainter(image)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        if self.gradient_type == self.LINEAR:
            gradient = QLinearGradient(self.start_point, self.end_point)
            gradient.setColorAt(0.0, primary)
            gradient.setColorAt(1.0, secondary)
            painter.fillRect(image.rect(), gradient)
            
        elif self.gradient_type == self.RADIAL:
            dx = self.end_point.x() - self.start_point.x()
            dy = self.end_point.y() - self.start_point.y()
            radius = math.sqrt(dx*dx + dy*dy)
            gradient = QRadialGradient(self.start_point, max(1, radius))
            gradient.setColorAt(0.0, primary)
            gradient.setColorAt(1.0, secondary)
            painter.fillRect(image.rect(), gradient)
            
        elif self.gradient_type == self.CONICAL:
            # Angle-based gradient around center point
            gradient = QConicalGradient(QPointF(self.start_point), 0)
            gradient.setColorAt(0.0, primary)
            gradient.setColorAt(0.5, secondary)
            gradient.setColorAt(1.0, primary)
            painter.fillRect(image.rect(), gradient)
            
        elif self.gradient_type == self.DIAMOND:
            # Custom diamond gradient (manual pixel calculation)
            self._draw_diamond_gradient(image, primary, secondary)
            painter.end()
            return
            
        elif self.gradient_type == self.REFLECTED:
            # Reflected linear gradient (mirrors at center)
            self._draw_reflected_gradient(image, primary, secondary)
            painter.end()
            return
        
        painter.end()
    
    def _draw_diamond_gradient(self, image: QImage, primary: QColor, secondary: QColor):
        """Draw a diamond-shaped gradient."""
        cx, cy = self.start_point.x(), self.start_point.y()
        dx = abs(self.end_point.x() - cx)
        dy = abs(self.end_point.y() - cy)
        max_dist = max(dx, dy, 1)
        
        width = image.width()
        height = image.height()
        
        for y in range(height):
            for x in range(width):
                # Diamond distance (Manhattan distance)
                dist = abs(x - cx) + abs(y - cy)
                t = min(1.0, dist / max_dist)
                
                r = int(primary.red() * (1 - t) + secondary.red() * t)
                g = int(primary.green() * (1 - t) + secondary.green() * t)
                b = int(primary.blue() * (1 - t) + secondary.blue() * t)
                a = int(primary.alpha() * (1 - t) + secondary.alpha() * t)
                
                image.setPixelColor(x, y, QColor(r, g, b, a))
    
    def _draw_reflected_gradient(self, image: QImage, primary: QColor, secondary: QColor):
        """Draw a reflected gradient (mirrors at center)."""
        sx, sy = self.start_point.x(), self.start_point.y()
        ex, ey = self.end_point.x(), self.end_point.y()
        
        # Vector from start to end
        dx = ex - sx
        dy = ey - sy
        length = math.sqrt(dx*dx + dy*dy)
        if length == 0:
            length = 1
        
        # Normalize
        nx, ny = dx / length, dy / length
        
        width = image.width()
        height = image.height()
        
        for y in range(height):
            for x in range(width):
                # Project point onto gradient line
                px, py = x - sx, y - sy
                proj = px * nx + py * ny
                
                # Reflect: use absolute distance from center, normalized
                t = abs(proj) / length
                t = min(1.0, t)
                
                r = int(primary.red() * (1 - t) + secondary.red() * t)
                g = int(primary.green() * (1 - t) + secondary.green() * t)
                b = int(primary.blue() * (1 - t) + secondary.blue() * t)
                a = int(primary.alpha() * (1 - t) + secondary.alpha() * t)
                
                image.setPixelColor(x, y, QColor(r, g, b, a))
    
    def draw_overlay(self, painter):
        """Draw guide line while dragging"""
        if self.drawing and self.start_point and self.end_point:
            painter.setPen(Qt.GlobalColor.white)
            painter.drawLine(self.start_point, self.end_point)
            painter.drawEllipse(self.start_point, 5, 5)
            painter.drawEllipse(self.end_point, 5, 5)
            
            # Show gradient type
            type_name = self.GRADIENT_NAMES[self.gradient_type]
            painter.drawText(self.start_point.x() + 10, self.start_point.y() - 10, type_name)
