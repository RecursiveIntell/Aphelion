import sys
import unittest
import os
import tempfile
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QColor, QPainter
from src.core.document import Document
from src.core.io import ProjectIO

# Init App
app = QApplication.instance() or QApplication(sys.argv)

class TestProjectIO(unittest.TestCase):
    """Test suite for ProjectIO file operations."""
    
    def setUp(self):
        self.doc = Document(100, 100)
        self.layer1 = self.doc.add_layer("Layer 1")
        self.layer1.image.fill(QColor(255, 0, 0))  # Red
        
        self.layer2 = self.doc.add_layer("Layer 2")
        self.layer2.image.fill(QColor(0, 255, 0))  # Green
        self.layer2.opacity = 0.5
        self.layer2.visible = False
        
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_save_and_load_project(self):
        """Test round-trip save/load preserves document structure."""
        filepath = os.path.join(self.temp_dir, "test_project.aphelion")
        
        # Save
        ProjectIO.save_project(self.doc, filepath)
        self.assertTrue(os.path.exists(filepath))
        
        # Load
        loaded_doc = ProjectIO.load_project(filepath)
        
        # Verify dimensions
        self.assertEqual(loaded_doc.size.width(), 100)
        self.assertEqual(loaded_doc.size.height(), 100)
        
        # Verify layer count
        self.assertEqual(len(loaded_doc.layers), 2)
        
    def test_layer_properties_preserved(self):
        """Test that layer properties survive save/load."""
        filepath = os.path.join(self.temp_dir, "test_props.aphelion")
        
        ProjectIO.save_project(self.doc, filepath)
        loaded_doc = ProjectIO.load_project(filepath)
        
        # Find Layer 2 (should be second)
        layer2 = loaded_doc.layers[1]
        self.assertEqual(layer2.name, "Layer 2")
        self.assertAlmostEqual(layer2.opacity, 0.5, places=2)
        self.assertFalse(layer2.visible)
        
    def test_layer_content_preserved(self):
        """Test that pixel data survives save/load."""
        filepath = os.path.join(self.temp_dir, "test_content.aphelion")
        
        ProjectIO.save_project(self.doc, filepath)
        loaded_doc = ProjectIO.load_project(filepath)
        
        # Check Layer 1 is red
        layer1 = loaded_doc.layers[0]
        color = layer1.image.pixelColor(50, 50)
        self.assertEqual(color.red(), 255)
        self.assertEqual(color.green(), 0)
        self.assertEqual(color.blue(), 0)
        
    def test_export_flat_png(self):
        """Test exporting flattened PNG."""
        filepath = os.path.join(self.temp_dir, "test_export.png")
        
        # Make Layer 2 visible for composite
        self.layer2.visible = True
        
        ProjectIO.export_flat(self.doc, filepath)
        self.assertTrue(os.path.exists(filepath))
        
        # Verify it's a valid image
        from PySide6.QtGui import QImage
        img = QImage(filepath)
        self.assertFalse(img.isNull())
        self.assertEqual(img.width(), 100)
        self.assertEqual(img.height(), 100)
        
    def test_invalid_project_file(self):
        """Test loading invalid file raises error."""
        filepath = os.path.join(self.temp_dir, "invalid.aphelion")
        
        # Create invalid zip
        import zipfile
        with zipfile.ZipFile(filepath, 'w') as zf:
            zf.writestr("garbage.txt", "not a manifest")
            
        with self.assertRaises(ValueError):
            ProjectIO.load_project(filepath)


class TestHistoryManagerEdgeCases(unittest.TestCase):
    """Test edge cases in HistoryManager."""
    
    def setUp(self):
        self.doc = Document(50, 50)
        
    def test_history_limit_enforced(self):
        """Test that history respects the limit."""
        # Default limit is 50, add 55 operations
        for i in range(55):
            self.doc.add_layer(f"Layer {i}")
            
        # Should have at most 50 items
        self.assertLessEqual(len(self.doc.history.undo_stack), 50)
        
    def test_goto_index_within_bounds(self):
        """Test goto_index navigates history correctly."""
        l1 = self.doc.add_layer("L1")
        l2 = self.doc.add_layer("L2")
        l3 = self.doc.add_layer("L3")
        
        # Stack has 3 items, indices 0, 1, 2
        self.assertEqual(len(self.doc.layers), 3)
        
        # Go to index 0 (after first add)
        self.doc.history.goto_index(0)
        self.assertEqual(len(self.doc.layers), 1)
        
    def test_goto_index_out_of_bounds(self):
        """Test goto_index handles invalid index gracefully."""
        self.doc.add_layer("L1")
        
        # These should not crash
        self.doc.history.goto_index(-1)
        self.doc.history.goto_index(100)
        
    def test_undo_empty_stack(self):
        """Test undo on empty stack returns False."""
        # Fresh document, no history
        result = self.doc.history.undo()
        self.assertFalse(result)
        
    def test_redo_empty_stack(self):
        """Test redo on empty stack returns False."""
        result = self.doc.history.redo()
        self.assertFalse(result)


class TestDocumentRender(unittest.TestCase):
    """Test Document.render() compositing."""
    
    def setUp(self):
        self.doc = Document(10, 10)
        
    def test_render_single_layer(self):
        """Test render with single opaque layer."""
        layer = self.doc.add_layer("Red")
        layer.image.fill(QColor(255, 0, 0))
        
        result = self.doc.render()
        color = result.pixelColor(5, 5)
        self.assertEqual(color.red(), 255)
        
    def test_render_hidden_layer_excluded(self):
        """Test hidden layers are not rendered."""
        layer1 = self.doc.add_layer("Red")
        layer1.image.fill(QColor(255, 0, 0))
        
        layer2 = self.doc.add_layer("Blue")
        layer2.image.fill(QColor(0, 0, 255))
        layer2.visible = False
        
        result = self.doc.render()
        color = result.pixelColor(5, 5)
        # Should be red (blue is hidden)
        self.assertEqual(color.red(), 255)
        self.assertEqual(color.blue(), 0)
        
    def test_render_respects_opacity(self):
        """Test layer opacity affects rendering."""
        layer1 = self.doc.add_layer("Red")
        layer1.image.fill(QColor(255, 0, 0))
        
        layer2 = self.doc.add_layer("Blue")
        layer2.image.fill(QColor(0, 0, 255))
        layer2.opacity = 0.5
        
        result = self.doc.render()
        color = result.pixelColor(5, 5)
        # Blue at 50% over red should give purple-ish
        self.assertGreater(color.red(), 0)
        self.assertGreater(color.blue(), 0)


if __name__ == '__main__':
    unittest.main()
