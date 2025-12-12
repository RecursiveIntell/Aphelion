from src.core.plugins import AphelionPlugin, PluginType
from src.tools.tool import Tool
from PySide6.QtGui import QPainter, QColor, QPen
from PySide6.QtCore import Qt, QPoint

class StarStampTool(Tool):
    def __init__(self, document, session):
        super().__init__(document, session)
        self.name = "Star Stamp"
        
    def mouse_press(self, pos: QPoint):
        if not self.document: return
        
        layer = self.document.get_active_layer()
        if not layer: return
        
        # Draw a Star directly on the layer
        # For undo support, we should technically use a specialized Command.
        # But for this simple plugin example, we'll direct draw + generic CanvasCommand?
        # The tool system usually handles "Active Tool" drawing or commands.
        # Let's adhere to "Direct Draw" for MVP plugin (destructive).
        # Or better: construct a CanvasCommand to capture before/after.
        
        from src.core.commands import CanvasCommand
        cmd = CanvasCommand(layer)
        
        painter = QPainter(layer.image)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Use Primary Color
        color = self.session.primary_color
        painter.setBrush(color)
        painter.setPen(Qt.NoPen)
        
        # Draw Star
        size = self.session.brush_size * 2
        
        # Simple Diamond Star
        #    *
        #  * * *
        #    *
        painter.translate(pos)
        painter.rotate(45)
        painter.drawRect(-size//2, -size//2, size, size)
        
        painter.end()
        
        cmd.capture_after()
        self.document.history.push(cmd)
        self.document.content_changed.emit()

    def mouse_move(self, pos: QPoint):
        pass
        
    def mouse_release(self, pos: QPoint):
        pass

class StarPlugin(AphelionPlugin):
    name = "Star Stamp"
    version = "1.0"
    type = PluginType.TOOL
    description = "A tool that stamps stars."
    
    def initialize(self, context):
        register_tool = context.get("register_tool")
        if register_tool:
            # We don't have an icon, so it will use "St" text
            register_tool("Star Stamp", StarStampTool, None, "Y")
