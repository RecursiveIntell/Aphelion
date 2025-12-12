from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QPaintEvent, QColor, QImage, QBrush, QPen, QTransform, QRegion
from PySide6.QtCore import Qt, QRect, QPoint, Signal
from ..core.document import Document
from ..tools.tool import Tool

class CanvasWidget(QWidget):
    # Signals
    cursor_moved = Signal(QPoint)
    zoom_changed = Signal(float)
    
    def __init__(self, document: Document, parent=None, session=None):
        super().__init__(parent)
        self.document = document
        self.session = session  # For keyboard shortcuts
        self.scale = 1.0
        self.offset = QPoint(0, 0)
        
        self.setMouseTracking(True) # Required for mouse move without click
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)  # Enable keyboard input
        
        # Subscribe to document changes to trigger repaints
        self.document.content_changed.connect(self.update)
        self.document.content_changed.connect(self.update)
        self.document.active_layer_changed.connect(lambda l: self.update())
        self.document.selection_changed.connect(self._on_selection_changed)
        
        self.active_tool: Tool | None = None

        # Create checkerboard pattern
        self.checker_brush = self._create_checkerboard_brush()

        # Transient layer for tools (e.g. brush preview)
        # Tools will write to this, and we composite it last.
        # Transient layer for tools (e.g. brush preview)
        # Tools will write to this, and we composite it last.
        self.transient_layer = None 

    def _on_selection_changed(self):
        self.update() 

    def _create_checkerboard_brush(self):
        size = 20
        checker = QImage(size, size, QImage.Format.Format_ARGB32)
        checker.fill(QColor(255, 255, 255))
        painter = QPainter(checker)
        painter.fillRect(0, 0, size // 2, size // 2, QColor(220, 220, 220))
        painter.fillRect(size // 2, size // 2, size // 2, size // 2, QColor(220, 220, 220))
        painter.end()
        return QBrush(checker)

    def paintEvent(self, event: QPaintEvent):
        painter = QPainter(self)
        
        # 0. Clip and Transform (Handle Zoom/Pan)
        transform = QTransform()
        transform.translate(self.offset.x(), self.offset.y())
        transform.scale(self.scale, self.scale)
        painter.setTransform(transform)
        
        # 1. Draw Background (Checkerboard)
        doc_rect = QRect(0, 0, self.document.size.width(), self.document.size.height())
        # Optimize: Calculate visible rect?
        # clip_rect = event.rect() # Widget coords
        # map clip_rect to doc coords...
        
        painter.fillRect(doc_rect, self.checker_brush)
        
        # 2. Render Document Content
        # We render the whole thing for now. Optimization: Render only visible tile.
        rendered_img = self.document.render() # TODO: Pass visible rect
        painter.drawImage(0, 0, rendered_img)
            
        # 3. Draw Selection Overlay
        if self.document.has_selection:
             painter.save()
             region = self.document.get_selection_region()
             if not region.isEmpty():
                 painter.setClipRegion(region)
                 painter.fillRect(doc_rect, QColor(0, 120, 255, 60))
                 painter.setPen(QPen(QColor(255, 255, 255), 1, Qt.DashLine))
                 painter.setBrush(Qt.NoBrush)
                 for r in region:
                     painter.drawRect(r)
             painter.restore()

        # 4. Draw Tool Overlay
        if self.active_tool:
             painter.save()
             self.active_tool.draw_overlay(painter)
             painter.restore()
            
        painter.end()

    def set_tool(self, tool: Tool):
        if self.active_tool:
            self.active_tool.deactivate()
        self.active_tool = tool
        if self.active_tool:
            self.active_tool.activate()

    # Zoom API
    def set_zoom(self, value: float):
        self.scale = max(0.1, min(value, 50.0))
        self.zoom_changed.emit(self.scale)
        self.update()

    def zoom_in(self):
        self.set_zoom(self.scale * 1.2)

    def zoom_out(self):
        self.set_zoom(self.scale / 1.2)

    def zoom_to_fit(self):
        # Calculate scale to fit document in widget
        if self.document.size.isEmpty(): return
        
        ratio_w = self.width() / self.document.size.width()
        ratio_h = self.height() / self.document.size.height()
        scale = min(ratio_w, ratio_h) * 0.9 # 90% fit
        self.set_zoom(scale)
        # Center
        # Calculate offset to center
        # Center of Doc * Scale + Offset = Center of Widget
        # Offset = Center of Widget - Center of Doc * Scale
        cx_w = self.width() / 2
        cy_w = self.height() / 2
        cx_d = self.document.size.width() / 2
        cy_d = self.document.size.height() / 2
        
        self.offset = QPoint(int(cx_w - cx_d * scale), int(cy_w - cy_d * scale))
        self.update()

    # Input events
    # Coordinate Mapping
    def map_to_doc(self, pos: QPoint) -> QPoint:
        # (widget_pos - offset) / scale
        return QPoint(int((pos.x() - self.offset.x()) / self.scale),
                      int((pos.y() - self.offset.y()) / self.scale))

    # Input events
    def wheelEvent(self, event):
        # Zoom centered on mouse
        old_pos = self.map_to_doc(event.position().toPoint())
        
        delta = event.angleDelta().y()
        if delta > 0:
            self.scale *= 1.1
        else:
            self.scale /= 1.1

        # Clamp scale
        self.scale = max(0.1, min(self.scale, 50.0))
        self.zoom_changed.emit(self.scale)
        
        # Adjust offset to keep mouse over same point
        # new_offset = mouse_pos - (doc_pos * new_scale)
        new_offset_x = event.position().x() - (old_pos.x() * self.scale)
        new_offset_y = event.position().y() - (old_pos.y() * self.scale)
        self.offset = QPoint(int(new_offset_x), int(new_offset_y))
        
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.MiddleButton:
            self._last_pan_pos = event.position().toPoint()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            return

        if self.active_tool:
            # Send world coordinates to tool
            world_pos = self.map_to_doc(event.position().toPoint())
            self.active_tool.mouse_press(world_pos)

    def mouseMoveEvent(self, event):
        # Handle Panning
        if event.buttons() & Qt.MouseButton.MiddleButton:
            delta = event.position().toPoint() - self._last_pan_pos
            self.offset += delta
            self._last_pan_pos = event.position().toPoint()
            self.update()
            return
            
        world_pos = self.map_to_doc(event.position().toPoint())
        self.cursor_moved.emit(world_pos)

        if self.active_tool:
            self.active_tool.mouse_move(world_pos)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.MiddleButton:
            self.setCursor(Qt.CursorShape.ArrowCursor)
            return

        if self.active_tool:
            world_pos = self.map_to_doc(event.position().toPoint())
            self.active_tool.mouse_release(world_pos)

    def keyPressEvent(self, event):
        """Handle keyboard shortcuts when canvas has focus."""
        # X - Swap colors (Paint.NET style)
        if event.key() == Qt.Key.Key_X and not event.modifiers():
            if self.session:
                print("DEBUG: X pressed in canvas - swapping colors!")
                self.session.swap_colors()
                event.accept()
                return
        super().keyPressEvent(event)
