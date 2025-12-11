from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QPainter, QColor
from PySide6.QtWidgets import QApplication
from .tool import Tool
from ..core.document import Document


class ColorPickerTool(Tool):
    """Eyedropper tool - samples colors from the canvas composite."""
    
    def __init__(self, document, session):
        super().__init__(document, session)
        self.name = "Color Picker"
    
    def mouse_press(self, pos: QPoint):
        # Check for right-click to set secondary color
        is_secondary = QApplication.mouseButtons() & Qt.MouseButton.RightButton
        self._sample_color(pos, is_secondary=is_secondary)

    def mouse_move(self, pos: QPoint):
        pass

    def mouse_release(self, pos: QPoint):
        pass
    
    def _sample_color(self, pos: QPoint, is_secondary: bool = False):
        """Sample color from the rendered document composite."""
        if not self.document:
            return
            
        # Render full composite to get accurate color
        rendered = self.document.render()
        
        # Bounds check
        if pos.x() < 0 or pos.y() < 0:
            return
        if pos.x() >= rendered.width() or pos.y() >= rendered.height():
            return
        
        # Get pixel color
        color = rendered.pixelColor(pos)
        
        # Set session color
        if is_secondary:
            self.session.secondary_color = color
        else:
            self.session.primary_color = color

