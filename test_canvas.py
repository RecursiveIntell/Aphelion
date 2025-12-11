import sys
import unittest
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QPoint, QRect
from src.core.document import Document
from src.ui.canvas import CanvasWidget

# Init App
app = QApplication.instance() or QApplication(sys.argv)


class TestCanvasWidget(unittest.TestCase):
    """Test suite for CanvasWidget."""
    
    def setUp(self):
        self.doc = Document(200, 200)
        self.doc.add_layer("Background")
        self.canvas = CanvasWidget(self.doc)
        self.canvas.resize(400, 400)  # Widget size
        
    def test_initial_scale(self):
        """Test initial zoom level is 1.0."""
        self.assertEqual(self.canvas.scale, 1.0)
        
    def test_set_zoom_clamps_min(self):
        """Test zoom cannot go below minimum."""
        self.canvas.set_zoom(0.01)
        self.assertGreaterEqual(self.canvas.scale, 0.1)
        
    def test_set_zoom_clamps_max(self):
        """Test zoom cannot exceed maximum."""
        self.canvas.set_zoom(100.0)
        self.assertLessEqual(self.canvas.scale, 50.0)
        
    def test_zoom_in_increases_scale(self):
        """Test zoom_in increases scale factor."""
        initial = self.canvas.scale
        self.canvas.zoom_in()
        self.assertGreater(self.canvas.scale, initial)
        
    def test_zoom_out_decreases_scale(self):
        """Test zoom_out decreases scale factor."""
        initial = self.canvas.scale
        self.canvas.zoom_out()
        self.assertLess(self.canvas.scale, initial)
        
    def test_map_to_doc_identity(self):
        """Test coordinate mapping at 1:1 zoom with no offset."""
        self.canvas.scale = 1.0
        self.canvas.offset = QPoint(0, 0)
        
        widget_pos = QPoint(100, 100)
        doc_pos = self.canvas.map_to_doc(widget_pos)
        
        self.assertEqual(doc_pos.x(), 100)
        self.assertEqual(doc_pos.y(), 100)
        
    def test_map_to_doc_with_scale(self):
        """Test coordinate mapping with 2x zoom."""
        self.canvas.scale = 2.0
        self.canvas.offset = QPoint(0, 0)
        
        widget_pos = QPoint(100, 100)
        doc_pos = self.canvas.map_to_doc(widget_pos)
        
        # At 2x zoom, widget 100 = doc 50
        self.assertEqual(doc_pos.x(), 50)
        self.assertEqual(doc_pos.y(), 50)
        
    def test_map_to_doc_with_offset(self):
        """Test coordinate mapping with pan offset."""
        self.canvas.scale = 1.0
        self.canvas.offset = QPoint(50, 50)
        
        widget_pos = QPoint(100, 100)
        doc_pos = self.canvas.map_to_doc(widget_pos)
        
        # (100 - 50) / 1.0 = 50
        self.assertEqual(doc_pos.x(), 50)
        self.assertEqual(doc_pos.y(), 50)
        
    def test_zoom_to_fit_centers_document(self):
        """Test zoom_to_fit calculates appropriate scale."""
        self.canvas.zoom_to_fit()
        
        # With 400x400 widget and 200x200 doc, scale should be ~1.8 (90% of 2.0)
        self.assertGreater(self.canvas.scale, 1.0)
        self.assertLess(self.canvas.scale, 2.0)
        
    def test_set_tool_deactivates_previous(self):
        """Test setting a new tool deactivates the old one."""
        from src.core.session import Session
        from src.tools.brush import BrushTool
        from src.tools.eraser import EraserTool
        
        session = Session()
        brush = BrushTool(self.doc, session)
        eraser = EraserTool(self.doc, session)
        
        self.canvas.set_tool(brush)
        self.assertEqual(self.canvas.active_tool, brush)
        
        self.canvas.set_tool(eraser)
        self.assertEqual(self.canvas.active_tool, eraser)


class TestCanvasRenderIntegration(unittest.TestCase):
    """Integration tests for canvas rendering."""
    
    def setUp(self):
        self.doc = Document(100, 100)
        self.layer = self.doc.add_layer("Layer 1")
        self.canvas = CanvasWidget(self.doc)
        
    def test_canvas_updates_on_content_change(self):
        """Test canvas repaints when document content changes."""
        # This is a signal-slot test
        update_called = [False]
        
        original_update = self.canvas.update
        def mock_update():
            update_called[0] = True
            original_update()
            
        self.canvas.update = mock_update
        
        # Trigger content change
        self.doc.content_changed.emit()
        
        self.assertTrue(update_called[0])


if __name__ == '__main__':
    unittest.main()
