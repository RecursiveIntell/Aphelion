#!/usr/bin/env python3
"""
Cairo Renderer Tests

Tests for the Cairo-based rendering backend, including:
- NumPy ↔ Cairo surface conversions
- QImage ↔ Cairo surface conversions
- Layer compositing with opacity
- Alpha correctness
"""
import sys
import os
import unittest

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import numpy as np
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QImage, QColor, QPainter
from PySide6.QtCore import Qt

from aphelion.core.renderer_cairo import (
    CairoRenderer,
    numpy_to_cairo_surface,
    cairo_surface_to_numpy,
    qimage_to_cairo_surface,
    cairo_surface_to_qimage,
)
from aphelion.core.document import Document

# Init Qt
app = QApplication.instance() or QApplication([])


class TestCairoNumpyConversion(unittest.TestCase):
    """Test NumPy ↔ Cairo surface conversions."""
    
    def test_roundtrip_solid_color(self):
        """Solid color should survive round-trip exactly."""
        # Create BGRA array (premultiplied)
        arr = np.zeros((10, 10, 4), dtype=np.uint8)
        arr[:, :, 0] = 50   # Blue
        arr[:, :, 1] = 100  # Green
        arr[:, :, 2] = 150  # Red
        arr[:, :, 3] = 255  # Alpha (fully opaque)
        
        surface = numpy_to_cairo_surface(arr)
        result = cairo_surface_to_numpy(surface)
        
        np.testing.assert_array_equal(result, arr)
    
    def test_roundtrip_with_transparency(self):
        """Transparent pixels should round-trip correctly."""
        arr = np.zeros((5, 5, 4), dtype=np.uint8)
        # Premultiplied: RGB values scaled by alpha
        arr[2, 2, :] = [25, 50, 100, 128]  # 50% alpha
        
        surface = numpy_to_cairo_surface(arr)
        result = cairo_surface_to_numpy(surface)
        
        np.testing.assert_array_equal(result, arr)
    
    def test_stride_handling(self):
        """Non-aligned width should be handled correctly."""
        # Use odd width that may require stride padding
        arr = np.zeros((10, 13, 4), dtype=np.uint8)
        arr[:, :, 2] = 200  # Red
        arr[:, :, 3] = 255
        
        surface = numpy_to_cairo_surface(arr)
        self.assertEqual(surface.get_width(), 13)
        self.assertEqual(surface.get_height(), 10)


class TestCairoQImageConversion(unittest.TestCase):
    """Test QImage ↔ Cairo surface conversions."""
    
    def test_roundtrip_qimage(self):
        """QImage should round-trip through Cairo."""
        img = QImage(10, 10, QImage.Format.Format_ARGB32_Premultiplied)
        img.fill(QColor(128, 64, 32, 255))
        
        surface = qimage_to_cairo_surface(img)
        result = cairo_surface_to_qimage(surface)
        
        # Check pixels
        for x in range(10):
            for y in range(10):
                orig = img.pixelColor(x, y)
                new = result.pixelColor(x, y)
                self.assertEqual(orig.red(), new.red())
                self.assertEqual(orig.green(), new.green())
                self.assertEqual(orig.blue(), new.blue())
                self.assertEqual(orig.alpha(), new.alpha())
    
    def test_qimage_with_alpha(self):
        """QImage with varying alpha should convert correctly."""
        img = QImage(4, 4, QImage.Format.Format_ARGB32_Premultiplied)
        img.fill(QColor(0, 0, 0, 0))
        img.setPixelColor(1, 1, QColor(255, 0, 0, 255))
        img.setPixelColor(2, 2, QColor(0, 255, 0, 128))
        
        surface = qimage_to_cairo_surface(img)
        result = cairo_surface_to_qimage(surface)
        
        # Check specific pixels
        p1 = result.pixelColor(1, 1)
        self.assertEqual(p1.red(), 255)
        self.assertEqual(p1.alpha(), 255)
        
        p2 = result.pixelColor(2, 2)
        self.assertEqual(p2.alpha(), 128)


class TestCairoRendererCompositing(unittest.TestCase):
    """Test layer compositing with CairoRenderer."""
    
    def test_single_layer_render(self):
        """Single opaque layer should render correctly."""
        doc = Document(50, 50)
        layer = doc.add_layer("Layer 1")
        layer.image.fill(QColor(255, 0, 0, 255))  # Red
        
        result = doc.render()
        
        self.assertEqual(result.width(), 50)
        self.assertEqual(result.height(), 50)
        
        color = result.pixelColor(25, 25)
        self.assertEqual(color.red(), 255)
        self.assertEqual(color.green(), 0)
        self.assertEqual(color.blue(), 0)
    
    def test_layer_opacity(self):
        """Layer opacity should affect rendering."""
        doc = Document(50, 50)
        
        # Bottom: white
        layer1 = doc.add_layer("White")
        layer1.image.fill(QColor(255, 255, 255, 255))
        
        # Top: black at 50% opacity
        layer2 = doc.add_layer("Black 50%")
        layer2.image.fill(QColor(0, 0, 0, 255))
        layer2.opacity = 0.5
        
        result = doc.render()
        color = result.pixelColor(25, 25)
        
        # Should be gray-ish (white blended with 50% black)
        # Expected: ~128 for each channel
        self.assertGreater(color.red(), 100)
        self.assertLess(color.red(), 160)
    
    def test_transparent_layer_stacking(self):
        """Transparent regions should show through."""
        doc = Document(50, 50)
        
        # Bottom: red
        layer1 = doc.add_layer("Red")
        layer1.image.fill(QColor(255, 0, 0, 255))
        
        # Top: transparent with blue center
        layer2 = doc.add_layer("Blue Center")
        layer2.image.fill(QColor(0, 0, 0, 0))
        layer2.image.setPixelColor(25, 25, QColor(0, 0, 255, 255))
        
        result = doc.render()
        
        # Corner should be red (from bottom layer)
        corner = result.pixelColor(0, 0)
        self.assertEqual(corner.red(), 255)
        self.assertEqual(corner.blue(), 0)
        
        # Center should be blue (from top layer)
        center = result.pixelColor(25, 25)
        self.assertEqual(center.blue(), 255)
        self.assertEqual(center.red(), 0)
    
    def test_layer_visibility(self):
        """Hidden layers should not affect rendering."""
        doc = Document(50, 50)
        
        layer1 = doc.add_layer("Visible")
        layer1.image.fill(QColor(255, 0, 0, 255))
        
        layer2 = doc.add_layer("Hidden")
        layer2.image.fill(QColor(0, 0, 255, 255))
        layer2.visible = False
        
        result = doc.render()
        color = result.pixelColor(25, 25)
        
        # Should be red (blue layer is hidden)
        self.assertEqual(color.red(), 255)
        self.assertEqual(color.blue(), 0)


class TestCairoRendererCache(unittest.TestCase):
    """Test layer cache invalidation."""
    
    def test_cache_invalidation(self):
        """Modifying layer should update render."""
        doc = Document(50, 50)
        layer = doc.add_layer("Layer")
        layer.image.fill(QColor(255, 0, 0, 255))
        
        # First render - red
        r1 = doc.render()
        self.assertEqual(r1.pixelColor(25, 25).red(), 255)
        
        # Modify layer
        layer.image.fill(QColor(0, 0, 255, 255))
        doc.content_changed.emit()  # Trigger cache invalidation
        
        # Second render - should be blue
        r2 = doc.render()
        self.assertEqual(r2.pixelColor(25, 25).blue(), 255)


if __name__ == '__main__':
    unittest.main()
