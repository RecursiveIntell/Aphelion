from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QColor
from .document import Document

class Session(QObject):
    """
    Manages global application state:
    - Active Tool
    - Primary / Secondary Colors
    - Clipboard? (Maybe later)
    """
    active_tool_changed = Signal(object) # Tool instance
    primary_color_changed = Signal(QColor)
    secondary_color_changed = Signal(QColor)
    
    def __init__(self):
        super().__init__()
        self._active_tool = None
        self._primary_color = QColor(0, 0, 0) # Black
        self._secondary_color = QColor(255, 255, 255) # White
        
    @property
    def active_tool(self):
        return self._active_tool
        
    @active_tool.setter
    def active_tool(self, tool):
        if self._active_tool != tool:
            if self._active_tool:
                self._active_tool.deactivate()
            self._active_tool = tool
            if self._active_tool:
                self._active_tool.activate()
            self.active_tool_changed.emit(tool)

    @property
    def primary_color(self):
        return self._primary_color
        
    @primary_color.setter
    def primary_color(self, color: QColor):
        if self._primary_color != color:
            self._primary_color = color
            self.primary_color_changed.emit(color)

    @property
    def secondary_color(self):
        return self._secondary_color
        
    @secondary_color.setter
    def secondary_color(self, color: QColor):
        if self._secondary_color != color:
            self._secondary_color = color
            self.secondary_color_changed.emit(color)
            
    def swap_colors(self):
        p = self._primary_color
        self.primary_color = self._secondary_color
        self.secondary_color = p
        
    # Actions triggered by tools
    zoom_action_triggered = Signal(float) # Factor (e.g. 1.2 or 0.8)

    # Shared Tool Options
    brush_size_changed = Signal(int)
    selection_mode_changed = Signal(str)
    
    @property
    def brush_size(self):
        return getattr(self, "_brush_size", 5)
        
    @brush_size.setter
    def brush_size(self, size: int):
        if self.brush_size != size:
            self._brush_size = size
            self.brush_size_changed.emit(size)

    @property
    def selection_mode(self):
        return getattr(self, "_selection_mode", "replace")

    @selection_mode.setter
    def selection_mode(self, mode: str):
            self._selection_mode = mode
            self.selection_mode_changed.emit(mode)
            
    # Edit Target: "image" or "mask"
    edit_target_changed = Signal(str)
    
    @property
    def edit_target(self):
        return getattr(self, "_edit_target", "image")
        
    @edit_target.setter
    def edit_target(self, target: str):
        if self.edit_target != target:
            self._edit_target = target
            self.edit_target_changed.emit(target)
