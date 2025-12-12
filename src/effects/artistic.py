"""
Artistic effects for Aphelion.
Pencil Sketch, Ink Sketch, Crystallize - NumPy optimized.
"""
from PySide6.QtGui import QImage, QColor
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                               QSlider, QDialogButtonBox, QSpinBox)
from PySide6.QtCore import Qt
from ..core.effects import Effect
from ..utils.image_processing import qimage_to_numpy, numpy_to_qimage
import numpy as np
from scipy.ndimage import sobel
from scipy.spatial import cKDTree


# ----------------- Pencil Sketch Effect -----------------

class PencilSketchDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Pencil Sketch")
        
        layout = QVBoxLayout()
        
        # Stroke intensity
        s_layout = QHBoxLayout()
        s_layout.addWidget(QLabel("Detail:"))
        self.s_slider = QSlider(Qt.Orientation.Horizontal)
        self.s_slider.setRange(1, 10)
        self.s_slider.setValue(5)
        s_layout.addWidget(self.s_slider)
        layout.addLayout(s_layout)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
    
    def get_config(self):
        return {"detail": self.s_slider.value()}


class PencilSketchEffect(Effect):
    """Pencil sketch artistic effect - NumPy optimized."""
    name = "Pencil Sketch"
    category = "Artistic"
    
    def create_dialog(self, parent) -> QDialog:
        return PencilSketchDialog(parent)
    
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

class InkSketchDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ink Sketch")
        
        layout = QVBoxLayout()
        
        # Coverage
        c_layout = QHBoxLayout()
        c_layout.addWidget(QLabel("Ink Coverage:"))
        self.c_slider = QSlider(Qt.Orientation.Horizontal)
        self.c_slider.setRange(1, 100)
        self.c_slider.setValue(50)
        c_layout.addWidget(self.c_slider)
        layout.addLayout(c_layout)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
    
    def get_config(self):
        return {"coverage": self.c_slider.value()}


class InkSketchEffect(Effect):
    """Ink sketch effect with high contrast edges - NumPy optimized."""
    name = "Ink Sketch"
    category = "Artistic"
    
    def create_dialog(self, parent) -> QDialog:
        return InkSketchDialog(parent)
    
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

class CrystallizeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Crystallize")
        
        layout = QVBoxLayout()
        
        # Cell size
        s_layout = QHBoxLayout()
        s_layout.addWidget(QLabel("Cell Size:"))
        self.s_spin = QSpinBox()
        self.s_spin.setRange(3, 50)
        self.s_spin.setValue(10)
        s_layout.addWidget(self.s_spin)
        layout.addLayout(s_layout)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
    
    def get_config(self):
        return {"cell_size": self.s_spin.value()}


class CrystallizeEffect(Effect):
    """Crystallize effect using Voronoi-like cells - NumPy optimized."""
    name = "Crystallize"
    category = "Distort"
    
    def create_dialog(self, parent) -> QDialog:
        return CrystallizeDialog(parent)
    
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
