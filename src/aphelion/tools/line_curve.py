from PySide6.QtCore import QPoint, QPointF, Qt
from PySide6.QtGui import QPainter, QPen, QColor, QPainterPath
from .tool import Tool
from ..core.commands import CanvasCommand


class LineCurveTool(Tool):
    """Line/Curve tool - draw straight lines or Bezier curves."""
    
    def __init__(self, document, session):
        super().__init__(document, session)
        self.name = "Line / Curve"
        self.start_pos = None
        self.end_pos = None
        self.control_points = []  # Up to 2 control points for cubic Bezier
        self.is_dragging = False
        self.mode = "line"  # "line" or "curve"
        self.edit_phase = 0  # 0: drawing line, 1-2: adding control points
    
    def mouse_press(self, pos: QPoint):
        if self.edit_phase == 0:
            # Start new line
            self.start_pos = pos
            self.end_pos = pos
            self.is_dragging = True
            self.control_points = []
        elif self.edit_phase in (1, 2):
            # Add control point
            self.control_points.append(pos)
            self.edit_phase += 1
            self.document.content_changed.emit()
    
    def mouse_move(self, pos: QPoint):
        if self.is_dragging and self.edit_phase == 0:
            self.end_pos = pos
            self.document.content_changed.emit()
    
    def mouse_release(self, pos: QPoint):
        if self.is_dragging and self.edit_phase == 0:
            self.is_dragging = False
            self.end_pos = pos
            
            # If shift held, constrain to angles
            from PySide6.QtWidgets import QApplication
            modifiers = QApplication.keyboardModifiers()
            if modifiers & Qt.KeyboardModifier.ShiftModifier:
                self.end_pos = self._constrain_angle(self.start_pos, pos)
            
            # Check if this should be a line or curve
            # For simplicity: single release = draw line immediately
            # Double-click or Enter key could confirm curve mode
            self._commit_shape()
    
    def _constrain_angle(self, start: QPoint, end: QPoint) -> QPoint:
        """Constrain to 45-degree increments."""
        import math
        dx = end.x() - start.x()
        dy = end.y() - start.y()
        angle = math.atan2(dy, dx)
        # Snap to nearest 45 degrees
        snapped = round(angle / (math.pi / 4)) * (math.pi / 4)
        dist = math.sqrt(dx * dx + dy * dy)
        new_x = start.x() + int(dist * math.cos(snapped))
        new_y = start.y() + int(dist * math.sin(snapped))
        return QPoint(new_x, new_y)
    
    def _commit_shape(self):
        """Draw the line/curve to the layer."""
        layer = self.document.get_active_layer()
        if not layer or not self.start_pos or not self.end_pos:
            return
        
        cmd = CanvasCommand(layer)
        
        painter = QPainter(layer.image)
        
        # Selection clipping
        if self.document.has_selection:
            painter.setClipRegion(self.document.get_selection_region())
        
        # Set pen
        pen = QPen(self.session.primary_color)
        pen.setWidth(self.session.brush_size)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        
        if len(self.control_points) == 0:
            # Straight line
            painter.drawLine(self.start_pos, self.end_pos)
        elif len(self.control_points) == 1:
            # Quadratic Bezier
            path = QPainterPath(QPointF(self.start_pos))
            path.quadTo(
                QPointF(self.control_points[0]),
                QPointF(self.end_pos)
            )
            painter.drawPath(path)
        else:
            # Cubic Bezier
            path = QPainterPath(QPointF(self.start_pos))
            path.cubicTo(
                QPointF(self.control_points[0]),
                QPointF(self.control_points[1]),
                QPointF(self.end_pos)
            )
            painter.drawPath(path)
        
        painter.end()
        
        cmd.capture_after()
        self.document.history.push(cmd)
        self.document.content_changed.emit()
        
        # Reset
        self.start_pos = None
        self.end_pos = None
        self.control_points = []
        self.edit_phase = 0
    
    def draw_overlay(self, painter: QPainter):
        """Draw preview of line/curve."""
        if not self.start_pos or not self.end_pos:
            return
        
        pen = QPen(self.session.primary_color)
        pen.setWidth(self.session.brush_size)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setStyle(Qt.PenStyle.DashLine)
        painter.setPen(pen)
        
        if len(self.control_points) == 0:
            painter.drawLine(self.start_pos, self.end_pos)
        elif len(self.control_points) == 1:
            path = QPainterPath(QPointF(self.start_pos))
            path.quadTo(QPointF(self.control_points[0]), QPointF(self.end_pos))
            painter.drawPath(path)
        
        # Draw control point handles
        painter.setPen(Qt.red)
        for cp in self.control_points:
            painter.drawEllipse(cp, 4, 4)
