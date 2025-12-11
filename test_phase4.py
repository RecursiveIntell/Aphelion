import sys
import unittest
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QColor, QImage
from PySide6.QtCore import QSize, Qt
from src.core.document import Document
from src.core.layer import Layer

# Init App
app = QApplication.instance() or QApplication(sys.argv)

class TestPhase4(unittest.TestCase):
    def setUp(self):
        self.doc = Document(100, 100)
        self.layer1 = self.doc.add_layer("Layer 1")
        self.layer1.image.fill(QColor(255, 0, 0)) # Red
        
        self.layer2 = self.doc.add_layer("Layer 2")
        self.layer2.image.fill(QColor(0, 0, 255)) # Blue
        
    def test_resize_image(self):
        # Resize Down
        self.doc.resize_image(50, 50)
        self.assertEqual(self.doc.size, QSize(50, 50))
        self.assertEqual(self.layer1.image.size(), QSize(50, 50))
        
        # Undo
        self.doc.history.undo()
        self.assertEqual(self.doc.size, QSize(100, 100))
        self.assertEqual(self.layer1.image.size(), QSize(100, 100))
        # Check simple pixel sampling (center)
        # 50,50 red?
        self.assertEqual(self.layer1.image.pixelColor(50, 50), QColor(255, 0, 0))

    def test_resize_canvas(self):
        # Resize Up
        self.doc.resize_canvas(200, 200, Qt.AlignCenter)
        self.assertEqual(self.doc.size, QSize(200, 200))
        self.assertEqual(self.layer1.image.size(), QSize(200, 200))
        # Center should be red (original), borders transparent?
        # Offset: (200-100)/2 = 50.
        # At 0,0 should be transparent
        self.assertEqual(self.layer1.image.pixelColor(0, 0).alpha(), 0)
        # At 60,60 (inside 50,50 offset rect) should be red
        self.assertEqual(self.layer1.image.pixelColor(60, 60), QColor(255, 0, 0))
        
        # Undo
        self.doc.history.undo()
        self.assertEqual(self.doc.size, QSize(100, 100))
        self.assertEqual(self.layer1.image.size(), QSize(100, 100))
        self.assertEqual(self.layer1.image.pixelColor(0, 0), QColor(255, 0, 0))

    def test_flip_image(self):
        # Paint left half white
        import PySide6.QtGui as QtGui
        painter = QtGui.QPainter(self.layer1.image)
        painter.fillRect(0, 0, 50, 100, Qt.white)
        painter.end()
        
        # Flip Horizontal
        self.doc.flip_image(True, False)
        # Now left should be Red (original right), Right should be White
        self.assertEqual(self.layer1.image.pixelColor(0, 0), QColor(255, 0, 0))
        self.assertEqual(self.layer1.image.pixelColor(60, 0), QColor(255, 255, 255))
        
        # Undo
        self.doc.history.undo()
        self.assertEqual(self.layer1.image.pixelColor(0, 0), QColor(255, 255, 255))

    def test_duplicate_layer(self):
        count = len(self.doc.layers)
        self.doc.duplicate_layer(1) # Layer 2
        self.assertEqual(len(self.doc.layers), count + 1)
        self.assertEqual(self.doc.layers[2].name, "Layer 2 Copy")
        
        # Undo
        self.doc.history.undo()
        self.assertEqual(len(self.doc.layers), count)

    def test_flatten(self):
        self.doc.flatten_image()
        self.assertEqual(len(self.doc.layers), 1)
        self.assertEqual(self.doc.layers[0].name, "Background")
        
        # Undo
        self.doc.history.undo()
        self.assertGreater(len(self.doc.layers), 1)

if __name__ == '__main__':
    unittest.main()
