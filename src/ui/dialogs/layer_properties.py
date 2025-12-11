from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QDialogButtonBox, QSlider, QComboBox
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter

class LayerPropertiesDialog(QDialog):
    def __init__(self, parent, layer):
        super().__init__(parent)
        self.setWindowTitle("Layer Properties")
        self.layer = layer
        
        layout = QVBoxLayout()
        
        # Name
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Name:"))
        self.edit_name = QLineEdit(layer.name)
        name_layout.addWidget(self.edit_name)
        layout.addLayout(name_layout)
        
        # Opacity
        opaque_layout = QHBoxLayout()
        opaque_layout.addWidget(QLabel("Opacity:"))
        self.slider_opacity = QSlider(Qt.Horizontal)
        self.slider_opacity.setRange(0, 255)
        # Assuming layer.opacity is 0-1.0 float or 0-255 int?
        # Check Layer class. Assuming 0.0-1.0 based on painter.setOpacity call in doc.
        # But let's check. If doc calls painter.setOpacity(layer.opacity) and it's 0-1 float.
        # Let's assume float 0-1.
        val = int(layer.opacity * 255)
        self.slider_opacity.setValue(val)
        opaque_layout.addWidget(self.slider_opacity)
        
        self.lbl_opacity = QLabel(f"{val}")
        opaque_layout.addWidget(self.lbl_opacity)
        
        self.slider_opacity.valueChanged.connect(lambda v: self.lbl_opacity.setText(str(v)))
        layout.addLayout(opaque_layout)
        
        # Blend Mode
        blend_layout = QHBoxLayout()
        blend_layout.addWidget(QLabel("Blend Mode:"))
        self.combo_blend = QComboBox()
        # Populate with standard Qt Blend Modes
        # We need a mapping from str to Qt.BlendMode or just use names?
        # Layer.blend_mode is proper enum.
        # For now, let's just support Normal / Multiply / Add / Screen / Overlay as MVP
        self.modes = [
            ("Normal", QPainter.CompositionMode.CompositionMode_SourceOver),
            ("Multiply", QPainter.CompositionMode.CompositionMode_Multiply),
            ("Screen", QPainter.CompositionMode.CompositionMode_Screen),
            ("Overlay", QPainter.CompositionMode.CompositionMode_Overlay),
            ("Darken", QPainter.CompositionMode.CompositionMode_Darken),
            ("Lighten", QPainter.CompositionMode.CompositionMode_Lighten),
            ("Color Dodge", QPainter.CompositionMode.CompositionMode_ColorDodge),
            ("Color Burn", QPainter.CompositionMode.CompositionMode_ColorBurn),
            ("Hard Light", QPainter.CompositionMode.CompositionMode_HardLight),
            ("Soft Light", QPainter.CompositionMode.CompositionMode_SoftLight),
            ("Difference", QPainter.CompositionMode.CompositionMode_Difference),
            ("Exclusion", QPainter.CompositionMode.CompositionMode_Exclusion)
        ]
        
        
        
        current_idx = 0
        for i, (name, mode) in enumerate(self.modes):
            self.combo_blend.addItem(name, mode)
            if layer.blend_mode == mode:
                current_idx = i
                
        self.combo_blend.setCurrentIndex(current_idx)
        blend_layout.addWidget(self.combo_blend)
        layout.addLayout(blend_layout)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
        
    def get_values(self):
        name = self.edit_name.text()
        opacity = self.slider_opacity.value() / 255.0
        blend_mode = self.combo_blend.currentData()
        return name, opacity, blend_mode
