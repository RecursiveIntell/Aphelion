"""
Correctness tests for NumPy image processing utilities.

Tests the "don't get wrecked" checklist:
- Round trip QImage → numpy → QImage preserves pixels
- Alpha blend of two known pixels matches expected
- Premultiply/unpremultiply are inverses
"""
import sys
import unittest
import numpy as np
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QImage, QColor

from src.utils.image_processing import (
    qimage_to_numpy, numpy_to_qimage,
    qimage_alpha8_to_numpy, numpy_to_qimage_alpha8,
    premultiply_alpha, unpremultiply_alpha,
    gaussian_blur_np, morphological_dilate, morphological_erode
)

# Init App
app = QApplication.instance() or QApplication(sys.argv)


class TestQImageNumPyRoundTrip(unittest.TestCase):
    """Test QImage ↔ NumPy conversions preserve pixel data."""
    
    def test_round_trip_solid_color(self):
        """Solid color image should survive round trip exactly."""
        img = QImage(10, 10, QImage.Format.Format_ARGB32_Premultiplied)
        img.fill(QColor(128, 64, 32, 255))
        
        arr = qimage_to_numpy(img)
        result = numpy_to_qimage(arr)
        
        # Check a few pixels
        for x in range(10):
            for y in range(10):
                orig = img.pixelColor(x, y)
                new = result.pixelColor(x, y)
                self.assertEqual(orig.red(), new.red())
                self.assertEqual(orig.green(), new.green())
                self.assertEqual(orig.blue(), new.blue())
                self.assertEqual(orig.alpha(), new.alpha())
    
    def test_round_trip_gradient(self):
        """Gradient image should survive round trip."""
        img = QImage(256, 1, QImage.Format.Format_ARGB32_Premultiplied)
        for x in range(256):
            img.setPixelColor(x, 0, QColor(x, 255-x, x//2, 255))
        
        arr = qimage_to_numpy(img)
        result = numpy_to_qimage(arr)
        
        for x in range(256):
            orig = img.pixelColor(x, 0)
            new = result.pixelColor(x, 0)
            self.assertEqual(orig.red(), new.red())
            self.assertEqual(orig.green(), new.green())
            self.assertEqual(orig.blue(), new.blue())
    
    def test_round_trip_alpha8(self):
        """Alpha8 mask should survive round trip."""
        img = QImage(10, 10, QImage.Format.Format_Alpha8)
        img.fill(0)
        img.setPixelColor(5, 5, QColor(0, 0, 0, 200))
        
        arr = qimage_alpha8_to_numpy(img)
        result = numpy_to_qimage_alpha8(arr)
        
        # Check center pixel
        self.assertEqual(result.pixelColor(5, 5).alpha(), 200)
        self.assertEqual(result.pixelColor(0, 0).alpha(), 0)


class TestPremultiplyAlpha(unittest.TestCase):
    """Test premultiply/unpremultiply are inverses."""
    
    def test_premultiply_unpremultiply_roundtrip(self):
        """Straight → premultiply → unpremultiply should be identity."""
        # Create straight alpha image (BGRA)
        arr = np.array([[[100, 150, 200, 128]]], dtype=np.uint8)
        
        premul = premultiply_alpha(arr.copy())
        unpremul = unpremultiply_alpha(premul)
        
        # Should be close to original (allow ±1 for rounding)
        np.testing.assert_allclose(unpremul, arr, atol=2)
    
    def test_premultiply_known_values(self):
        """Test premultiply with known expected values."""
        # 50% alpha, RGB = (200, 100, 50) in BGRA format
        arr = np.array([[[50, 100, 200, 128]]], dtype=np.uint8)  # BGRA
        
        premul = premultiply_alpha(arr)
        
        # 128/255 ≈ 0.502, so values should be halved
        self.assertAlmostEqual(premul[0, 0, 0], 25, delta=2)   # B: 50 * 0.5
        self.assertAlmostEqual(premul[0, 0, 1], 50, delta=2)   # G: 100 * 0.5
        self.assertAlmostEqual(premul[0, 0, 2], 100, delta=2)  # R: 200 * 0.5
        self.assertEqual(premul[0, 0, 3], 128)                  # Alpha unchanged
    
    def test_fully_opaque_unchanged(self):
        """Fully opaque pixels should not change with premultiply."""
        arr = np.array([[[100, 150, 200, 255]]], dtype=np.uint8)
        
        premul = premultiply_alpha(arr.copy())
        
        np.testing.assert_array_equal(premul, arr)
    
    def test_fully_transparent_zeros_rgb(self):
        """Fully transparent pixels should have zero RGB after premultiply."""
        arr = np.array([[[100, 150, 200, 0]]], dtype=np.uint8)
        
        premul = premultiply_alpha(arr)
        
        self.assertEqual(premul[0, 0, 0], 0)
        self.assertEqual(premul[0, 0, 1], 0)
        self.assertEqual(premul[0, 0, 2], 0)


class TestMorphologicalOps(unittest.TestCase):
    """Test morphological operations on masks."""
    
    def test_dilate_expands(self):
        """Dilation should expand white regions."""
        mask = np.zeros((10, 10), dtype=np.uint8)
        mask[5, 5] = 255  # Single white pixel
        
        dilated = morphological_dilate(mask, radius=1)
        
        # Center and neighbors should be white
        self.assertEqual(dilated[5, 5], 255)
        self.assertEqual(dilated[4, 5], 255)
        self.assertEqual(dilated[6, 5], 255)
        self.assertEqual(dilated[5, 4], 255)
        self.assertEqual(dilated[5, 6], 255)
    
    def test_erode_shrinks(self):
        """Erosion should shrink white regions."""
        mask = np.full((10, 10), 255, dtype=np.uint8)
        mask[0, :] = 0  # Black edge
        
        eroded = morphological_erode(mask, radius=1)
        
        # First row should still be black
        self.assertEqual(eroded[0, 5], 0)
        # Second row should now be black (eroded into edge)
        self.assertEqual(eroded[1, 5], 0)
    
    def test_dilate_erode_roundtrip(self):
        """Dilate then erode should roughly preserve shape."""
        mask = np.zeros((20, 20), dtype=np.uint8)
        mask[5:15, 5:15] = 255  # 10x10 square
        
        dilated = morphological_dilate(mask, radius=2)
        eroded = morphological_erode(dilated, radius=2)
        
        # Center should still be white
        self.assertEqual(eroded[10, 10], 255)


class TestGaussianBlur(unittest.TestCase):
    """Test Gaussian blur implementation."""
    
    def test_blur_reduces_contrast(self):
        """Blurring should reduce contrast between adjacent pixels."""
        arr = np.zeros((10, 10, 4), dtype=np.uint8)
        arr[5, 5, :] = [255, 255, 255, 255]  # Single white pixel
        
        blurred = gaussian_blur_np(arr, sigma=1.0)
        
        # Center should be less bright
        self.assertLess(blurred[5, 5, 0], 255)
        # Neighbors should be brighter than 0
        self.assertGreater(blurred[5, 4, 0], 0)
        self.assertGreater(blurred[4, 5, 0], 0)
    
    def test_blur_sigma_zero_unchanged(self):
        """Sigma=0 should return unchanged image."""
        arr = np.array([[[100, 150, 200, 255]]], dtype=np.uint8)
        
        blurred = gaussian_blur_np(arr, sigma=0)
        
        np.testing.assert_array_equal(blurred, arr)


if __name__ == '__main__':
    unittest.main()
