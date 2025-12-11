from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QSlider, QComboBox, QToolBar, QSpinBox, QCheckBox, QButtonGroup, QRadioButton
from PySide6.QtCore import Qt, QSize
from ..core.session import Session

class ToolOptionsBar(QToolBar):
    def __init__(self, session: Session):
        super().__init__("Tool Options")
        self.session = session
        self.setMovable(False)
        self.setFloatable(False)
        self.setStyleSheet("QToolBar { spacing: 10px; padding: 5px; }")
        
        # We will clear and rebuild this toolbar based on the active tool
        # Or keep a stack of widgets? 
        # Rebuilding is simpler for now.
        
        self.session.active_tool_changed.connect(self.on_tool_changed)
        
        # Initial Build
        self.on_tool_changed(self.session.active_tool)

    def on_tool_changed(self, tool):
        self.clear()
        
        if not tool:
            return
            
        # Common Label?
        # self.addWidget(QLabel(f"<b>{tool.name}</b>"))
        # self.addSeparator()
        
        # Brush Size (Brush, Eraser, Clone, etc.)
        if hasattr(tool, 'name') and tool.name in ["Brush", "Eraser", "Line", "Star Stamp"]:
            self._add_brush_size()
            
        # Tolerance (Bucket, Magic Wand)
        if tool.name in ["Bucket", "Magic Wand"]:
            self._add_tolerance()
            
        # Selection Mode (Rect, Ellipse, Lasso, Magic Wand)
        if "Select" in tool.name or tool.name == "Magic Wand":
            self._add_selection_mode()
            
        # Text Options (Text Tool) - if we had them
        if tool.name == "Text":
            self.addWidget(QLabel("Font size:"))
            # Text tool options would go here
            self._add_brush_size() # Reuse for font size for now?
            
        self.addSeparator()

    def _add_brush_size(self):
        lbl = QLabel("Size:")
        self.addWidget(lbl)
        
        slider = QSlider(Qt.Horizontal)
        slider.setRange(1, 100)
        slider.setFixedWidth(150)
        slider.setValue(self.session.brush_size)
        
        # Spinbox for precise control
        spin = QSpinBox()
        spin.setRange(1, 100)
        spin.setValue(self.session.brush_size)
        
        def update_size(val):
            self.session.brush_size = val
            if slider.value() != val: slider.blockSignals(True); slider.setValue(val); slider.blockSignals(False)
            if spin.value() != val: spin.blockSignals(True); spin.setValue(val); spin.blockSignals(False)

        slider.valueChanged.connect(update_size)
        spin.valueChanged.connect(update_size)
        
        self.session.brush_size_changed.connect(lambda v: (
            slider.blockSignals(True), slider.setValue(v), slider.blockSignals(False),
            spin.blockSignals(True), spin.setValue(v), spin.blockSignals(False)
        ))
        
        self.addWidget(slider)
        self.addWidget(spin)

    def _add_tolerance(self):
        # We don't have tolerance in Session yet? 
        # PaintBucketTool in `src/tools/fill.py` uses `tolerance` param but defaults to 32?
        # Check src/tools/fill.py lines 1-120 (viewed earlier). 
        # It takes `tolerance` in constructor or fill method?
        # Actually `fill` method takes `tolerance=32`.
        # We need to store tolerance in Session or Tool instance.
        # Let's add `tolerance` to Session for shared persistence.
        
        if not hasattr(self.session, 'tolerance'):
            self.session.tolerance = 32 # Default
            
        lbl = QLabel("Tolerance:")
        self.addWidget(lbl)
        
        slider = QSlider(Qt.Horizontal)
        slider.setRange(0, 100) # Percent or byte? usually 0-100%
        slider.setFixedWidth(150)
        slider.setValue(self.session.tolerance) # Assume session has it (we'll add it)
        
        slider.valueChanged.connect(lambda v: setattr(self.session, 'tolerance', v))
        
        self.addWidget(slider)
        
        
    def _add_selection_mode(self):
        lbl = QLabel("Mode:")
        self.addWidget(lbl)
        
        # Radio buttons in a widget
        container = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(0,0,0,0)
        
        bg = QButtonGroup(container)
        modes = [("Replace", "replace"), ("Add", "add"), ("Subtract", "subtract"), ("Intersect", "intersect")]
        
        current = self.session.selection_mode
        
        for text, mode_id in modes:
            btn = QRadioButton(text)
            if current == mode_id:
                btn.setChecked(True)
            bg.addButton(btn)
            layout.addWidget(btn)
            
            # Use closure to capture mode_id
            def make_callback(m):
                return lambda: setattr(self.session, 'selection_mode', m)
            
            btn.clicked.connect(make_callback(mode_id))
            
        container.setLayout(layout)
        self.addWidget(container)
