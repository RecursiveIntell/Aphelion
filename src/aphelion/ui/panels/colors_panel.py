from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QColorDialog
from PySide6.QtGui import QColor, QPixmap, QPainter, QBrush
from PySide6.QtCore import Qt, Signal
from ...core.session import Session

class ColorSwatch(QPushButton):
    color_changed = Signal(QColor)
    
    def __init__(self, color: QColor, parent=None):
        super().__init__(parent)
        self.start_color = color
        self.setFixedSize(40, 40)
        self.update_color(color)
        self.clicked.connect(self.choose_color)
        
    def update_color(self, color: QColor):
        self.current_color = color
        # Set background style or icon
        # StyleSheet is easiest for solid color
        self.setStyleSheet(f"background-color: {color.name()}; border: 1px solid #888;")
        
    def choose_color(self):
        c = QColorDialog.getColor(self.current_color, self, "Select Color", QColorDialog.ColorDialogOption.ShowAlphaChannel)
        if c.isValid():
            self.update_color(c)
            self.color_changed.emit(c)

class ColorsPanel(QWidget):
    def __init__(self, session: Session):
        super().__init__()
        self.session = session
        
        self.layout = QVBoxLayout()
        
        # Primary / Secondary
        self.swatch_layout = QHBoxLayout()
        
        self.primary_swatch = ColorSwatch(self.session.primary_color)
        self.primary_swatch.color_changed.connect(lambda c: setattr(self.session, 'primary_color', c))
        
        self.secondary_swatch = ColorSwatch(self.session.secondary_color)
        self.secondary_swatch.color_changed.connect(lambda c: setattr(self.session, 'secondary_color', c))
        
        self.btn_swap = QPushButton("<->")
        self.btn_swap.setFixedSize(30, 30)
        self.btn_swap.clicked.connect(self.session.swap_colors)
        
        self.swatch_layout.addWidget(self.primary_swatch)
        self.swatch_layout.addWidget(self.btn_swap)
        self.swatch_layout.addWidget(self.secondary_swatch)
        
        self.layout.addLayout(self.swatch_layout)
        
        # Labels
        self.lbl_info = QLabel("Primary / Secondary")
        self.lbl_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.lbl_info)
        
        self.layout.addStretch()
        self.setLayout(self.layout)
        
        # Listen to session changes
        self.session.primary_color_changed.connect(self.primary_swatch.update_color)
        self.session.secondary_color_changed.connect(self.secondary_swatch.update_color)
