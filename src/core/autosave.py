import os
import time
from PySide6.QtCore import QTimer, QObject
from .io import ProjectIO

class AutosaveManager(QObject):
    def __init__(self, main_window, interval_minutes=5):
        super().__init__()
        self.main_window = main_window
        self.interval_ms = interval_minutes * 60 * 1000
        
        self.autosave_dir = os.path.expanduser("~/.aphelion/autosave")
        if not os.path.exists(self.autosave_dir):
            os.makedirs(self.autosave_dir, exist_ok=True)
            
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.save_all)
        self.timer.start(self.interval_ms)
        
    def save_all(self):
        print("Autosaving...")
        count = self.main_window.tab_widget.count()
        for i in range(count):
            widget = self.main_window.tab_widget.widget(i)
            if hasattr(widget, 'canvas') and widget.canvas.document:
                doc = widget.canvas.document
                # Sanitize name
                name = self.main_window.tab_widget.tabText(i).replace("*", "").strip()
                if not name: name = "Untitled"
                
                filename = f"autosave_{name}_{int(time.time())}.aphelion"
                path = os.path.join(self.autosave_dir, filename)
                
                try:
                    ProjectIO.save_project(doc, path)
                    # Clean up old autosaves? (Future)
                except Exception as e:
                    print(f"Autosave failed for {name}: {e}")
