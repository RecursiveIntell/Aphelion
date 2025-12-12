"""
Command classes for undo/redo system.

Optimized with dirty-rect tracking and byte-based memory management.
"""
from PySide6.QtGui import QImage, QPainter
from PySide6.QtCore import QRect
from .history import Command
from .layer import Layer


class CanvasCommand(Command):
    """
    Undoable command for canvas/layer modifications.
    
    Uses dirty-rect tracking to store only the changed region,
    dramatically reducing memory usage for local edits.
    """
    
    def __init__(self, layer: Layer, target: str = "image", dirty_rect: QRect = None):
        """
        Initialize canvas command.
        
        Args:
            layer: The layer being modified
            target: "image" or "mask"
            dirty_rect: Optional bounding rect of changes. If None, captures full image.
        """
        self.layer = layer
        self.target = target
        self.dirty_rect = dirty_rect
        
        # Capture state BEFORE
        self._capture_source_image()
        self.before_data = self._capture_region()
        self.after_data = None  # Lazy - captured after change
    
    def _capture_source_image(self) -> QImage:
        """Get the current image being tracked."""
        if self.target == "image":
            return self.layer.image
        elif self.target == "mask":
            return self.layer.mask
        return None
    
    def _capture_region(self) -> tuple:
        """
        Capture the current state of the dirty region.
        
        Returns:
            Tuple of (rect, image_data) where image_data is the cropped region
        """
        source = self._capture_source_image()
        if source is None:
            return (None, None)
        
        if self.dirty_rect is None or not self.dirty_rect.isValid():
            # Fall back to full image copy
            rect = source.rect()
            return (rect, source.copy())
        else:
            # Clip dirty_rect to image bounds
            rect = self.dirty_rect.intersected(source.rect())
            if rect.isEmpty():
                return (None, None)
            return (rect, source.copy(rect))
    
    def capture_after(self):
        """Capture the state after modification."""
        self.after_data = self._capture_region()
    
    def set_dirty_rect(self, rect: QRect):
        """Update the dirty rect (call before capture_after)."""
        self.dirty_rect = rect
    
    def execute(self):
        """Redo - restore after state."""
        if self.after_data and self.after_data[0]:
            self._restore(self.after_data)
    
    def undo(self):
        """Undo - restore before state."""
        if self.before_data and self.before_data[0]:
            self._restore(self.before_data)
    
    def _restore(self, data: tuple):
        """Restore a captured region to the layer."""
        rect, region_image = data
        if rect is None or region_image is None:
            return
        
        if self.target == "image":
            painter = QPainter(self.layer.image)
            # Clear the region first (for proper alpha handling)
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source)
            painter.drawImage(rect.topLeft(), region_image)
            painter.end()
        elif self.target == "mask":
            if self.layer.mask:
                painter = QPainter(self.layer.mask)
                painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source)
                painter.drawImage(rect.topLeft(), region_image)
                painter.end()
    
    def memory_bytes(self) -> int:
        """Estimate memory usage of this command in bytes."""
        total = 0
        
        if self.before_data and self.before_data[1]:
            img = self.before_data[1]
            total += img.sizeInBytes()
        
        if self.after_data and self.after_data[1]:
            img = self.after_data[1]
            total += img.sizeInBytes()
        
        return total


class LayerPropertyCommand(Command):
    """Command for changing layer properties (name, opacity, visibility, etc.)."""
    
    def __init__(self, layer: Layer, property_name: str, old_value, new_value, signal_callback=None):
        self.layer = layer
        self.property_name = property_name
        self.old_value = old_value
        self.new_value = new_value
        self.signal_callback = signal_callback

    def execute(self):
        setattr(self.layer, self.property_name, self.new_value)
        if self.signal_callback:
            self.signal_callback()

    def undo(self):
        setattr(self.layer, self.property_name, self.old_value)
        if self.signal_callback:
            self.signal_callback()
    
    def memory_bytes(self) -> int:
        """Property commands use negligible memory."""
        return 64  # Small fixed overhead


