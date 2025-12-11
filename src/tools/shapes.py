from PySide6.QtCore import QPoint, QRect, Qt
from PySide6.QtGui import QPainter, QColor, QPen, QBrush
from .tool import Tool
from ..core.document import Document
from ..core.commands import CanvasCommand

class LineTool(Tool):
    def __init__(self, document, session):
        super().__init__(document, session)
        self.name = "Line/Curve"
        self.start_pos = None
        self.end_pos = None
        self.is_dragging = False

    def mouse_press(self, pos: QPoint):
        self.start_pos = pos
        self.end_pos = pos
        self.is_dragging = True

    def mouse_move(self, pos: QPoint):
        if self.is_dragging:
            self.end_pos = pos
            self.document.content_changed.emit()

    def mouse_release(self, pos: QPoint):
        if self.is_dragging:
            self.is_dragging = False
            self.end_pos = pos
            
            # Commit to layer
            layer = self.document.get_active_layer()
            if layer:
                cmd = CanvasCommand(layer)
                
                painter = QPainter(layer.image)
                painter.setIsDrawingSelection(self.document.has_selection) # Optional if we use clip
                if self.document.has_selection:
                    painter.setClipRegion(self.document.get_selection_region())
                    
                # Use Session Colors
                pen_color = self.session.primary_color
                painter.setPen(QPen(pen_color, 2))
                
                painter.drawLine(self.start_pos, self.end_pos)
                painter.end()
                
                cmd.capture_after()
                self.document.history.push(cmd)
                self.document.content_changed.emit()

    def draw_overlay(self, painter: QPainter):
        if self.is_dragging:
            painter.setPen(QPen(Qt.black, 2)) # Preview
            painter.drawLine(self.start_pos, self.end_pos)

class ShapesTool(Tool):
    def __init__(self, document, session):
        super().__init__(document, session)
        self.name = "Shapes"
        self.shape_type = "Rectangle" # Rectangle, Ellipse, RoundedRect
        self.fill_mode = "Outline" # Outline, Fill, Both
        self.start_pos = None
        self.end_pos = None
        self.is_dragging = False

    def mouse_press(self, pos: QPoint):
        self.start_pos = pos
        self.end_pos = pos
        self.is_dragging = True

    def mouse_move(self, pos: QPoint):
        if self.is_dragging:
            self.end_pos = pos
            self.document.content_changed.emit()

    def mouse_release(self, pos: QPoint):
        if self.is_dragging:
            self.is_dragging = False
            
            layer = self.document.get_active_layer()
            if layer:
                cmd = CanvasCommand(layer)
                painter = QPainter(layer.image)
                if self.document.has_selection:
                    painter.setClipRegion(self.document.get_selection_region())
                
                rect = QRect(self.start_pos, self.end_pos).normalized()
                
                # Use Session Colors
                p_color = self.session.primary_color
                s_color = self.session.secondary_color
                
                pen = QPen(p_color, 2)
                brush = QBrush(s_color)
                
                if self.fill_mode == "Outline":
                    painter.setPen(pen)
                    painter.setBrush(Qt.NoBrush)
                elif self.fill_mode == "Fill":
                    painter.setPen(Qt.NoPen)
                    painter.setBrush(brush)
                else: 
                    painter.setPen(pen)
                    painter.setBrush(brush)
                
                if self.shape_type == "Rectangle":
                    painter.drawRect(rect)
                elif self.shape_type == "Ellipse":
                    painter.drawEllipse(rect)
                elif self.shape_type == "RoundedRect":
                    painter.drawRoundedRect(rect, 10, 10)
                    
                painter.end()
                
                cmd.capture_after()
                self.document.history.push(cmd)
                self.document.content_changed.emit()

    def draw_overlay(self, painter: QPainter):
        if self.is_dragging:
            rect = QRect(self.start_pos, self.end_pos).normalized()
            painter.setPen(Qt.black)
            painter.setBrush(Qt.NoBrush)
            if self.shape_type == "Rectangle":
                painter.drawRect(rect)
            elif self.shape_type == "Ellipse":
                painter.drawEllipse(rect)
