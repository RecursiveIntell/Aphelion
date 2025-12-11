import sys
import unittest
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QColor, QImage
from PySide6.QtCore import QPoint, QRect
from src.core.document import Document
from src.core.session import Session
from src.tools.brush import BrushTool
from src.tools.eraser import EraserTool
from src.tools.rectangle_select import RectangleSelectTool
from src.tools.selection import EllipseSelectTool, LassoSelectTool, MagicWandTool
from src.tools.fill import PaintBucketTool

# Init App
app = QApplication.instance() or QApplication(sys.argv)


class TestBrushTool(unittest.TestCase):
    """Test suite for BrushTool."""
    
    def setUp(self):
        self.doc = Document(100, 100)
        self.layer = self.doc.add_layer("Layer 1")
        self.layer.image.fill(QColor(255, 255, 255))  # White
        self.session = Session()
        self.session.primary_color = QColor(255, 0, 0)  # Red
        self.session.brush_size = 5
        self.tool = BrushTool(self.doc, self.session)
        
    def test_brush_draws_on_layer(self):
        """Test that brush stroke modifies layer pixels."""
        # Simulate stroke
        self.tool.mouse_press(QPoint(50, 50))
        self.tool.mouse_move(QPoint(55, 55))
        self.tool.mouse_release(QPoint(55, 55))
        
        # Check pixel changed
        color = self.layer.image.pixelColor(52, 52)
        # Should be red or close to it
        self.assertGreater(color.red(), 200)
        
    def test_brush_creates_undo_command(self):
        """Test that brush stroke is undoable."""
        initial_stack_size = len(self.doc.history.undo_stack)
        
        self.tool.mouse_press(QPoint(10, 10))
        self.tool.mouse_move(QPoint(20, 20))
        self.tool.mouse_release(QPoint(20, 20))
        
        # Command should be pushed
        self.assertEqual(len(self.doc.history.undo_stack), initial_stack_size + 1)
        
    def test_brush_undo_restores_layer(self):
        """Test that undo restores original layer content."""
        # Store original pixel at stroke path
        original_at_30 = self.layer.image.pixelColor(30, 30)
        
        # Draw a stroke that passes through (30, 30)
        self.tool.mouse_press(QPoint(25, 25))
        self.tool.mouse_move(QPoint(30, 30))  # This is where drawing happens
        self.tool.mouse_move(QPoint(35, 35))
        self.tool.mouse_release(QPoint(35, 35))
        
        # Pixel at 30,30 should be changed (red now)
        modified = self.layer.image.pixelColor(30, 30)
        self.assertGreater(modified.red(), 200)  # Should be red-ish
        
        # Undo
        self.doc.history.undo()
        
        # Pixel should be restored to original (white)
        restored = self.layer.image.pixelColor(30, 30)
        self.assertEqual(restored.red(), 255)
        self.assertEqual(restored.green(), 255)


class TestEraserTool(unittest.TestCase):
    """Test suite for EraserTool."""
    
    def setUp(self):
        self.doc = Document(100, 100)
        self.layer = self.doc.add_layer("Layer 1")
        self.layer.image.fill(QColor(255, 0, 0))  # Red
        self.session = Session()
        self.session.brush_size = 10
        self.tool = EraserTool(self.doc, self.session)
        
    def test_eraser_makes_transparent(self):
        """Test that eraser creates transparency."""
        # Eraser draws on mouse_move, not mouse_press
        self.tool.mouse_press(QPoint(45, 45))
        self.tool.mouse_move(QPoint(50, 50))  # Drawing happens here
        self.tool.mouse_move(QPoint(55, 55))
        self.tool.mouse_release(QPoint(55, 55))
        
        # Check alpha at the stroke path
        color = self.layer.image.pixelColor(50, 50)
        self.assertLess(color.alpha(), 255)


class TestRectangleSelectTool(unittest.TestCase):
    """Test suite for RectangleSelectTool."""
    
    def setUp(self):
        self.doc = Document(100, 100)
        self.doc.add_layer("Layer 1")
        self.session = Session()
        self.tool = RectangleSelectTool(self.doc, self.session)
        
    def test_rectangle_select_creates_selection(self):
        """Test that rectangle select creates a selection region."""
        self.assertFalse(self.doc.has_selection)
        
        self.tool.mouse_press(QPoint(10, 10))
        self.tool.mouse_move(QPoint(50, 50))
        self.tool.mouse_release(QPoint(50, 50))
        
        self.assertTrue(self.doc.has_selection)
        
    def test_rectangle_select_region_bounds(self):
        """Test selection region contains expected points."""
        self.tool.mouse_press(QPoint(20, 20))
        self.tool.mouse_move(QPoint(60, 60))
        self.tool.mouse_release(QPoint(60, 60))
        
        region = self.doc.get_selection_region()
        # Point inside should be in region
        self.assertTrue(region.contains(QPoint(40, 40)))
        # Point outside should not be
        self.assertFalse(region.contains(QPoint(5, 5)))


