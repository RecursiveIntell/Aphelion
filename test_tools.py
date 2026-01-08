import sys
import unittest
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QColor, QImage
from PySide6.QtCore import QPoint, QRect
from aphelion.core.document import Document
from aphelion.core.session import Session
from aphelion.tools.brush import BrushTool
from aphelion.tools.eraser import EraserTool
from aphelion.tools.rectangle_select import RectangleSelectTool
from aphelion.tools.selection import EllipseSelectTool, LassoSelectTool, MagicWandTool
from aphelion.tools.fill import PaintBucketTool

# Init App
app = QApplication.instance() or QApplication(sys.argv)

from PySide6.QtCore import Qt

class TestTools(unittest.TestCase):
    def setUp(self):
        self.doc = Document(100, 100)
        self.layer = self.doc.add_layer("Background")
        self.layer.image.fill(Qt.white)
        self.session = Session()
        self.session.active_color = QColor(0, 0, 0) # Black
        
    def test_brush_tool(self):
        tool = BrushTool(self.doc, self.session)
        tool.size = 10
        
        # Simulate stroke
        # Note: Tool interface takes just (pos). Qt.LeftButton is usually assumed or passed via event.
        # But base Tool.mouse_press(self, pos: QPoint)
        tool.mouse_press(QPoint(50, 50))
        tool.mouse_move(QPoint(60, 60))
        tool.mouse_release(QPoint(60, 60))
        
        # Check if painted
        # 55, 55 should be black
        c = self.layer.image.pixelColor(55, 55)
        self.assertEqual(c.red(), 0)
        self.assertEqual(c.green(), 0)
        self.assertEqual(c.blue(), 0)
        
    def test_eraser_tool(self):
        # Fill with black
        self.layer.image.fill(QColor(0, 0, 0))
        
        tool = EraserTool(self.doc, self.session)
        tool.size = 10
        
        tool.mouse_press(QPoint(50, 50))
        tool.mouse_release(QPoint(50, 50))
        
        # Should be transparent (0, 0, 0, 0)
        c = self.layer.image.pixelColor(50, 50)
        self.assertEqual(c.alpha(), 0)
        
    def test_rect_select_tool(self):
        tool = RectangleSelectTool(self.doc, self.session)
        
        tool.mouse_press(QPoint(10, 10))
        tool.mouse_move(QPoint(50, 50))
        tool.mouse_release(QPoint(50, 50))
        
        self.assertTrue(self.doc.has_selection)
        self.assertTrue(self.doc.get_selection_region().contains(QPoint(30, 30)))
        
    def test_bucket_fill(self):
        # Draw a black square in center
        import PySide6.QtGui as QtGui
        painter = QtGui.QPainter(self.layer.image)
        painter.fillRect(40, 40, 20, 20, Qt.black)
        painter.end()
        
        tool = PaintBucketTool(self.doc, self.session)
        self.session.active_color = QColor(255, 0, 0) # Red
        
        # Fill the white area (outside square)
        tool.mouse_press(QPoint(10, 10))
        tool.mouse_release(QPoint(10, 10))
        
        # 10,10 should be Red
        self.assertEqual(self.layer.image.pixelColor(10, 10), QColor(255, 0, 0))
        # 50,50 (inside square) should still be Black
        self.assertEqual(self.layer.image.pixelColor(50, 50), QColor(0, 0, 0))

if __name__ == '__main__':
    from PySide6.QtCore import Qt
    unittest.main()
