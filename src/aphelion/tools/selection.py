from PySide6.QtCore import QPoint, QRect, Qt
from PySide6.QtGui import QPainter, QColor, QPainterPath, QImage
from PySide6.QtWidgets import QApplication
from .tool import Tool
from ..core.document import Document
from ..utils.flood_fill import flood_fill_mask

class EllipseSelectTool(Tool):
    def __init__(self, document, session):
        super().__init__(document, session)
        self.name = "Ellipse Select"
        self.start_pos = None
        self.current_pos = None
        self.is_dragging = False

    def mouse_press(self, pos: QPoint):
        self.start_pos = pos
        self.current_pos = pos
        self.is_dragging = True

    def mouse_move(self, pos: QPoint):
        if self.is_dragging:
            self.current_pos = pos
            self.document.content_changed.emit() # Trigger overlay redraw

    def mouse_release(self, pos: QPoint):
        if self.is_dragging:
            self.is_dragging = False
            rect = QRect(self.start_pos, pos).normalized()
            if rect.width() > 0 and rect.height() > 0:
                # We need to set selection with an Ellipse shape.
                # Document.set_selection takes a RECT currently and treats it as a rect.
                # We need a generic set_selection_mask or modify set_selection to accept a shape/mask.
                
                # Let's manually create the mask for the ellipse
                mask = QImage(self.document.size, QImage.Format.Format_Alpha8)
                mask.fill(0)
                painter = QPainter(mask)
                painter.setBrush(Qt.white)
                painter.setPen(Qt.NoPen)
                painter.drawEllipse(rect)
                painter.end()
                
                # Determine mode
                mode = self.session.selection_mode
                modifiers = QApplication.keyboardModifiers()
                if modifiers & Qt.KeyboardModifier.ShiftModifier:
                    mode = "add"
                elif modifiers & Qt.KeyboardModifier.AltModifier:
                    mode = "subtract"
                elif modifiers & Qt.KeyboardModifier.ControlModifier:
                    mode = "intersect"

                self.document.combine_selection(mask, mode)
                
    def _create_selection_command(self, new_partial_mask, operation):
        # This logic duplicates Document.set_selection logic mostly.
        # Ideally Document has a method `combine_selection(mask, operation)`
        from ..core.commands import SelectionCommand
        
        old_mask = self.document.selection_mask.copy()
        final_mask = self.document.selection_mask.copy()
        
        painter = QPainter(final_mask)
        if operation == "replace":
            final_mask.fill(0)
            painter.drawImage(0, 0, new_partial_mask)
        # TODO: Add/Subtract logic (Phase 3 task? Yes.)
        painter.end()
        
        return SelectionCommand(self.document, old_mask, final_mask)

    def draw_overlay(self, painter: QPainter):
        if self.is_dragging:
            rect = QRect(self.start_pos, self.current_pos).normalized()
            painter.setPen(Qt.DashLine)
            painter.drawEllipse(rect)

class LassoSelectTool(Tool):
    def __init__(self, document, session):
        super().__init__(document, session)
        self.name = "Lasso Select"
        self.path = None
        self.is_dragging = False

    def mouse_press(self, pos: QPoint):
        self.path = QPainterPath(pos)
        self.is_dragging = True

    def mouse_move(self, pos: QPoint):
        if self.is_dragging:
            self.path.lineTo(pos)
            self.document.content_changed.emit()

    def mouse_release(self, pos: QPoint):
        if self.is_dragging:
            self.is_dragging = False
            self.path.closeSubpath()
            
            # Create mask
            mask = QImage(self.document.size, QImage.Format.Format_Alpha8)
            mask.fill(0)
            painter = QPainter(mask)
            painter.setBrush(Qt.white)
            painter.setPen(Qt.NoPen)
            painter.drawPath(self.path)
            painter.end()
            
            # Determine mode
            mode = self.session.selection_mode
            modifiers = QApplication.keyboardModifiers()
            if modifiers & Qt.KeyboardModifier.ShiftModifier:
                mode = "add"
            elif modifiers & Qt.KeyboardModifier.AltModifier:
                mode = "subtract"
            elif modifiers & Qt.KeyboardModifier.ControlModifier:
                mode = "intersect"

            self.document.combine_selection(mask, mode)
            self.path = None

    def _create_selection_command(self, new_partial_mask, operation):
        # Wrapper to duplicate logic (should be in Document)
        from ..core.commands import SelectionCommand
        old_mask = self.document.selection_mask.copy()
        final_mask = self.document.selection_mask.copy()
        painter = QPainter(final_mask)
        if operation == "replace":
             final_mask.fill(0)
             painter.drawImage(0, 0, new_partial_mask)
        painter.end()
        return SelectionCommand(self.document, old_mask, final_mask)

    def draw_overlay(self, painter: QPainter):
        if self.is_dragging and self.path:
            painter.setPen(Qt.DashLine)
            painter.drawPath(self.path)

class MagicWandTool(Tool):
    def __init__(self, document, session):
        super().__init__(document, session)
        self.name = "Magic Wand"

    def mouse_press(self, pos: QPoint):
        # Flood fill from pos
        layer = self.document.get_active_layer()
        if not layer: return

        # Get target color
        target_color = layer.image.pixelColor(pos)

        # Use tolerance from session
        tolerance = self.session.tolerance if self.session else 32

        # Perform Flood Fill -> Generate Mask
        # This is expensive. Should run in thread? For V1, synchronous.
        mask = self.flood_fill(layer.image, pos, target_color, tolerance)
        
        # Apply
        mode = self.session.selection_mode
        modifiers = QApplication.keyboardModifiers()
        if modifiers & Qt.KeyboardModifier.ShiftModifier:
            mode = "add"
        elif modifiers & Qt.KeyboardModifier.AltModifier:
            mode = "subtract"
        elif modifiers & Qt.KeyboardModifier.ControlModifier:
            mode = "intersect"

        self.document.combine_selection(mask, mode)

    def mouse_move(self, pos: QPoint):
        pass

    def mouse_release(self, pos: QPoint):
        pass

    def flood_fill(self, image: QImage, seed: QPoint, target_color: QColor, tolerance: int) -> QImage:
        """Returns Alpha8 mask using shared flood fill implementation."""
        return flood_fill_mask(image, seed, tolerance, use_alpha=True)