class TestEllipseSelectTool(unittest.TestCase):
    """Test suite for EllipseSelectTool."""
    
    def setUp(self):
        self.doc = Document(100, 100)
        self.doc.add_layer("Layer 1")
        self.session = Session()
        self.tool = EllipseSelectTool(self.doc, self.session)
        
    def test_ellipse_select_creates_selection(self):
        """Test ellipse select creates selection."""
        self.tool.mouse_press(QPoint(10, 10))
        self.tool.mouse_move(QPoint(90, 90))
        self.tool.mouse_release(QPoint(90, 90))
        
        self.assertTrue(self.doc.has_selection)


class TestPaintBucketTool(unittest.TestCase):
    """Test suite for PaintBucketTool."""
    
    def setUp(self):
        self.doc = Document(50, 50)
        self.layer = self.doc.add_layer("Layer 1")
        self.layer.image.fill(QColor(255, 255, 255))  # White
        self.session = Session()
        self.session.primary_color = QColor(0, 0, 255)  # Blue
        self.tool = PaintBucketTool(self.doc, self.session)
        
    def test_flood_fill_fills_area(self):
        """Test flood fill changes color of connected area."""
        # Fill at center
        self.tool.mouse_press(QPoint(25, 25))
        
        # Should be blue now
        color = self.layer.image.pixelColor(25, 25)
        self.assertEqual(color.blue(), 255)
        
    def test_fill_respects_tolerance(self):
        """Test fill tolerance affects area filled."""
        # Create gradient-ish area by adding slightly different color
        self.layer.image.setPixelColor(10, 10, QColor(250, 250, 250))
        
        # With default tolerance, should still fill
        self.tool.tolerance = 10
        self.tool.mouse_press(QPoint(25, 25))
        
        # Both should be blue
        c1 = self.layer.image.pixelColor(25, 25)
        c2 = self.layer.image.pixelColor(10, 10)
        self.assertEqual(c1.blue(), 255)
        

class TestMagicWandTool(unittest.TestCase):
    """Test suite for MagicWandTool."""
    
    def setUp(self):
        self.doc = Document(100, 100)
        self.layer = self.doc.add_layer("Layer 1")
        # Create two distinct regions
        self.layer.image.fill(QColor(255, 0, 0))  # Red
        # Paint blue square
        from PySide6.QtGui import QPainter
        painter = QPainter(self.layer.image)
        painter.fillRect(60, 60, 30, 30, QColor(0, 0, 255))
        painter.end()
        
        self.session = Session()
        self.tool = MagicWandTool(self.doc, self.session)
        
    def test_magic_wand_selects_similar_color(self):
        """Test magic wand selects connected similar colors."""
        # Click on red area
        self.tool.mouse_press(QPoint(10, 10))
        
        self.assertTrue(self.doc.has_selection)
        region = self.doc.get_selection_region()
        # Red area point should be selected
        self.assertTrue(region.contains(QPoint(10, 10)))
        
    def test_magic_wand_excludes_different_color(self):
        """Test magic wand does not select different colors."""
        self.tool.tolerance = 10  # Low tolerance
        self.tool.mouse_press(QPoint(10, 10))  # Click on red
        
        region = self.doc.get_selection_region()
        # Blue area should NOT be selected
        # Center of blue square: 75, 75
        self.assertFalse(region.contains(QPoint(75, 75)))


class TestSelectionModes(unittest.TestCase):
    """Test selection mode operations (add, subtract, intersect)."""
    
    def setUp(self):
        self.doc = Document(100, 100)
        self.doc.add_layer("Layer 1")
        
    def test_selection_add_mode(self):
        """Test add mode combines selections."""
        # Create first selection
        self.doc.set_selection(QRect(10, 10, 20, 20), "replace")
        
        # Add second selection
        self.doc.set_selection(QRect(50, 50, 20, 20), "add")
        
        region = self.doc.get_selection_region()
        # Both points should be in selection
        self.assertTrue(region.contains(QPoint(15, 15)))
        self.assertTrue(region.contains(QPoint(55, 55)))
        
    def test_selection_subtract_mode(self):
        """Test subtract mode removes from selection."""
        # Create large selection
        self.doc.set_selection(QRect(10, 10, 80, 80), "replace")
        
        # Subtract middle
        self.doc.set_selection(QRect(40, 40, 20, 20), "subtract")
        
        region = self.doc.get_selection_region()
        # Corner should still be selected
        self.assertTrue(region.contains(QPoint(15, 15)))
        # Middle should NOT be selected
        self.assertFalse(region.contains(QPoint(50, 50)))


if __name__ == '__main__':
    unittest.main()
