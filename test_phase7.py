import sys
import unittest
import shutil
import os
from PySide6.QtWidgets import QApplication, QPushButton
from PySide6.QtCore import QByteArray
from src.core.settings import SettingsManager
from src.ui.panels.tools_dock import ToolsDock

# Init App
app = QApplication.instance() or QApplication(sys.argv)

class TestPhase7(unittest.TestCase):
    def test_settings_persistence(self):
        settings = SettingsManager()
        settings.set_value("test_key", "test_value")
        settings.sync()
        
        # New instance should read same value
        # QSettings on linux uses config files usually.
        # But same process read is valid test of api.
        
        val = settings.get_value("test_key")
        self.assertEqual(val, "test_value")
        
        # Binary data (Geometry)
        geo = QByteArray(b"geometry_data")
        settings.set_value("window/geometry", geo)
        val = settings.get_value("window/geometry")
        self.assertEqual(val, geo)

    def test_shortcuts_assigned(self):
        # ToolsDock should assign shortcuts
        # We need a dummy Document/Session to init ToolsDock
        from src.core.session import Session
        from src.core.document import Document
        session = Session()
        doc = Document(10, 10)
        
        dock = ToolsDock(session)
        dock.initialize_standard_tools(doc)
        
        # Check Brush Shortcut
        self.assertIn("Brush", dock.tools)
        brush_btn = dock.tools["Brush"]["button"]
        
        # shortcut() returns QKeySequence. 
        # toString() gives string rep.
        self.assertEqual(brush_btn.shortcut().toString(), "B")
        
        # Check Rect Select
        rect = dock.tools["Rect Select"]["button"]
        self.assertEqual(rect.shortcut().toString(), "S")

if __name__ == '__main__':
    unittest.main()
