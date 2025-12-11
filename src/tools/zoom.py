from PySide6.QtCore import QPoint, Qt
from .tool import Tool
from ..core.document import Document

class ZoomTool(Tool):
    def __init__(self, document, session):
        super().__init__(document, session)
        self.name = "Zoom"
        self.cursor = Qt.CursorShape.PointingHandCursor # Or MagnifyingGlass if available

    def mouse_release(self, pos: QPoint):
        # We rely on mouse press for immediate action or release?
        # Standard is press for tools often, but release for "actions".
        # Let's use release to match paint.net (chk behavior? usually click).
        # Actually used press in draft. Let's use release to be safe.
        pass

    def mouse_press(self, pos: QPoint):
        from PySide6.QtWidgets import QApplication
        from PySide6.QtCore import Qt
        
        # Determine button
        # Tool doesn't get event button directly in signature?
        # src/tools/tool.py: mouse_press(pos).
        # src/ui/canvas.py: calls mouse_press(world_pos).
        # It swallows the event details.
        # We need to check QApplication.mouseButtons() or modify Tool signature.
        # Modifying signature is invasive. 
        # Checking QApplication.mouseButtons() works.
        
        buttons = QApplication.mouseButtons()
        
        if buttons & Qt.MouseButton.LeftButton:
            self.session.zoom_action_triggered.emit(1.2)
        elif buttons & Qt.MouseButton.RightButton:
             self.session.zoom_action_triggered.emit(1.0 / 1.2)

    def mouse_move(self, pos: QPoint):
        pass
