from PySide6.QtGui import QPainter, QPen, QColor
from PySide6.QtCore import Qt, QPoint, QLine
from .tool import Tool
from ..core.commands import CanvasCommand

class BrushTool(Tool):
    def __init__(self, document, session):
        super().__init__(document, session)
        self.name = "Brush"
        self.is_drawing = False
        self.last_pos = QPoint()
        self.current_command: CanvasCommand | None = None
        self.pressure_enabled = True  # Enable tablet pressure
        self.last_pressure = 1.0

    def mouse_press(self, pos: QPoint):
        self.is_drawing = True
        self.last_pos = pos
        self.last_pressure = 1.0
        
        active_layer = self.document.get_active_layer()
        if active_layer:
            # Determine target
            target = self.session.edit_target
            if target == "mask" and not active_layer.mask:
                target = "image" # Fallback if no mask
                
            # Create command
            self.current_command = CanvasCommand(active_layer, target=target)

    def tablet_event(self, pos: QPoint, pressure: float):
        """Handle tablet event with pressure sensitivity."""
        if not self.is_drawing:
            return
        
        self.last_pressure = max(0.1, pressure)
        self._draw_stroke(pos)

    def mouse_move(self, pos: QPoint):
        if not self.is_drawing:
            return
        self._draw_stroke(pos)

    def _draw_stroke(self, pos: QPoint):
        """Draw brush stroke with optional pressure sensitivity."""
        active_layer = self.document.get_active_layer()
        if active_layer:
            target = self.session.edit_target
            
            target_image = active_layer.image
            if target == "mask" and active_layer.mask:
                target_image = active_layer.mask
            
            # Draw
            painter = QPainter(target_image)
            
            # Handle Selection Clipping
            if self.document.has_selection and hasattr(self.document, '_cached_selection_region'):
                painter.setClipRegion(self.document._cached_selection_region)

            color = self.session.primary_color
            base_size = self.session.brush_size
            
            # Apply pressure to size
            if self.pressure_enabled:
                size = int(base_size * self.last_pressure)
            else:
                size = base_size
            
            size = max(1, size)

            pen = QPen(color)
            pen.setWidth(size)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            painter.setPen(pen)
            
            painter.drawLine(self.last_pos, pos)
            painter.end()
            
            self.last_pos = pos
            # Request redraw
            self.document.content_changed.emit()

    def mouse_release(self, pos: QPoint):
        if self.is_drawing:
            self.is_drawing = False
            if self.current_command:
                self.current_command.capture_after()
                self.document.history.push(self.current_command)
                self.current_command = None
