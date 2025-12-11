"""
Render and stylize effects for Aphelion.
"""
from PySide6.QtGui import QImage, QColor
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QSlider, QDialogButtonBox, QSpinBox
from PySide6.QtCore import Qt
from ..core.effects import Effect
import math
import random


class GlowDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Glow")
        
        layout = QVBoxLayout()
        
        r_layout = QHBoxLayout()
        r_layout.addWidget(QLabel("Radius:"))
        self.r_spin = QSpinBox()
        self.r_spin.setRange(1, 20)
        self.r_spin.setValue(5)
        r_layout.addWidget(self.r_spin)
        layout.addLayout(r_layout)
        
        b_layout = QHBoxLayout()
        b_layout.addWidget(QLabel("Brightness:"))
        self.b_slider = QSlider(Qt.Orientation.Horizontal)
        self.b_slider.setRange(0, 100)
        self.b_slider.setValue(50)
        b_layout.addWidget(self.b_slider)
        layout.addLayout(b_layout)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
    
    def get_config(self):
        return {"radius": self.r_spin.value(), "brightness": self.b_slider.value()}


class GlowEffect(Effect):
    """Soft glow effect - blur bright areas and blend."""
    name = "Glow"
    category = "Photo"
    
    def create_dialog(self, parent) -> QDialog:
        return GlowDialog(parent)
    
    def apply(self, image: QImage, config: dict) -> QImage:
        radius = config.get("radius", 5)
        brightness = config.get("brightness", 50) / 100.0
        
        width = image.width()
        height = image.height()
        
        # Create glow layer (blur of bright pixels)
        glow = QImage(width, height, QImage.Format.Format_ARGB32_Premultiplied)
        glow.fill(0)
        
        # Simple box blur for glow
        for y in range(height):
            for x in range(width):
                r_sum = g_sum = b_sum = 0
                count = 0
                
                for dy in range(-radius, radius + 1):
                    for dx in range(-radius, radius + 1):
                        nx = x + dx
                        ny = y + dy
                        if 0 <= nx < width and 0 <= ny < height:
                            c = image.pixelColor(nx, ny)
                            # Weight by brightness
                            lum = (c.red() + c.green() + c.blue()) / 3
                            weight = lum / 255.0
                            r_sum += c.red() * weight
                            g_sum += c.green() * weight
                            b_sum += c.blue() * weight
                            count += 1
                
                if count > 0:
                    glow.setPixelColor(x, y, QColor(
                        int(min(255, r_sum / count * 2)),
                        int(min(255, g_sum / count * 2)),
                        int(min(255, b_sum / count * 2)),
                        255
                    ))
        
        # Blend glow with original (screen blend)
        result = image.copy()
        for y in range(height):
            for x in range(width):
                orig = image.pixelColor(x, y)
                g = glow.pixelColor(x, y)
                
                # Screen blend: 1 - (1-a)*(1-b)
                r = int(255 - (255 - orig.red()) * (255 - g.red() * brightness) / 255)
                gr = int(255 - (255 - orig.green()) * (255 - g.green() * brightness) / 255)
                b = int(255 - (255 - orig.blue()) * (255 - g.blue() * brightness) / 255)
                
                result.setPixelColor(x, y, QColor(
                    min(255, max(0, r)),
                    min(255, max(0, gr)),
                    min(255, max(0, b)),
                    orig.alpha()
                ))
        
        return result


class OutlineEffect(Effect):
    """Draw outline around edges."""
    name = "Outline"
    category = "Stylize"
    
    def apply(self, image: QImage, config: dict) -> QImage:
        width = image.width()
        height = image.height()
        result = QImage(width, height, QImage.Format.Format_ARGB32_Premultiplied)
        result.fill(QColor(255, 255, 255))
        
        # Sobel edge detection
        for y in range(1, height - 1):
            for x in range(1, width - 1):
                gx = 0
                gy = 0
                
                # Sobel kernels
                for ky in range(-1, 2):
                    for kx in range(-1, 2):
                        c = image.pixelColor(x + kx, y + ky)
                        gray = (c.red() + c.green() + c.blue()) // 3
                        
                        # Gx kernel
                        if kx == -1: gx -= gray * (2 if ky == 0 else 1)
                        elif kx == 1: gx += gray * (2 if ky == 0 else 1)
                        
                        # Gy kernel
                        if ky == -1: gy -= gray * (2 if kx == 0 else 1)
                        elif ky == 1: gy += gray * (2 if kx == 0 else 1)
                
                magnitude = int(min(255, math.sqrt(gx*gx + gy*gy)))
                # Invert for outline (dark on white)
                val = 255 - magnitude
                result.setPixelColor(x, y, QColor(val, val, val, 255))
        
        return result


class FragmentDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Fragment")
        
        layout = QVBoxLayout()
        
        c_layout = QHBoxLayout()
        c_layout.addWidget(QLabel("Count:"))
        self.c_spin = QSpinBox()
        self.c_spin.setRange(2, 8)
        self.c_spin.setValue(4)
        c_layout.addWidget(self.c_spin)
        layout.addLayout(c_layout)
        
        d_layout = QHBoxLayout()
        d_layout.addWidget(QLabel("Distance:"))
        self.d_spin = QSpinBox()
        self.d_spin.setRange(1, 20)
        self.d_spin.setValue(5)
        d_layout.addWidget(self.d_spin)
        layout.addLayout(d_layout)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
    
    def get_config(self):
        return {"count": self.c_spin.value(), "distance": self.d_spin.value()}


class FragmentEffect(Effect):
    """Fragment effect - creates ghosting copies."""
    name = "Fragment"
    category = "Stylize"
    
    def create_dialog(self, parent) -> QDialog:
        return FragmentDialog(parent)
    
    def apply(self, image: QImage, config: dict) -> QImage:
        count = config.get("count", 4)
        distance = config.get("distance", 5)
        
        width = image.width()
        height = image.height()
        result = image.copy()
        
        for y in range(height):
            for x in range(width):
                r_sum = g_sum = b_sum = 0
                
                for i in range(count):
                    angle = (i / count) * 2 * math.pi
                    dx = int(distance * math.cos(angle))
                    dy = int(distance * math.sin(angle))
                    
                    sx = max(0, min(width - 1, x + dx))
                    sy = max(0, min(height - 1, y + dy))
                    
                    c = image.pixelColor(sx, sy)
                    r_sum += c.red()
                    g_sum += c.green()
                    b_sum += c.blue()
                
                result.setPixelColor(x, y, QColor(
                    r_sum // count,
                    g_sum // count,
                    b_sum // count,
                    image.pixelColor(x, y).alpha()
                ))
        
        return result


class CloudsEffect(Effect):
    """Render clouds using Perlin-like noise."""
    name = "Clouds"
    category = "Render"
    
    def apply(self, image: QImage, config: dict) -> QImage:
        width = image.width()
        height = image.height()
        result = QImage(width, height, QImage.Format.Format_ARGB32_Premultiplied)
        
        # Simple fractal noise
        for y in range(height):
            for x in range(width):
                val = 0
                scale = 64
                amp = 128
                
                for _ in range(4):
                    # Use deterministic noise based on position
                    noise = ((x * 13 + y * 7 + scale * 5) % 256) / 256.0
                    val += noise * amp
                    scale //= 2
                    amp //= 2
                
                val = int(min(255, max(0, val)))
                result.setPixelColor(x, y, QColor(val, val, val, 255))
        
        return result


class TileReflectionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Tile Reflection")
        
        layout = QVBoxLayout()
        
        s_layout = QHBoxLayout()
        s_layout.addWidget(QLabel("Tile Size:"))
        self.s_spin = QSpinBox()
        self.s_spin.setRange(10, 100)
        self.s_spin.setValue(40)
        s_layout.addWidget(self.s_spin)
        layout.addLayout(s_layout)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
    
    def get_config(self):
        return {"tile_size": self.s_spin.value()}


class TileReflectionEffect(Effect):
    """Tile reflection effect."""
    name = "Tile Reflection"
    category = "Distort"
    
    def create_dialog(self, parent) -> QDialog:
        return TileReflectionDialog(parent)
    
    def apply(self, image: QImage, config: dict) -> QImage:
        tile_size = config.get("tile_size", 40)
        
        width = image.width()
        height = image.height()
        result = image.copy()
        
        for ty in range(0, height, tile_size):
            for tx in range(0, width, tile_size):
                # Alternate flip per tile
                flip_h = ((tx // tile_size) % 2) == 1
                flip_v = ((ty // tile_size) % 2) == 1
                
                for dy in range(tile_size):
                    for dx in range(tile_size):
                        x = tx + dx
                        y = ty + dy
                        
                        if x >= width or y >= height:
                            continue
                        
                        # Calculate source
                        sx = dx if not flip_h else (tile_size - 1 - dx)
                        sy = dy if not flip_v else (tile_size - 1 - dy)
                        
                        sx = tx + sx
                        sy = ty + sy
                        
                        if 0 <= sx < width and 0 <= sy < height:
                            result.setPixelColor(x, y, image.pixelColor(sx, sy))
        
        return result
