from PySide6.QtGui import QImage, QPainter
from .history import Command
from .layer import Layer

class CanvasCommand(Command):
    def __init__(self, layer: Layer, target: str = "image"):
        self.layer = layer
        self.target = target
        
        # Capture state BEFORE
        if self.target == "image":
             self.before_image = layer.image.copy()
        elif self.target == "mask":
             if layer.mask:
                 self.before_image = layer.mask.copy()
             else:
                 self.before_image = None
                 
        self.after_image = None # To be captured after change

    def capture_after(self):
        if self.target == "image":
            self.after_image = self.layer.image.copy()
        elif self.target == "mask":
            if self.layer.mask:
                self.after_image = self.layer.mask.copy()
            else:
                self.after_image = None

    def execute(self):
        # Redo
        if self.after_image is not None:
            self._restore(self.after_image)
        elif self.target == "mask" and self.after_image is None:
             # Mask might have been deleted/not created
             if self.layer.mask:
                 self.layer.delete_mask()

    def undo(self):
        # Undo
        if self.before_image is not None:
             self._restore(self.before_image)
        elif self.target == "mask" and self.before_image is None:
             # Before was None => Delete mask
             if self.layer.mask:
                 self.layer.delete_mask()
        
    def _restore(self, source: QImage):
        # Restore pixels
        if self.target == "image":
             self.layer.image = source.copy()
        elif self.target == "mask":
             self.layer.mask = source.copy()

class LayerPropertyCommand(Command):
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

class LayerStructureCommand(Command):
    def __init__(self, document, action: str, layer: Layer = None, index: int = -1, previous_index: int = -1):
        self.document = document
        self.action = action # "add", "remove", "move"
        self.layer = layer
        self.index = index
        self.previous_index = previous_index

    def execute(self):
        if self.action == "add":
            self.document.layers.insert(self.index, self.layer)
            self.document.layer_added.emit(self.layer)
            self.document.set_active_layer(self.index)
        elif self.action == "remove":
            # We assume layer is already in document at index
            # But for robustness in redo, we use index
            if self.document.layers[self.index] == self.layer:
                 self.document.layers.pop(self.index)
                 self.document.layer_removed.emit(self.layer.id)
                 # reset active layer if needed
                 if self.document._active_layer_index >= len(self.document.layers):
                     self.document.set_active_layer(len(self.document.layers) - 1)
        elif self.action == "move":
             layer = self.document.layers.pop(self.previous_index)
             self.document.layers.insert(self.index, layer)
             self.document.content_changed.emit() # Layer order changed
             if self.document.get_active_layer() == layer:
                 self.document.set_active_layer(self.index)

    def undo(self):
        if self.action == "add":
            # Undo add = remove
            if self.document.layers[self.index] == self.layer:
                self.document.layers.pop(self.index)
                self.document.layer_removed.emit(self.layer.id)
                self.document.set_active_layer(max(0, self.index - 1))
        elif self.action == "remove":
            # Undo remove = add back
            self.document.layers.insert(self.index, self.layer)
            self.document.layer_added.emit(self.layer)
            self.document.set_active_layer(self.index)
        elif self.action == "move":
            # Undo move = move back
            layer = self.document.layers.pop(self.index)
            self.document.layers.insert(self.previous_index, layer)
            self.document.content_changed.emit()
            if self.document.get_active_layer() == layer:
                 self.document.set_active_layer(self.previous_index)

class DocumentPropertyCommand(Command):
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

class SelectionCommand(Command):
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

class MacroCommand(Command):
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
            command.redo()
