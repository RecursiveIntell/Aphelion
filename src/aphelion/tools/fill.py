from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QPainter, QColor, QLinearGradient
from .tool import Tool
from ..core.document import Document
from ..core.commands import CanvasCommand

class PaintBucketTool(Tool):
    def __init__(self, document, session):
        super().__init__(document, session)
        self.name = "Paint Bucket"
        self.tolerance = 30  # Default tolerance for flood fill

    def mouse_press(self, pos: QPoint):
        layer = self.document.get_active_layer()
        if not layer: return
        
        # Check bounds
        if pos.x() < 0 or pos.x() >= layer.image.width() or pos.y() < 0 or pos.y() >= layer.image.height():
            return
        
        # Prepare undo
        cmd = CanvasCommand(layer)
        
        # Get target color
        target_color = layer.image.pixelColor(pos.x(), pos.y())
        
        # Flood Fill logic similar to Magic Wand but painting
        # We can implement a shared recursive fill or reuse selection mask logic?
        # Reuse selection logic: Get Mask -> Fill Mask area?
        # Or direct pixel manipulation.
        # Direct is faster potentially if we write bytes.
        
        # Let's reuse the BFS logic for now (duplicated - should refactor to Utils)
        # Use primary color
        fill_color = self.session.primary_color
        self.fill(layer.image, pos, target_color, fill_color)
        
        cmd.capture_after()
        self.document.history.push(cmd)
        self.document.content_changed.emit()

    def mouse_move(self, pos: QPoint):
        pass

    def mouse_release(self, pos: QPoint):
        pass

    def fill(self, image, seed, target_color, fill_color):
         # Limited BFS Flood Fill with Optimization
         if target_color == fill_color: return

         width = image.width()
         height = image.height()
         
         # Convert colors to ARGB int for fast check if exact match needed
         # But tolerance check needs r,g,b components.
         # target_color matches seed pixel color
         tr, tg, tb = target_color.red(), target_color.green(), target_color.blue()
         
         # Use integer tuple for queue/visited to avoid QPoint overhead
         queue = [(seed.x(), seed.y())]
         visited = set()
         visited.add((seed.x(), seed.y()))
         
         # Optimization: direct pixel access (returns int QRgb)
         # But we might need qRed etc.
         # If simpler: just use pixelColor overhead if tolerance is high, but we want speed.
         
         # Let's try to access pixel() -> int
         # And parse int manually to avoid function call overhead?
         # ARGB32: AARRGGBB
         
         import struct
         
         # Pre-calculate fill color int?
         # We need to setPixelColor still, or setPixel (takes int)
         # image.setPixel(x,y, int_val)
         
         fr, fg, fb, fa = fill_color.red(), fill_color.green(), fill_color.blue(), fill_color.alpha()
         fill_rgb = fill_color.rgba() # Returns int
         
         
         while queue:
            x, y = queue.pop(0)
            
            image.setPixelColor(x, y, fill_color) # Slow? setPixel(x,y, fill_rgb) might fail if signed/unsigned confusion in PySide6
            
            # Check neighbors
            # Unrolled
            if x + 1 < width:
                nx, ny = x + 1, y
                if (nx, ny) not in visited:
                    visited.add((nx, ny))
                    c_int = image.pixel(nx, ny)
                    # ARGB32 - extraction
                    cr = (c_int >> 16) & 0xFF
                    cg = (c_int >> 8) & 0xFF
                    cb = c_int & 0xFF
                    
                    dist = max(abs(cr - tr), abs(cg - tg), abs(cb - tb))
                    if dist <= self.tolerance:
                        queue.append((nx, ny))

            if x - 1 >= 0:
                nx, ny = x - 1, y
                if (nx, ny) not in visited:
                    visited.add((nx, ny))
                    c_int = image.pixel(nx, ny)
                    cr = (c_int >> 16) & 0xFF
                    cg = (c_int >> 8) & 0xFF
                    cb = c_int & 0xFF
                    dist = max(abs(cr - tr), abs(cg - tg), abs(cb - tb))
                    if dist <= self.tolerance:
                        queue.append((nx, ny))

            if y + 1 < height:
                nx, ny = x, y + 1
                if (nx, ny) not in visited:
                    visited.add((nx, ny))
                    c_int = image.pixel(nx, ny)
                    cr = (c_int >> 16) & 0xFF
                    cg = (c_int >> 8) & 0xFF
                    cb = c_int & 0xFF
                    dist = max(abs(cr - tr), abs(cg - tg), abs(cb - tb))
                    if dist <= self.tolerance:
                        queue.append((nx, ny))

            if y - 1 >= 0:
                nx, ny = x, y - 1
                if (nx, ny) not in visited:
                    visited.add((nx, ny))
                    c_int = image.pixel(nx, ny)
                    cr = (c_int >> 16) & 0xFF
                    cg = (c_int >> 8) & 0xFF
                    cb = c_int & 0xFF
                    dist = max(abs(cr - tr), abs(cg - tg), abs(cb - tb))
                    if dist <= self.tolerance:
                        queue.append((nx, ny))

class GradientTool(Tool):
    def __init__(self, document, session):
        super().__init__(document, session)
        self.name = "Gradient"
        self.start_pos = None
        self.is_dragging = False

    def mouse_press(self, pos: QPoint):
        self.start_pos = pos
        self.is_dragging = True

    def mouse_move(self, pos: QPoint):
        if self.is_dragging:
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
                
                # Gradient
                grad = QLinearGradient(self.start_pos, pos)
                # Use Session colors
                c1 = self.session.primary_color
                c2 = self.session.secondary_color
                grad.setColorAt(0, c1)
                grad.setColorAt(1, c2)
                
                painter.fillRect(layer.image.rect(), grad)
                painter.end()
                
                cmd.capture_after()
                self.document.history.push(cmd)
                self.document.content_changed.emit()

    def draw_overlay(self, painter: QPainter):
        if self.is_dragging and self.start_pos:
            # Draw line
            current_pos = self.session.active_tool.current_pos if hasattr(self.session.active_tool, 'current_pos') else QApplication.widgetAt(QCursor.pos()) 
            # Wait, `current_pos` is not tracked in GradientTool.
            # We need to track it in mouse_move.
            # Or use `last_pos`?
            pass

    # We need to update mouse_move to store current_pos
    def mouse_move(self, pos: QPoint):
        self.current_pos = pos
        if self.is_dragging:
            self.document.content_changed.emit()

    def draw_overlay(self, painter: QPainter):
        if self.is_dragging and self.start_pos and hasattr(self, 'current_pos'):
            # Draw line
            painter.setPen(Qt.black)
            painter.drawLine(self.start_pos, self.current_pos)
            
            # Draw endpoints
            painter.setBrush(Qt.white)
            painter.drawEllipse(self.start_pos, 3, 3)
            painter.drawEllipse(self.current_pos, 3, 3)
