from PySide6.QtGui import QPainter, QPen, QColor, QBrush
from PySide6.QtCore import Qt, QPoint, QRect
from PySide6.QtWidgets import QApplication
from .tool import Tool

class RectangleSelectTool(Tool):
    def __init__(self, document, session):
        super().__init__(document, session)
        self.name = "Rectangle Select"
        self.is_selecting = False
        self.start_pos = QPoint()
        self.current_pos = QPoint()

    def mouse_press(self, pos: QPoint):
        self.is_selecting = True
        self.start_pos = pos
        self.current_pos = pos
        # For now, replace selection on new press
        # Future: Check modifiers for Add/Subtract

    def mouse_move(self, pos: QPoint):
        if self.is_selecting:
            self.current_pos = pos
            # We don't commit yet, we just update UI (transient)
            # But the CanvasWidget needs to know what to draw.
            # We can use a signal or direct access if cleaner.
            # Standard pattern: Tool draws transient, commit on release.
            self.document.content_changed.emit() # Force redraw to show overlay

    def mouse_release(self, pos: QPoint):
        if self.is_selecting:
            self.is_selecting = False
            self.current_pos = pos
            
            # Commit selection to Document
            rect = QRect(self.start_pos, self.current_pos).normalized()
            
            # Determine mode
            mode = self.session.selection_mode
            modifiers = QApplication.keyboardModifiers()
            if modifiers & Qt.KeyboardModifier.ShiftModifier:
                mode = "add"
            elif modifiers & Qt.KeyboardModifier.AltModifier:
                mode = "subtract"
            elif modifiers & Qt.KeyboardModifier.ControlModifier:
                mode = "intersect"
                
            self.document.set_selection(rect, mode)

    # Draw transient overlay (Called by CanvasWidget ideally, or we assume CanvasWidget handles 'dragging' state)
    # A cleaner way: Tool has a `draw_overlay(painter)` method.