class LayerStructureCommand(Command):
    """Command for layer add/remove/move operations."""
    
    def __init__(self, document, action: str, layer: Layer = None, index: int = -1, previous_index: int = -1):
        self.document = document
        self.action = action  # "add", "remove", "move"
        self.layer = layer
        self.index = index
        self.previous_index = previous_index

    def execute(self):
        if self.action == "add":
            self.document.layers.insert(self.index, self.layer)
            self.document.layer_added.emit(self.layer)
            self.document.set_active_layer(self.index)
        elif self.action == "remove":
            if self.document.layers[self.index] == self.layer:
                self.document.layers.pop(self.index)
                self.document.layer_removed.emit(self.layer.id)
                if self.document._active_layer_index >= len(self.document.layers):
                    self.document.set_active_layer(len(self.document.layers) - 1)
        elif self.action == "move":
            layer = self.document.layers.pop(self.previous_index)
            self.document.layers.insert(self.index, layer)
            self.document.content_changed.emit()
            if self.document.get_active_layer() == layer:
                self.document.set_active_layer(self.index)

    def undo(self):
        if self.action == "add":
            if self.document.layers[self.index] == self.layer:
                self.document.layers.pop(self.index)
                self.document.layer_removed.emit(self.layer.id)
                self.document.set_active_layer(max(0, self.index - 1))
        elif self.action == "remove":
            self.document.layers.insert(self.index, self.layer)
            self.document.layer_added.emit(self.layer)
            self.document.set_active_layer(self.index)
        elif self.action == "move":
            layer = self.document.layers.pop(self.index)
            self.document.layers.insert(self.previous_index, layer)
            self.document.content_changed.emit()
            if self.document.get_active_layer() == layer:
                self.document.set_active_layer(self.previous_index)
    
    def memory_bytes(self) -> int:
        """Structure commands reference layers, don't copy them."""
        return 128  # Small fixed overhead


class DocumentPropertyCommand(Command):
    """Command for document-level property changes."""
    
    def __init__(self, document, property_name: str, old_value, new_value, signal_callback=None):
        self.document = document
        self.property_name = property_name
        self.old_value = old_value
        self.new_value = new_value
        self.signal_callback = signal_callback
        
    def execute(self):
        setattr(self.document, self.property_name, self.new_value)
        if self.signal_callback:
            self.signal_callback()

    def undo(self):
        setattr(self.document, self.property_name, self.old_value)
        if self.signal_callback:
            self.signal_callback()
    
    def memory_bytes(self) -> int:
        return 128


class SelectionCommand(Command):
    """Command for selection mask changes."""
    
    def __init__(self, document, old_mask: QImage, new_mask: QImage):
        self.document = document
        self.old_mask = old_mask
        self.new_mask = new_mask
    
    def execute(self):
        self.document.selection_mask = self.new_mask.copy()
        self.document._update_selection_region()
        self.document.selection_changed.emit()

    def undo(self):
        self.document.selection_mask = self.old_mask.copy()
        self.document._update_selection_region()
        self.document.selection_changed.emit()
    
    def memory_bytes(self) -> int:
        total = 0
        if self.old_mask:
            total += self.old_mask.sizeInBytes()
        if self.new_mask:
            total += self.new_mask.sizeInBytes()
        return total


class MacroCommand(Command):
    """Compound command that groups multiple commands."""
    
    def __init__(self, name: str):
        super().__init__()
        self.name = name
        self.commands: list[Command] = []

    def add_command(self, command: Command):
        self.commands.append(command)

    def execute(self):
        for command in self.commands:
            command.execute()

    def undo(self):
        for command in reversed(self.commands):
            command.undo()
    
    def redo(self):
        for command in self.commands:
            command.execute()
    
    def memory_bytes(self) -> int:
        return sum(cmd.memory_bytes() for cmd in self.commands)
