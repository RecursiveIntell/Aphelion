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


class RoundedRectTool(ShapeTool):
    """Rounded rectangle shape tool."""
    def __init__(self, document, session):
        super().__init__(document, session)
        self.name = "Rounded Rectangle"
        self.corner_radius = 20  # Default corner radius
        
    def draw_shape(self, painter: QPainter):
        painter.setPen(self.get_pen())
        painter.setBrush(Qt.NoBrush)
        rect = self.get_rect()
        painter.drawRoundedRect(rect, self.corner_radius, self.corner_radius)


class PolygonTool(ShapeTool):
    """Regular polygon shape tool (triangle, pentagon, hexagon, etc.)."""
    def __init__(self, document, session):
        super().__init__(document, session)
        self.name = "Polygon"
        self.sides = 6  # Default to hexagon
        
    def draw_shape(self, painter: QPainter):
        import math
        from PySide6.QtCore import QPointF
        from PySide6.QtGui import QPolygonF
        
        painter.setPen(self.get_pen())
        painter.setBrush(Qt.NoBrush)
        
        rect = self.get_rect()
        cx = rect.center().x()
        cy = rect.center().y()
        radius = min(rect.width(), rect.height()) / 2
        
        points = []
        for i in range(self.sides):
            angle = (2 * math.pi * i / self.sides) - (math.pi / 2)  # Start from top
            x = cx + radius * math.cos(angle)
            y = cy + radius * math.sin(angle)
            points.append(QPointF(x, y))
        
        polygon = QPolygonF(points)
        painter.drawPolygon(polygon)


class StarTool(ShapeTool):
    """Star shape tool with configurable points."""
    def __init__(self, document, session):
        super().__init__(document, session)
        self.name = "Star"
        self.points = 5  # Number of points
        self.inner_radius_ratio = 0.4  # Inner radius as ratio of outer
        
    def draw_shape(self, painter: QPainter):
        import math
        from PySide6.QtCore import QPointF
        from PySide6.QtGui import QPolygonF
        
        painter.setPen(self.get_pen())
        painter.setBrush(Qt.NoBrush)
        
        rect = self.get_rect()
        cx = rect.center().x()
        cy = rect.center().y()
        outer_radius = min(rect.width(), rect.height()) / 2
        inner_radius = outer_radius * self.inner_radius_ratio
        
        star_points = []
        for i in range(self.points * 2):
            angle = (math.pi * i / self.points) - (math.pi / 2)  # Start from top
            radius = outer_radius if i % 2 == 0 else inner_radius
            x = cx + radius * math.cos(angle)
            y = cy + radius * math.sin(angle)
            star_points.append(QPointF(x, y))
        
        polygon = QPolygonF(star_points)
        painter.drawPolygon(polygon)


class ArrowTool(ShapeTool):
    """Arrow shape tool."""
    def __init__(self, document, session):
        super().__init__(document, session)
        self.name = "Arrow"
        self.head_size = 20  # Arrow head size
        
    def draw_shape(self, painter: QPainter):
        import math
        from PySide6.QtCore import QPointF
        from PySide6.QtGui import QPolygonF
        
        painter.setPen(self.get_pen())
        
        # Draw line from start to end
        painter.drawLine(self.start_pos, self.current_pos)
        
        # Calculate arrow head
        dx = self.current_pos.x() - self.start_pos.x()
        dy = self.current_pos.y() - self.start_pos.y()
        length = math.sqrt(dx * dx + dy * dy)
        
        if length < 1:
            return
        
        # Normalize direction
        ux = dx / length
        uy = dy / length
        
        # Perpendicular
        px = -uy
        py = ux
        
        # Arrow head points
        head_size = min(self.head_size, length * 0.3)
        
        tip = QPointF(self.current_pos.x(), self.current_pos.y())
        left = QPointF(
            self.current_pos.x() - head_size * ux + head_size * 0.5 * px,
            self.current_pos.y() - head_size * uy + head_size * 0.5 * py
        )
        right = QPointF(
            self.current_pos.x() - head_size * ux - head_size * 0.5 * px,
            self.current_pos.y() - head_size * uy - head_size * 0.5 * py
        )
        
        arrow_head = QPolygonF([tip, left, right])
        painter.setBrush(QBrush(self.session.primary_color))
        painter.drawPolygon(arrow_head)
