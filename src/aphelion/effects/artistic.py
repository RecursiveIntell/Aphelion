"""
Artistic effects for Aphelion.
Pencil Sketch, Ink Sketch, Crystallize - NumPy optimized.
"""
from PySide6.QtGui import QImage, QColor
from PySide6.QtWidgets import QDialog
from PySide6.QtCore import Qt
from ..core.effects import Effect
from ..ui.dialogs import ConfigDialog
from ..ui.dialogs.controls import create_slider_control
from ..utils.image_processing import qimage_to_numpy, numpy_to_qimage
import numpy as np
from scipy.ndimage import sobel
from scipy.spatial import cKDTree


# ----------------- Pencil Sketch Effect -----------------

class PencilSketchEffect(Effect):
    """Pencil sketch artistic effect - NumPy optimized."""
    name = "Pencil Sketch"
    category = "Artistic"

    def create_dialog(self, parent) -> QDialog:
        controls = [
            create_slider_control("detail", "Detail:", 5, 1, 10),
        ]
        return ConfigDialog(self.name, controls, parent)
    
    def apply(self, image: QImage, config: dict) -> QImage:
        detail = config.get("detail", 5)
        
        arr = qimage_to_numpy(image)
        
        # Convert to grayscale (vectorized)
        gray = (arr[:, :, 0].astype(np.float32) * 0.299 + 
                arr[:, :, 1].astype(np.float32) * 0.587 + 
                arr[:, :, 2].astype(np.float32) * 0.114)
        
        # Apply Sobel edge detection (vectorized)
        gx = sobel(gray, axis=1)
        gy = sobel(gray, axis=0)
        magnitude = np.sqrt(gx**2 + gy**2)
        
        # Scale by detail and clamp
        magnitude = np.clip(magnitude * detail / 5, 0, 255)
        
        # Invert for pencil effect (dark lines on white)
        val = 255 - magnitude.astype(np.uint8)
        
        # Create result with grayscale values
        result = arr.copy()
        result[:, :, 0] = val
        result[:, :, 1] = val
        result[:, :, 2] = val
        # Keep alpha
        
        return numpy_to_qimage(result)


# ----------------- Ink Sketch Effect -----------------

class InkSketchEffect(Effect):
    """Ink sketch effect with high contrast edges - NumPy optimized."""
    name = "Ink Sketch"
    category = "Artistic"

    def create_dialog(self, parent) -> QDialog:
        controls = [
            create_slider_control("coverage", "Ink Coverage:", 50, 1, 100),
        ]
        return ConfigDialog(self.name, controls, parent)
    
    def apply(self, image: QImage, config: dict) -> QImage:
        coverage = config.get("coverage", 50)
        threshold = 255 - int(coverage * 2.55)
        
        arr = qimage_to_numpy(image)
        
        # Convert to grayscale (vectorized)
        gray = (arr[:, :, 0].astype(np.float32) * 0.299 + 
                arr[:, :, 1].astype(np.float32) * 0.587 + 
                arr[:, :, 2].astype(np.float32) * 0.114)
        
        # Simple gradient edge detection (vectorized)
        gx = np.abs(np.diff(gray, axis=1, prepend=gray[:, :1]))
        gy = np.abs(np.diff(gray, axis=0, prepend=gray[:1, :]))
        edge = gx + gy
        
        # Threshold to black/white
        black_mask = edge > threshold
        
        result = arr.copy()
        result[:, :, 0] = np.where(black_mask, 0, 255)
        result[:, :, 1] = np.where(black_mask, 0, 255)
        result[:, :, 2] = np.where(black_mask, 0, 255)
        # Keep alpha
        
        return numpy_to_qimage(result)


# ----------------- Crystallize Effect -----------------

class CrystallizeEffect(Effect):
    """Crystallize effect using Voronoi-like cells - NumPy optimized."""
    name = "Crystallize"
    category = "Distort"

    def create_dialog(self, parent) -> QDialog:
        controls = [
            create_slider_control("cell_size", "Cell Size:", 10, 3, 50),
        ]
        return ConfigDialog(self.name, controls, parent)
    
    def apply(self, image: QImage, config: dict) -> QImage:
        cell_size = config.get("cell_size", 10)
        
        arr = qimage_to_numpy(image)
        height, width = arr.shape[:2]
        
        # Generate seed points on a grid with random offset
        np.random.seed(42)  # Reproducible results
        seeds = []
        seed_colors = []
        
        for y in range(0, height, cell_size):
            for x in range(0, width, cell_size):
                # Random offset within cell
                sx = min(width - 1, x + np.random.randint(0, cell_size))
                sy = min(height - 1, y + np.random.randint(0, cell_size))
                seeds.append((sx, sy))
                seed_colors.append(arr[sy, sx].copy())
        
        seeds = np.array(seeds)
        seed_colors = np.array(seed_colors)
        
        # Create coordinate grid
        yy, xx = np.mgrid[0:height, 0:width]
        coords = np.stack([xx.ravel(), yy.ravel()], axis=1)
        
        # Use KD-tree for fast nearest neighbor lookup
        tree = cKDTree(seeds)
        _, indices = tree.query(coords)
        
        # Reshape indices and assign colors
        indices = indices.reshape(height, width)
        result = seed_colors[indices]
        
        return numpy_to_qimage(result)
