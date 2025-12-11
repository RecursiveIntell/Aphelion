from PySide6.QtCore import QPoint, Qt, QRect, QPointF
from PySide6.QtGui import QPainter, QImage, QPixmap
from .tool import Tool
from ..core.document import Document
from ..core.commands import CanvasCommand

class MoveSelectedPixelsTool(Tool):
    def __init__(self, document, session):
        super().__init__(document, session)
        self.name = "Move Selected Pixels"
        self.is_dragging = False
        self.last_pos = QPoint()
        self.floating_buffer = None # The pixels being moved
        self.floating_pos = QPoint()
        self.original_selection_rect = QRect()
        
    def mouse_press(self, pos: QPoint):
        if not self.document.has_selection:
            return # Should we pick up full layer? Maybe.
        
        self.is_dragging = True
        self.last_pos = pos
        
        # 1. Cut pixels from active layer at selection
        layer = self.document.get_active_layer()
        if not layer: return
        
        # We need to capture the current layer state for Undo IF we commit immediately?
        # Typically "Move" is complex: 
        #   - Cut pixels -> Create floating layer/buffer
        #   - Move buffer
        #   - Paste buffer on release/commit
        
        # Simplified:
        # 1. Capture "Before" state (CanvasCommand)
        # 2. Extract selection to QImage buffer
        # 3. Clear selection from layer
        # 4. On drag, render buffer on overlay
        # 5. On release, paste buffer to layer and push command
        
        # ACTUALLY: Paint.NET renders it live.
        # Problem: Combining "Cut" and "Paste" in one mouse drag is tricky for Undo if we want intermediate feedback.
        # Better:
        # Mouse Press: Cut pixels, store in self.floating_buffer. Clear area in layer.
        
        # We need a command for the "Cut" part? Or the whole "Cut-Move-Paste" sequence?
        # Usually it's one atomic "Move Select" action.
        
        # Let's save the layer state first
        self.cmd = CanvasCommand(layer)
        
        region = self.document.get_selection_region()
        rect = region.boundingRect()
        self.original_selection_rect = rect
        self.floating_pos = rect.topLeft()
        
        # Copy
        self.floating_buffer = layer.image.copy(rect)
        # Apply mask to buffer? (Only copy selected pixels)
        # Yes, we need to mask out unselected pixels in the rect.
        # Complex.
        
        # Simplified V1: Just move rect.
        
        # Clear original area
        painter = QPainter(layer.image)
        painter.setClipRegion(region)
        # Clear
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
        painter.fillRect(rect, Qt.transparent)
        painter.end()
        
        self.document.content_changed.emit()

    def mouse_move(self, pos: QPoint):
        if self.is_dragging:
            delta = pos - self.last_pos
            self.floating_pos += delta
            self.last_pos = pos
            # Ideally we also move the selection mask itself with the pixels?
            # Yes, Paint.NET does that.
            self.document.content_changed.emit()

    def mouse_release(self, pos: QPoint):
        if self.is_dragging:
            self.is_dragging = False
            
            # Commit
            layer = self.document.get_active_layer()
            if layer and self.floating_buffer:
                painter = QPainter(layer.image)
                # We need to mask it again? 
                # If we just draw the buffer, we draw the rect.
                painter.drawImage(self.floating_pos, self.floating_buffer)
                painter.end()
                
                # Also move the selection region?
                # We need to translate the selection mask to new position.
                offset = self.floating_pos - self.original_selection_rect.topLeft()
                
                # Update mask
                # Access mask directly (hacky)
                # Better: Create command to update mask too?
                # For now let's just update mask in place (not undoable separately, bundled with pixels?)
                # If we bundle it, we need `MovePixelsCommand` that does both.
                # CanvasCommand only handles Layer Image.
                
                # Let's ignore mask update for a sec, just pixels.
                
                self.cmd.capture_after()
                self.document.history.push(self.cmd)
                self.document.content_changed.emit()
                self.floating_buffer = None

    def draw_overlay(self, painter: QPainter):
        if self.is_dragging and self.floating_buffer:
            painter.drawImage(self.floating_pos, self.floating_buffer)
            # Draw border
            painter.setPen(Qt.DashLine)
            painter.drawRect(QRect(self.floating_pos, self.floating_buffer.size()))

class MoveSelectionTool(Tool):
    def __init__(self, document, session):
        super().__init__(document, session)
        self.name = "Move Selection"
        # Moves the mask, not pixels.
        pass
    
    def mouse_press(self, pos: QPoint):
        pass
    def mouse_move(self, pos: QPoint):
        pass
    def mouse_release(self, pos: QPoint):
        pass
