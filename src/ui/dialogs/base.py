from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox, QPushButton, QComboBox, QDialogButtonBox, QGroupBox, QGridLayout, QButtonGroup
from PySide6.QtCore import Qt

class ResizeDialog(QDialog):
    def __init__(self, parent, width, height, title="Resize"):
        super().__init__(parent)
        self.setWindowTitle(title)
        
        self.width_val = width
        self.height_val = height
        
        layout = QVBoxLayout()
        
        # Width
        w_layout = QHBoxLayout()
        w_layout.addWidget(QLabel("Width:"))
        self.spin_width = QSpinBox()
        self.spin_width.setRange(1, 100000)
        self.spin_width.setValue(width)
        w_layout.addWidget(self.spin_width)
        w_layout.addWidget(QLabel("px"))
        layout.addLayout(w_layout)
        
        # Height
        h_layout = QHBoxLayout()
        h_layout.addWidget(QLabel("Height:"))
        self.spin_height = QSpinBox()
        self.spin_height.setRange(1, 100000)
        self.spin_height.setValue(height)
        h_layout.addWidget(self.spin_height)
        h_layout.addWidget(QLabel("px"))
        layout.addLayout(h_layout)
        
        # Aspect Ratio
        # TODO: Add specific aspect ratio lock UI
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
        
    def get_values(self):
        return self.spin_width.value(), self.spin_height.value()

class CanvasResizeDialog(ResizeDialog):
    def __init__(self, parent, width, height):
        super().__init__(parent, width, height, "Canvas Size")
        
        # Anchor UI
        top_layout = self.layout()
        # insert before buttons (last item)
        
        self.grp_anchor = QGroupBox("Anchor")
        anchor_layout = QGridLayout()
        self.bg_anchor = QButtonGroup(self)
        
        anchors = [
            (Qt.AlignTop | Qt.AlignLeft, 0, 0),
            (Qt.AlignTop | Qt.AlignHCenter, 0, 1),
            (Qt.AlignTop | Qt.AlignRight, 0, 2),
            (Qt.AlignVCenter | Qt.AlignLeft, 1, 0),
            (Qt.AlignCenter, 1, 1),
            (Qt.AlignVCenter | Qt.AlignRight, 1, 2),
            (Qt.AlignBottom | Qt.AlignLeft, 2, 0),
            (Qt.AlignBottom | Qt.AlignHCenter, 2, 1),
            (Qt.AlignBottom | Qt.AlignRight, 2, 2)
        ]
        
        for align, r, c in anchors:
            btn = QPushButton()
            btn.setCheckable(True)
            btn.setFixedSize(30, 30)
            btn.setProperty("align", align)
            self.bg_anchor.addButton(btn)
            anchor_layout.addWidget(btn, r, c)
            
            if align == Qt.AlignCenter:
                btn.setChecked(True)
                
        self.grp_anchor.setLayout(anchor_layout)
        
        # Insert before button box
        top_layout.insertWidget(top_layout.count() - 1, self.grp_anchor)
        
    def get_anchor(self):
        btn = self.bg_anchor.checkedButton()
        if btn:
            return btn.property("align")
        return Qt.AlignCenter
