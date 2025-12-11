from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QPainter, QColor
from .tool import Tool
from ..core.commands import CanvasCommand


class CloneStampTool(Tool):
    """Clone Stamp - copies pixels from source to destination."""
    
    def __init__(self, document, session):
        super().__init__(document, session)
        self.name = "Clone Stamp"
        self.source_pos = None  # Alt+click to set
        self.source_offset = None  # Maintained during stroke
        self.is_cloning = False
        self.last_pos = None
        self.current_command = None
    
    def mouse_press(self, pos: QPoint):
        # Check for Alt modifier to set source
        from PySide6.QtWidgets import QApplication
        modifiers = QApplication.keyboardModifiers()
        
        if modifiers & Qt.KeyboardModifier.AltModifier:
            # Set source point
            self.source_pos = pos
            self.source_offset = None  # Reset offset
            return
        
        # Start cloning if source is set
        if self.source_pos is None:
            return  # No source set, do nothing
        
        # Calculate offset if first stroke after setting source
        if self.source_offset is None:
            self.source_offset = QPoint(
                self.source_pos.x() - pos.x(),
                self.source_pos.y() - pos.y()
            )
        
        self.is_cloning = True
        self.last_pos = pos
        
        # Start command
        layer = self.document.get_active_layer()
        if layer:
            self.current_command = CanvasCommand(layer)
    
    def mouse_move(self, pos: QPoint):
        if not self.is_cloning or self.source_offset is None:
            return
        
        layer = self.document.get_active_layer()
        if not layer:
            return
        
        # Calculate source position
        src_x = pos.x() + self.source_offset.x()
        src_y = pos.y() + self.source_offset.y()
        
        # Get brush size
        size = self.session.brush_size
        half = size // 2
        
        # Clone pixels in brush area
        for dy in range(-half, half + 1):
            for dx in range(-half, half + 1):
                # Circular brush
                if dx * dx + dy * dy > half * half:
                    continue
                
                sx = src_x + dx
                sy = src_y + dy
                tx = pos.x() + dx
                ty = pos.y() + dy
                
                # Bounds check source
                if sx < 0 or sy < 0 or sx >= layer.image.width() or sy >= layer.image.height():
                    continue
                # Bounds check target
                if tx < 0 or ty < 0 or tx >= layer.image.width() or ty >= layer.image.height():
                    continue
                
                # Copy pixel
                color = layer.image.pixelColor(sx, sy)
                layer.image.setPixelColor(tx, ty, color)
        
        self.last_pos = pos
        self.document.content_changed.emit()
    
    def mouse_release(self, pos: QPoint):
        if self.is_cloning and self.current_command:
            self.current_command.capture_after()
            self.document.history.push(self.current_command)
            self.current_command = None
        self.is_cloning = False
    
    def draw_overlay(self, painter: QPainter):
        """Draw source indicator."""
        if self.source_pos:
            painter.setPen(Qt.red)
            painter.drawLine(
                self.source_pos.x() - 5, self.source_pos.y(),
                self.source_pos.x() + 5, self.source_pos.y()
            )
            painter.drawLine(
                self.source_pos.x(), self.source_pos.y() - 5,
                self.source_pos.x(), self.source_pos.y() + 5
            )
