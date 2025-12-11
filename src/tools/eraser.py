from PySide6.QtGui import QPainter, QPen, QColor, QBrush
from PySide6.QtCore import Qt, QPoint
from .tool import Tool
from ..core.commands import CanvasCommand

class EraserTool(Tool):
    def __init__(self, document, session):
        super().__init__(document, session)
        self.name = "Eraser"
        self.is_drawing = False
        self.last_pos = QPoint()
        self.current_command: CanvasCommand | None = None
        self.pressure_enabled = True
        self.last_pressure = 1.0

    def mouse_press(self, pos: QPoint):
        self.is_drawing = True
        self.last_pos = pos
        self.last_pressure = 1.0
        active_layer = self.document.get_active_layer()
        if active_layer:
            target = self.session.edit_target
            if target == "mask" and not active_layer.mask:
                target = "image"
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
        """Draw eraser stroke with optional pressure sensitivity."""
        active_layer = self.document.get_active_layer()
        if active_layer:
            target = self.session.edit_target
            target_image = active_layer.image
            
            if target == "mask" and active_layer.mask:
                target_image = active_layer.mask
            
            painter = QPainter(target_image)
            
            # Clipping
            if self.document.has_selection and hasattr(self.document, '_cached_selection_region'):
                painter.setClipRegion(self.document._cached_selection_region)
            
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_DestinationOut)
            
            base_size = self.session.brush_size
            if self.pressure_enabled:
                size = int(base_size * self.last_pressure)
            else:
                size = base_size
            size = max(1, size)
            
            pen = QPen(QColor(0,0,0,255))
            pen.setWidth(size)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            painter.setPen(pen)
            
            painter.drawLine(self.last_pos, pos)
            painter.end()
            
            self.last_pos = pos
            self.document.content_changed.emit()

    def mouse_release(self, pos: QPoint):
        if self.is_drawing:
            self.is_drawing = False
            if self.current_command:
                self.current_command.capture_after()
                self.document.history.push(self.current_command)
                self.current_command = None
