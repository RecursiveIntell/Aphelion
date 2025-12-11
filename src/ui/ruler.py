from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QColor, QFont
from PySide6.QtCore import Qt, QSize

class RulerWidget(QWidget):
    HORIZONTAL = 0
    VERTICAL = 1

    def __init__(self, orientation, parent=None):
        super().__init__(parent)
        self.orientation = orientation
        self.offset = 0.0 # Pixels
        self.zoom = 1.0
        self.unit_size = 50 # Default unit spacing
        
        if self.orientation == self.HORIZONTAL:
            self.setFixedHeight(25)
        else:
            self.setFixedWidth(25)
            
    def set_zoom(self, zoom):
        if self.zoom != zoom:
            self.zoom = zoom
            self.update()
            
    def set_offset(self, offset):
        if self.offset != offset:
            self.offset = offset
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(240, 240, 240))
        painter.setPen(Qt.black)
        font = painter.font()
        font.setPointSize(8)
        painter.setFont(font)
        
        if self.orientation == self.HORIZONTAL:
            self._draw_horizontal(painter)
        else:
            self._draw_vertical(painter)
            
    def _draw_horizontal(self, painter):
        w = self.width()
        # Start from offset (which maps to 0 in doc coords)
        # Screen X to Doc X: (screen_x) / zoom + offset?? 
        # No, offset is the document coordinate at screen 0?
        # Typically ruler matches canvas.
        # Let's assume offset matches the scroll/pan.
        
        # Doc 0 is at screen coordinates: (0 - offset) * zoom?
        # Let's stick to simple: pass "start_doc_coord" as offset.
        
        # Tick logic
        # Distance between ticks on screen approx 50-100px.
        # Doc units per tick = Screen_Tick / Zoom.
        # Find nice power of 10 or 5.
        
        screen_tick_target = 60
        doc_tick = screen_tick_target / self.zoom
        
        # Round to nice number
        import math
        exp = math.floor(math.log10(doc_tick or 1))
        step = 10**exp
        if doc_tick / step >= 5: step *= 5
        elif doc_tick / step >= 2: step *= 2
        
        start_doc = self.offset
        end_doc = self.offset + w / self.zoom
        
        start_tick = (start_doc // step) * step
        
        t = start_tick
        while t < end_doc + step:
            # Map doc T to screen X
            screen_x = (t - self.offset) * self.zoom
            
            if 0 <= screen_x <= w:
                if t % (step * 2) == 0:
                     h = 10
                     painter.drawText(int(screen_x) + 2, 10, str(int(t)))
                elif t % step == 0:
                     h = 6
                else: h = 4
                
                painter.drawLine(int(screen_x), 24, int(screen_x), 24 - h)
                
            t += step

    def _draw_vertical(self, painter):
        h_widget = self.height()
        screen_tick_target = 60
        doc_tick = screen_tick_target / self.zoom
        
        # Round to nice number
        import math
        exp = math.floor(math.log10(doc_tick or 1))
        step = 10**exp
        if doc_tick / step >= 5: step *= 5
        elif doc_tick / step >= 2: step *= 2
        
        start_doc = self.offset
        end_doc = self.offset + h_widget / self.zoom
        
        start_tick = (start_doc // step) * step
        
        t = start_tick
        while t < end_doc + step:
            # Map doc T to screen Y
            screen_y = (t - self.offset) * self.zoom
            
            if 0 <= screen_y <= h_widget:
                if t % (step * 2) == 0:
                     l = 10
                     # Save/Rotate for text? Vertical text is messy in Qt simple draw
                     painter.save()
                     painter.translate(2, int(screen_y) + 10)
                     painter.rotate(-90)
                     painter.drawText(0, 0, str(int(t)))
                     painter.restore()
                elif t % step == 0:
                     l = 6
                else: l = 4
                
                painter.drawLine(24, int(screen_y), 24 - l, int(screen_y))
                
            t += step
