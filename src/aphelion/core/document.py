from PySide6.QtCore import QObject, Signal, QSize, QRect, Qt, QPoint
from PySide6.QtGui import QImage, QColor, QPainter, QRegion, QBitmap
from .layer import Layer
from .history import HistoryManager
from .commands import DocumentPropertyCommand, SelectionCommand, LayerStructureCommand, MacroCommand, CanvasCommand
from PySide6.QtGui import QTransform
from ..utils.image_processing import (
    qimage_alpha8_to_numpy, numpy_to_qimage_alpha8,
    gaussian_blur_np, morphological_dilate, morphological_erode
)
from .renderer_cairo import CairoRenderer

class Document(QObject):
    # Signals to notify UI
    layer_added = Signal(object) # Layer object
    layer_removed = Signal(str) # Layer ID
    active_layer_changed = Signal(object) # Layer object
    content_changed = Signal() # Helper for simple redraw requests
    selection_changed = Signal()

    def __init__(self, width: int, height: int):
        super().__init__()
        self.size = QSize(width, height)
        self.layers: list[Layer] = []
        self._active_layer_index = -1
        self.history = HistoryManager()
        self.file_path = None  # Path to saved project file
        
        # Cairo-based renderer for layer compositing
        self._renderer = CairoRenderer()
        
        # Selection Mask (Alpha8: 0=Unselected, 255=Selected)
        self.selection_mask = QImage(width, height, QImage.Format.Format_Alpha8)
        self.selection_mask.fill(0) 
        self.has_selection = False
        self.selection_region = QRegion()
        
        # Connect content_changed to invalidate renderer cache
        self.content_changed.connect(self._invalidate_render_cache)

    def resize_image(self, width: int, height: int):
        if self.size.width() == width and self.size.height() == height:
            return
            
        new_size = QSize(width, height)
        macro = MacroCommand(f"Resize Image to {width}x{height}")
        
        # 1. Properties
        prop_cmd = DocumentPropertyCommand(self, "size", self.size, new_size, 
                                          signal_callback=lambda: self.content_changed.emit())
        macro.add_command(prop_cmd)

        # 2. Layers
        canvas_cmds = []
        for layer in self.layers:
            cmd = CanvasCommand(layer)
            macro.add_command(cmd)
            canvas_cmds.append(cmd)
            
        # 3. Selection
        sel_cmd = SelectionCommand(self, self.selection_mask.copy(), self.selection_mask.copy())
        macro.add_command(sel_cmd)
        
        # Execute Property
        prop_cmd.execute()
        
        # Execute Logic
        for layer in self.layers:
            layer.image = layer.image.scaled(new_size, Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation)
        
        self.selection_mask = self.selection_mask.scaled(new_size, Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.FastTransformation)
        self._update_selection_region()
        
        # Capture After
        for cmd in canvas_cmds:
            cmd.capture_after()
        sel_cmd.new_mask = self.selection_mask.copy()
        
        self.history.push(macro)
        self.content_changed.emit()
        self.selection_changed.emit()

    def resize_canvas(self, width: int, height: int, anchor=Qt.AlignCenter):
        if self.size.width() == width and self.size.height() == height:
            return
            
        new_size = QSize(width, height)
        macro = MacroCommand(f"Resize Canvas to {width}x{height}")
        
        prop_cmd = DocumentPropertyCommand(self, "size", self.size, new_size, 
                                          signal_callback=lambda: self.content_changed.emit())
        macro.add_command(prop_cmd)
        
        canvas_cmds = []
        for layer in self.layers:
            cmd = CanvasCommand(layer)
            macro.add_command(cmd)
            canvas_cmds.append(cmd)
            
        sel_cmd = SelectionCommand(self, self.selection_mask.copy(), self.selection_mask.copy())
        macro.add_command(sel_cmd)
        
        old_size_w = self.size.width()
        old_size_h = self.size.height()
        
        # Do it
        prop_cmd.execute()
        
        # Calculate offset
        dx, dy = 0, 0
        if anchor == Qt.AlignCenter:
            dx = (width - old_size_w) // 2
            dy = (height - old_size_h) // 2
        elif anchor == Qt.AlignTop | Qt.AlignLeft:
            dx = 0
            dy = 0
        elif anchor == Qt.AlignTop | Qt.AlignHCenter:
            dx = (width - old_size_w) // 2
            dy = 0
        elif anchor == Qt.AlignTop | Qt.AlignRight:
            dx = width - old_size_w
            dy = 0
        elif anchor == Qt.AlignVCenter | Qt.AlignLeft:
            dx = 0
            dy = (height - old_size_h) // 2
        elif anchor == Qt.AlignVCenter | Qt.AlignRight:
            dx = width - old_size_w
            dy = (height - old_size_h) // 2
        elif anchor == Qt.AlignBottom | Qt.AlignLeft:
            dx = 0
            dy = height - old_size_h
        elif anchor == Qt.AlignBottom | Qt.AlignHCenter:
            dx = (width - old_size_w) // 2
            dy = height - old_size_h
        elif anchor == Qt.AlignBottom | Qt.AlignRight:
            dx = width - old_size_w
            dy = height - old_size_h
        else: # Default center
            dx = (width - old_size_w) // 2
            dy = (height - old_size_h) // 2
        
        # Resize Layers (Crop/Expand)
        for layer in self.layers:
            new_img = QImage(new_size, QImage.Format.Format_ARGB32_Premultiplied)
            new_img.fill(0)
            painter = QPainter(new_img)
            painter.drawImage(dx, dy, layer.image)
            painter.end()
            layer.image = new_img
            
        # Resize Mask
        new_mask = QImage(new_size, QImage.Format.Format_Alpha8)
        new_mask.fill(0)
        painter = QPainter(new_mask)
        painter.drawImage(dx, dy, self.selection_mask)
        painter.end()
        self.selection_mask = new_mask
        self._update_selection_region()
        
        for cmd in canvas_cmds:
            cmd.capture_after()
        sel_cmd.new_mask = self.selection_mask.copy()
        
        self.history.push(macro)
        self.content_changed.emit()
        self.selection_changed.emit()

    def rotate_image(self, angle: float):
        macro = MacroCommand(f"Rotate {angle}")
        
        canvas_cmds = []
        for layer in self.layers:
             cmd = CanvasCommand(layer)
             macro.add_command(cmd)
             canvas_cmds.append(cmd)
             
        sel_cmd = SelectionCommand(self, self.selection_mask.copy(), self.selection_mask.copy())
        macro.add_command(sel_cmd)

        # Handle Size Change (90/270)
        if angle in [90, -90, 270, -270]:
             new_size = QSize(self.size.height(), self.size.width())
             prop_cmd = DocumentPropertyCommand(self, "size", self.size, new_size)
             macro.add_command(prop_cmd)
             prop_cmd.execute()
             
        transform = QTransform().rotate(angle)
        
        for layer in self.layers:
             layer.image = layer.image.transformed(transform, Qt.TransformationMode.SmoothTransformation)
             
        self.selection_mask = self.selection_mask.transformed(transform, Qt.TransformationMode.FastTransformation)
        self._update_selection_region()
        
        for cmd in canvas_cmds:
             cmd.capture_after()
        sel_cmd.new_mask = self.selection_mask.copy()
        
        self.history.push(macro)
        self.content_changed.emit()
        self.selection_changed.emit()

    def flip_image(self, horizontal: bool, vertical: bool):
        macro = MacroCommand("Flip Image")
        
        canvas_cmds = []
        for layer in self.layers:
             cmd = CanvasCommand(layer)
             macro.add_command(cmd)
             canvas_cmds.append(cmd)

        sel_cmd = SelectionCommand(self, self.selection_mask.copy(), self.selection_mask.copy())
        macro.add_command(sel_cmd)
        
        for layer in self.layers:
             layer.image = layer.image.mirrored(horizontal, vertical)
             
        self.selection_mask = self.selection_mask.mirrored(horizontal, vertical)
        self._update_selection_region()
        
        for cmd in canvas_cmds:
             cmd.capture_after()
        sel_cmd.new_mask = self.selection_mask.copy()
        
        self.history.push(macro)
        self.content_changed.emit()
        self.selection_changed.emit()

    def _resize_internal(self, new_size):
        # Legacy/Unused or removed.
        pass
        
    def flatten_image(self):
         if len(self.layers) < 1: return
         
         macro = MacroCommand("Flatten Image")
         
         # 1. Flatten
         flat_img = QImage(self.size, QImage.Format.Format_ARGB32_Premultiplied)
         flat_img.fill(Qt.white) # Background
         painter = QPainter(flat_img)
         for layer in self.layers:
             if layer.visible:
                 painter.setOpacity(layer.opacity)
                 # Blend mode... MVP Normal
                 painter.drawImage(0, 0, layer.image)
         painter.end()
         
         # 2. Remove all layers
         # We need to copy the list because we are modifying it
         cats = list(self.layers)
         for layer in reversed(cats):
             cmd = LayerStructureCommand(self, "remove", layer=layer, index=self.layers.index(layer))
             macro.add_command(cmd)
             cmd.execute()
             
         # 3. Add Flat Layer
         new_layer = Layer(self.size.width(), self.size.height(), "Background")
         new_layer.image = flat_img
         cmd = LayerStructureCommand(self, "add", layer=new_layer, index=0)
         macro.add_command(cmd)
         cmd.execute()
         
         self.history.push(macro)

    def merge_layer_down(self, index: int):
         if index <= 0 or index >= len(self.layers): return
         
         top = self.layers[index]
         bottom = self.layers[index-1]
         
         macro = MacroCommand("Merge Layer Down")
         
         # 1. Remove Top
         rm_cmd = LayerStructureCommand(self, "remove", layer=top, index=index)
         macro.add_command(rm_cmd)
         rm_cmd.execute() # Removes from list
         
         # 2. Update Bottom
         cv_cmd = CanvasCommand(bottom)
         macro.add_command(cv_cmd)
         
         painter = QPainter(bottom.image)
         painter.setOpacity(top.opacity)
         # Blend Modes...
         painter.drawImage(0, 0, top.image)
         painter.end()
         
         cv_cmd.capture_after()
         
         self.history.push(macro)
         self.content_changed.emit()

    def _invalidate_render_cache(self):
        """Invalidate the Cairo renderer cache when content changes."""
        for layer in self.layers:
            self._renderer.invalidate_layer(layer.id)
    
    def invalidate_layer_cache(self, layer_id: str):
        """Invalidate cache for a specific layer."""
        self._renderer.invalidate_layer(layer_id)

    def render(self, rect: QRect = None) -> QImage:
        """
        Render the document composite using Cairo backend.
        
        Args:
            rect: Optional clip rectangle (not yet implemented)
            
        Returns:
            QImage with composited layers
        """
        return self._renderer.render_to_qimage(self)

    def combine_selection(self, new_mask: QImage, operation: str = "replace"):
        """
        Combine a new mask with existing selection.
        operation: 'replace', 'add', 'subtract', 'intersect'
        """
        old_mask = self.selection_mask.copy()
        new_selection = self.selection_mask.copy()
        
        painter = QPainter(new_selection)
        
        if operation == "replace":
            new_selection.fill(0)
            painter.drawImage(0, 0, new_mask)
            
        elif operation == "add":
            # Add (Union)
            # SourceOver works if we paint opaque white (255) where selected.
            # Assuming new_mask is Alpha8 with 0 or 255.
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
            painter.drawImage(0, 0, new_mask)
            
        elif operation == "subtract":
            # Subtract
            # DestOut: Result = Dest * (1 - SourceAlpha)
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_DestinationOut)
            painter.drawImage(0, 0, new_mask)
            
        elif operation == "intersect":
            # Intersect
            # DestIn: Result = Dest * SourceAlpha
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_DestinationIn)
            painter.drawImage(0, 0, new_mask)
            
        painter.end()
        
        command = SelectionCommand(self, old_mask, new_selection)
        self.history.push(command)
        command.execute()

    def set_selection(self, rect: QRect, operation: str = "replace"):
        """
        Set selection using a rectangle (wrapper for combine_selection).
        """
        temp_mask = QImage(self.size, QImage.Format.Format_Alpha8)
        temp_mask.fill(0)
        painter = QPainter(temp_mask)
        painter.fillRect(rect, Qt.GlobalColor.white)
        painter.end()
        
        self.combine_selection(temp_mask, operation)

    def _update_selection_region(self):
        # Update has_selection flag
        # MaskInColor: Matching (0) -> 1, Others (255) -> 0.
        # If QRegion includes 0, this works.
        # Actually let's try MaskInColor if MaskOutColor failed.
        bitmap = QBitmap.fromImage(self.selection_mask.createMaskFromColor(0, Qt.MaskMode.MaskInColor))
        self.selection_region = QRegion(bitmap)
        
        # Update has_selection flag
        self.has_selection = not self.selection_region.isEmpty()

    def get_selection_region(self) -> QRegion:
        return self.selection_region

    def clear_selection(self):
        # Deselect
        if not self.has_selection:
            return
        # Set selection to empty rect with replace
        self.set_selection(QRect(0,0,0,0), "replace")
        
    def select_all(self):
        # Full white mask
        new_mask = QImage(self.size, QImage.Format.Format_Alpha8)
        new_mask.fill(255) # 255 = Selected
        
        self.combine_selection(new_mask, "replace")
        
    def invert_selection(self):
        # Invert the current mask
        old_mask = self.selection_mask.copy()
        new_mask = self.selection_mask.copy()
        new_mask.invertPixels()
        
        # NOTE: Ensure Alpha8
        # invertPixels on Alpha8 works (0->255, 255->0)
        
        command = SelectionCommand(self, old_mask, new_mask)
        self.history.push(command)
        command.execute()

    def feather_selection(self, radius: int):
        """Apply a feather (blur) to the selection edges using NumPy."""
        if not self.has_selection or radius <= 0:
            return
        
        old_mask = self.selection_mask.copy()
        
        # Convert to numpy, blur, convert back
        mask_arr = qimage_alpha8_to_numpy(self.selection_mask)
        sigma = radius / 3.0
        blurred = gaussian_blur_np(mask_arr, sigma)
        new_mask = numpy_to_qimage_alpha8(blurred)
        
        command = SelectionCommand(self, old_mask, new_mask)
        self.history.push(command)
        command.execute()

    def expand_selection(self, amount: int):
        """Expand the selection by given pixel amount using morphological dilation."""
        if not self.has_selection or amount <= 0:
            return
        
        old_mask = self.selection_mask.copy()
        
        # Convert to numpy, dilate, convert back
        mask_arr = qimage_alpha8_to_numpy(self.selection_mask)
        dilated = morphological_dilate(mask_arr, amount)
        new_mask = numpy_to_qimage_alpha8(dilated)
        
        command = SelectionCommand(self, old_mask, new_mask)
        self.history.push(command)
        command.execute()

    def contract_selection(self, amount: int):
        """Contract the selection by given pixel amount using morphological erosion."""
        if not self.has_selection or amount <= 0:
            return
        
        old_mask = self.selection_mask.copy()
        
        # Convert to numpy, erode, convert back
        mask_arr = qimage_alpha8_to_numpy(self.selection_mask)
        eroded = morphological_erode(mask_arr, amount)
        new_mask = numpy_to_qimage_alpha8(eroded)
        
        command = SelectionCommand(self, old_mask, new_mask)
        self.history.push(command)
        command.execute()

    def add_layer(self, name: str = "New Layer") -> Layer:
        layer = Layer(self.size.width(), self.size.height(), name)
        command = LayerStructureCommand(self, "add", layer=layer, index=len(self.layers))
        self.history.push(command)
        command.execute()
        return layer

    def delete_layer(self, index: int):
        if 0 <= index < len(self.layers) and len(self.layers) > 1:
            layer = self.layers[index]
            command = LayerStructureCommand(self, "remove", layer=layer, index=index)
            self.history.push(command)
            command.execute()

    def get_active_layer(self) -> Layer | None:
        if 0 <= self._active_layer_index < len(self.layers):
            return self.layers[self._active_layer_index]
        return None

    def set_active_layer(self, index: int):
        if 0 <= index < len(self.layers):
            self._active_layer_index = index
            self.active_layer_changed.emit(self.layers[index])

    def move_layer_up(self):
        idx = self._active_layer_index
        if idx < len(self.layers) - 1:
            self.move_layer(idx, idx + 1)
            
    def move_layer_down(self):
        idx = self._active_layer_index
        if idx > 0:
            self.move_layer(idx, idx - 1)

    def duplicate_layer(self, index: int):
        if index < 0 or index >= len(self.layers): return
        
        orig = self.layers[index]
        new_layer = Layer(orig.image.width(), orig.image.height(), f"{orig.name} Copy")
        new_layer.image = orig.image.copy()
        new_layer.opacity = orig.opacity
        new_layer.visible = orig.visible
        new_layer.blend_mode = orig.blend_mode
        
        cmd = LayerStructureCommand(self, "add", layer=new_layer, index=index + 1)
        self.history.push(cmd)
        cmd.execute()

    def move_layer(self, from_index: int, to_index: int):
        if from_index == to_index: 
            return
        if not (0 <= from_index < len(self.layers) and 0 <= to_index < len(self.layers)):
            return
            
        command = LayerStructureCommand(self, "move", index=to_index, previous_index=from_index)
        self.history.push(command)
        command.execute()
