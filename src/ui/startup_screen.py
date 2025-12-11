from PySide6.QtWidgets import (QDialog, QVBoxLayout, QPushButton, QLabel, 
                               QListWidget, QHBoxLayout, QFrame, QWidget)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from ..core.settings import SettingsManager
import os

class StartupScreen(QDialog):
    open_file = Signal(str)
    new_file = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Welcome to Aphelion")
        self.resize(600, 400)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        
        layout = QHBoxLayout()
        
        # Left Panel (Actions)
        left_panel = QFrame()
        left_panel.setStyleSheet("background-color: #333333; color: white;")
        left_layout = QVBoxLayout(left_panel)
        
        lbl_title = QLabel("Aphelion")
        lbl_title.setStyleSheet("font-size: 24px; font-weight: bold; margin-bottom: 20px;")
        left_layout.addWidget(lbl_title)
        
        btn_new = QPushButton("New Image...")
        btn_new.setMinimumHeight(40)
        btn_new.clicked.connect(self.on_new)
        left_layout.addWidget(btn_new)
        
        btn_open = QPushButton("Open Image...")
        btn_open.setMinimumHeight(40)
        btn_open.clicked.connect(self.on_open)
        left_layout.addWidget(btn_open)
        
        left_layout.addStretch()
        
        # Version
        left_layout.addWidget(QLabel("Version 0.5 Beta"))
        
        layout.addWidget(left_panel, 1)
        
        # Right Panel (Recents)
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.addWidget(QLabel("Recent Files"))
        
        self.list_recents = QListWidget()
        self.list_recents.itemDoubleClicked.connect(self.on_recent_clicked)
        right_layout.addWidget(self.list_recents)
        
        layout.addWidget(right_panel, 2)
        
        self.setLayout(layout)
        
        self.load_recents()
        
    def load_recents(self):
        settings = SettingsManager()
        recents = settings.get_recent_files()
        for path in recents:
            if os.path.exists(path):
                self.list_recents.addItem(path)
                
    def on_new(self):
        self.new_file.emit()
        self.accept()
        
    def on_open(self):
        # We can't easily show file dialog here and return path?
        # Or we rely on MainWindow to show it.
        # Let's emit a signal with empty string to trigger Open Dialog in MainWindow?
        # Or we return a code?
        # Actually easier: Self-contained? No, MainWindow handles the actual opening.
        # We'll set a result code?
        # Let's use custom property or signals connected by MainWindow before show.
        self.open_file.emit("") # Empty means "Ask user"
        self.accept()
        
    def on_recent_clicked(self, item):
        path = item.text()
        self.open_file.emit(path)
        self.accept()
