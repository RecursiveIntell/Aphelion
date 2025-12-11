from PySide6.QtGui import QPainter, QPen, QColor, QBrush
from PySide6.QtCore import Qt, QPoint, QRect
from .tool import Tool
from ..core.commands import CanvasCommand

class ShapeTool(Tool):
    def __init__(self, document, session):
        super().__init__(document, session)
        self.start_pos = QPoint()
        self.current_pos = QPoint()
        self.is_drawing = False
        
    def mouse_press(self, pos: QPoint):
        self.is_drawing = True
        self.start_pos = pos
        self.current_pos = pos

    def mouse_move(self, pos: QPoint):
        if self.is_drawing:
            self.current_pos = pos
            # Request overlay update
            # We need a way to trigger canvas update without modifying content
            # The canvas usually updates on content_changed signal.
            # We might need a separate signal for "overlay_changed" or just reuse content_changed 
            # but that implies doc change (which isn't true yet).
            # For now, let's assume canvas repaints on mouse move if tool is active?
            # Actually, we need to tell the view to update the overlay.
            # In Aphelion current architecture, tool events come from CanvasWidget.
            # CanvasWidget should probably update() on mouse move if tool says so.
            # But let's just use a hack: document.content_changed.emit() forces repaint even if no content changed?
            # It's inefficient but works for MVP.
            # Better: We'll add a signal to Tool or Session? 
            # Or just assume CanvasWidget calls update() after mouse_move.
            pass

    def mouse_release(self, pos: QPoint):
        if self.is_drawing:
            self.is_drawing = False
            self.current_pos = pos
            self.commit_shape()

    def commit_shape(self):
        active_layer = self.document.get_active_layer()
        if not active_layer: return
        
        # Check target
        target = self.session.edit_target
        if target == "mask" and not active_layer.mask:
            target = "image"
            
        cmd = CanvasCommand(active_layer, target=target)
        
        # Draw directly to layer for the command capture
        # We need to manually simulate the draw on the layer image
        
        target_image = active_layer.image if target == "image" else active_layer.mask
        
        painter = QPainter(target_image)
        
        # Clipping
        if self.document.has_selection and hasattr(self.document, '_cached_selection_region'):
            painter.setClipRegion(self.document._cached_selection_region)
            
        self.draw_shape(painter)
        painter.end()
        
        cmd.capture_after()
        self.document.history.push(cmd)
        self.document.content_changed.emit()

    def draw_shape(self, painter: QPainter):
        # Override in subclasses
        pass

    def get_pen(self):
        color = self.session.primary_color
        # if self.session.edit_target == "mask": color = ... (Handled by user picking black/white)
        
        pen = QPen(color)
        pen.setWidth(self.session.brush_size) # Reuse brush size for now or add shape_stroke_width
        pen.setJoinStyle(Qt.PenJoinStyle.MiterJoin)
        return pen
        
    def get_rect(self):
        return QRect(self.start_pos, self.current_pos).normalized()

    def draw_overlay(self, painter: QPainter):
        if self.is_drawing:
            self.draw_shape(painter)

class RectangleTool(ShapeTool):
    def __init__(self, document, session):
        super().__init__(document, session)
        self.name = "Rectangle"
        
    def draw_shape(self, painter: QPainter):
        painter.setPen(self.get_pen())
        painter.setBrush(Qt.NoBrush) # Support Fill later
        painter.drawRect(self.get_rect())

class EllipseTool(ShapeTool):
    def __init__(self, document, session):
        super().__init__(document, session)
        self.name = "Ellipse"
        
    def draw_shape(self, painter: QPainter):
        painter.setPen(self.get_pen())
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(self.get_rect())

class LineTool(ShapeTool):
    def __init__(self, document, session):
        super().__init__(document, session)
        self.name = "Line"
        
    def draw_shape(self, painter: QPainter):
        painter.setPen(self.get_pen())
        painter.drawLine(self.start_pos, self.current_pos)
