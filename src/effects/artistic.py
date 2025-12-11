"""
Artistic effects for Aphelion.
Pencil Sketch, Ink Sketch, Crystallize.
"""
from PySide6.QtGui import QImage, QColor
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                               QSlider, QDialogButtonBox, QSpinBox)
from PySide6.QtCore import Qt
from ..core.effects import Effect
import math
import random


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
    """Pencil sketch artistic effect."""
    name = "Pencil Sketch"
    category = "Artistic"
    
    def create_dialog(self, parent) -> QDialog:
        return PencilSketchDialog(parent)
    
    def apply(self, image: QImage, config: dict) -> QImage:
        detail = config.get("detail", 5)
        
        width = image.width()
        height = image.height()
        result = image.copy()
        
        # Convert to grayscale first
        gray = [[0] * width for _ in range(height)]
        for y in range(height):
            for x in range(width):
                c = image.pixelColor(x, y)
                gray[y][x] = int(c.red() * 0.299 + c.green() * 0.587 + c.blue() * 0.114)
        
        # Apply edge detection (Sobel)
        for y in range(1, height - 1):
            for x in range(1, width - 1):
                # Sobel kernels
                gx = (gray[y-1][x+1] + 2*gray[y][x+1] + gray[y+1][x+1] -
                      gray[y-1][x-1] - 2*gray[y][x-1] - gray[y+1][x-1])
                gy = (gray[y+1][x-1] + 2*gray[y+1][x] + gray[y+1][x+1] -
                      gray[y-1][x-1] - 2*gray[y-1][x] - gray[y-1][x+1])
                
                magnitude = min(255, int(math.sqrt(gx*gx + gy*gy) * detail / 5))
                
                # Invert for pencil effect (dark lines on white)
                val = 255 - magnitude
                result.setPixelColor(x, y, QColor(val, val, val, image.pixelColor(x, y).alpha()))
        
        return result


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
    """Ink sketch effect with high contrast edges."""
    name = "Ink Sketch"
    category = "Artistic"
    
    def create_dialog(self, parent) -> QDialog:
        return InkSketchDialog(parent)
    
    def apply(self, image: QImage, config: dict) -> QImage:
        coverage = config.get("coverage", 50)
        threshold = 255 - int(coverage * 2.55)
        
        width = image.width()
        height = image.height()
        result = image.copy()
        
        # Convert to grayscale
        gray = [[0] * width for _ in range(height)]
        for y in range(height):
            for x in range(width):
                c = image.pixelColor(x, y)
                gray[y][x] = int(c.red() * 0.299 + c.green() * 0.587 + c.blue() * 0.114)
        
        # Edge detection with thresholding
        for y in range(1, height - 1):
            for x in range(1, width - 1):
                gx = abs(gray[y][x+1] - gray[y][x-1])
                gy = abs(gray[y+1][x] - gray[y-1][x])
                edge = gx + gy
                
                # High contrast black/white
                if edge > threshold:
                    result.setPixelColor(x, y, QColor(0, 0, 0, image.pixelColor(x, y).alpha()))
                else:
                    result.setPixelColor(x, y, QColor(255, 255, 255, image.pixelColor(x, y).alpha()))
        
        return result


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
    """Crystallize effect using Voronoi-like cells."""
    name = "Crystallize"
    category = "Distort"
    
    def create_dialog(self, parent) -> QDialog:
        return CrystallizeDialog(parent)
    
    def apply(self, image: QImage, config: dict) -> QImage:
        cell_size = config.get("cell_size", 10)
        
        width = image.width()
        height = image.height()
        result = image.copy()
        
        # Generate random seed points
        seeds = []
        for y in range(0, height, cell_size):
            for x in range(0, width, cell_size):
                # Random offset within cell
                sx = min(width - 1, x + random.randint(0, cell_size - 1))
                sy = min(height - 1, y + random.randint(0, cell_size - 1))
                color = image.pixelColor(sx, sy)
                seeds.append((sx, sy, color))
        
        # Assign each pixel to nearest seed
        for y in range(height):
            for x in range(width):
                min_dist = float('inf')
                best_color = image.pixelColor(x, y)
                
                for sx, sy, color in seeds:
                    dist = (x - sx) ** 2 + (y - sy) ** 2
                    if dist < min_dist:
                        min_dist = dist
                        best_color = color
                
                result.setPixelColor(x, y, best_color)
        
        return result
