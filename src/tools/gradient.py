"""
Gradient Tool for Aphelion.
Supports linear and radial gradients.
"""
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QImage, QColor, QPainter, QLinearGradient, QRadialGradient
from .tool import Tool
from ..core.commands import CanvasCommand
import math


class GradientTool(Tool):
    name = "Gradient"
    
    # Gradient types
    LINEAR = 0
    RADIAL = 1
    
    def __init__(self, document, session):
        super().__init__(document, session)
        self.gradient_type = self.LINEAR
        self.start_point = None
        self.end_point = None
        self.drawing = False
        self._cmd = None
    
    def set_gradient_type(self, gtype):
        """Set gradient type: LINEAR or RADIAL"""
        self.gradient_type = gtype
    
    def mouse_press(self, pos: QPoint):
        if not self.document:
            return
        layer = self.document.get_active_layer()
        if not layer:
            return
            
        self.start_point = pos
        self.end_point = pos
        self.drawing = True
        self._cmd = CanvasCommand(layer)
    
    def mouse_move(self, pos: QPoint):
        if self.drawing:
            self.end_point = pos
    
    def mouse_release(self, pos: QPoint):
        if not self.drawing or not self.document:
            return
            
        layer = self.document.get_active_layer()
        if not layer:
            return
            
        self.end_point = pos
        self.drawing = False
        
        # Apply gradient to layer
        self._draw_gradient(layer.image)
        
        # Capture after for undo
        if self._cmd:
            self._cmd.capture_after()
            self.document.history.push(self._cmd)
        
        self.document.content_changed.emit()
        self.start_point = None
        self.end_point = None
    
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
        else:  # RADIAL
            dx = self.end_point.x() - self.start_point.x()
            dy = self.end_point.y() - self.start_point.y()
            radius = math.sqrt(dx*dx + dy*dy)
            gradient = QRadialGradient(self.start_point, max(1, radius))
        
        gradient.setColorAt(0.0, primary)
        gradient.setColorAt(1.0, secondary)
        
        painter.fillRect(image.rect(), gradient)
        painter.end()
    
    def draw_overlay(self, painter):
        """Draw guide line while dragging"""
        if self.drawing and self.start_point and self.end_point:
            painter.setPen(Qt.white)
            painter.drawLine(self.start_point, self.end_point)
            painter.drawEllipse(self.start_point, 5, 5)
            painter.drawEllipse(self.end_point, 5, 5)
