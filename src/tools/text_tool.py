from PySide6.QtGui import QPainter, QPen, QColor, QFont, QFontMetrics
from PySide6.QtCore import Qt, QPoint, QRect
from PySide6.QtWidgets import QLineEdit, QGraphicsProxyWidget
from .tool import Tool
from ..core.commands import CanvasCommand

class TextTool(Tool):
    def __init__(self, document, session):
        super().__init__(document, session)
        self.name = "Text"
        self.text_pos = QPoint()
        self.is_editing = False
        self.editor = None # QLineEdit or similar overlay
        self.font = QFont("Arial", 12)
        
    def mouse_press(self, pos: QPoint):
        if self.is_editing:
            # Commit current text
            self.commit_text()
            self.is_editing = False
            # If clicked elsewhere, maybe start new text?
            # For MVP, click commits and stops.
        else:
            self.start_editing(pos)
            
    def mouse_move(self, pos: QPoint):
        pass

    def mouse_release(self, pos: QPoint):
        pass

    def start_editing(self, pos: QPoint):
        self.is_editing = True
        self.text_pos = pos
        # We need an input widget overlay.
        # This is tricky because Tool doesn't own widgets easily.
        # But we can ask Session -> MainWindow -> Canvas?
        # Or we can just use QInputDialog for "Phase 2.3 MVP" simplicity?
        # Real Photoshop text tool types on canvas.
        # Let's use QInputDialog for now to ensure robustness, 
        # then upgrade to on-canvas widget if time permits.
        
        # Actually, let's try to be better than Paint.NET MVP.
        # We can simulate typing by capturing key events if we had them.
        # But Tool doesn't receive keys yet (CanvasWidget needs update).
        
        # Fallback: QSimple InputDialog
        from PySide6.QtWidgets import QInputDialog
        text, ok = QInputDialog.getText(None, "Enter Text", "Text:")
        if ok and text:
            self.text = text
            self.commit_text()
        self.is_editing = False

    def commit_text(self):
        active_layer = self.document.get_active_layer()
        if not active_layer: return
        
        target = self.session.edit_target
        if target == "mask" and not active_layer.mask:
            target = "image"
            
        cmd = CanvasCommand(active_layer, target=target)
        
        target_image = active_layer.image if target == "image" else active_layer.mask
        
        painter = QPainter(target_image)
        
        if self.document.has_selection and hasattr(self.document, '_cached_selection_region'):
            painter.setClipRegion(self.document._cached_selection_region)
            
        painter.setPen(QPen(self.session.primary_color))
        painter.setFont(self.font)
        painter.drawText(self.text_pos, self.text)
        painter.end()
        
        cmd.capture_after()
        self.document.history.push(cmd)
        self.document.content_changed.emit()

    def draw_overlay(self, painter):
        pass
