from PySide6.QtCore import QPoint, Qt, QRect
from PySide6.QtGui import QPainter, QColor, QFont, QPen
from PySide6.QtWidgets import QInputDialog
from .tool import Tool
from ..core.document import Document
from ..core.commands import CanvasCommand

class TextTool(Tool):
    def __init__(self, document, session):
        super().__init__(document, session)
        self.name = "Text"
        self.text = ""
        self.font = QFont("Arial", 12)

    def mouse_press(self, pos: QPoint):
        # Text tool usually opens a dialog or places a cursor.
        # For V1, let's use a Dialog.
        text, ok = QInputDialog.getText(None, "Text Tool", "Enter Text:")
        if ok and text:
            self.text = text
            self.draw_text(pos)
    
    def mouse_move(self, pos: QPoint):
        pass

    def mouse_release(self, pos: QPoint):
        pass

    def draw_text(self, pos: QPoint):
        layer = self.document.get_active_layer()
        if layer:
            cmd = CanvasCommand(layer)
            painter = QPainter(layer.image)
            if self.document.has_selection:
                painter.setClipRegion(self.document.get_selection_region())
                
            painter.setFont(self.font)
            color = self.session.primary_color
            painter.setPen(color)
            painter.drawText(pos, self.text)
            painter.end()
            
            cmd.capture_after()
            self.document.history.push(cmd)
            self.document.content_changed.emit()
