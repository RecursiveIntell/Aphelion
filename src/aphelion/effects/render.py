"""
Render and stylize effects for Aphelion - NumPy optimized.
"""
from PySide6.QtGui import QImage, QColor
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QSlider, QDialogButtonBox, QSpinBox
from PySide6.QtCore import Qt
from ..core.effects import Effect
from ..utils.image_processing import qimage_to_numpy, numpy_to_qimage
import numpy as np
from scipy.ndimage import uniform_filter, sobel


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
    """Soft glow effect - NumPy optimized."""
    name = "Glow"
    category = "Photo"
    
    def create_dialog(self, parent) -> QDialog:
        return GlowDialog(parent)
    
    def apply(self, image: QImage, config: dict) -> QImage:
        radius = config.get("radius", 5)
        brightness = config.get("brightness", 50) / 100.0
        
        arr = qimage_to_numpy(image).astype(np.float32)
        
        # Compute luminance for weighting
        lum = (arr[:, :, 0] + arr[:, :, 1] + arr[:, :, 2]) / (3 * 255.0)
        
        # Create glow (weighted blur of bright areas)
        kernel_size = 2 * radius + 1
        glow = np.zeros_like(arr, dtype=np.float32)
        
        for c in range(3):
            weighted = arr[:, :, c] * lum
            weighted_blur = uniform_filter(weighted, size=kernel_size, mode='reflect')
            glow[:, :, c] = weighted_blur * 2
        
        glow = np.clip(glow, 0, 255)
        
        # Screen blend: 1 - (1-a)*(1-b)
        orig = arr / 255.0
        g = glow / 255.0 * brightness
        result = 1 - (1 - orig) * (1 - g)
        result = np.clip(result * 255, 0, 255).astype(np.uint8)
        
        return numpy_to_qimage(result)


class OutlineEffect(Effect):
    """Draw outline around edges - NumPy optimized."""
    name = "Outline"
    category = "Stylize"
    
    def apply(self, image: QImage, config: dict) -> QImage:
        arr = qimage_to_numpy(image)
        
        # Convert to grayscale
        gray = (arr[:, :, 0].astype(np.float32) + 
                arr[:, :, 1].astype(np.float32) + 
                arr[:, :, 2].astype(np.float32)) / 3.0
        
        # Sobel edge detection
        gx = sobel(gray, axis=1)
        gy = sobel(gray, axis=0)
        magnitude = np.sqrt(gx**2 + gy**2)
        magnitude = np.clip(magnitude, 0, 255)
        
        # Invert for outline (dark on white)
        val = (255 - magnitude).astype(np.uint8)
        
        result = arr.copy()
        result[:, :, 0] = val
        result[:, :, 1] = val
        result[:, :, 2] = val
        
        return numpy_to_qimage(result)


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
    """Fragment effect - NumPy optimized."""
    name = "Fragment"
    category = "Stylize"
    
    def create_dialog(self, parent) -> QDialog:
        return FragmentDialog(parent)
    
    def apply(self, image: QImage, config: dict) -> QImage:
        count = config.get("count", 4)
        distance = config.get("distance", 5)
        
        arr = qimage_to_numpy(image).astype(np.float32)
        height, width = arr.shape[:2]
        
        result = np.zeros_like(arr, dtype=np.float32)
        
        # Create coordinate grids
        yy, xx = np.mgrid[0:height, 0:width]
        
        for i in range(count):
            angle = (i / count) * 2 * np.pi
            dx = int(distance * np.cos(angle))
            dy = int(distance * np.sin(angle))
            
            # Shift coordinates
            sx = np.clip(xx + dx, 0, width - 1)
            sy = np.clip(yy + dy, 0, height - 1)
            
            # Sample from shifted positions
            result += arr[sy, sx]
        
        result = np.clip(result / count, 0, 255).astype(np.uint8)
        return numpy_to_qimage(result)


class CloudsEffect(Effect):
    """Render clouds using fractal noise - NumPy optimized."""
    name = "Clouds"
    category = "Render"
    
    def apply(self, image: QImage, config: dict) -> QImage:
        arr = qimage_to_numpy(image)
        height, width = arr.shape[:2]
        
        # Create coordinate grids
        yy, xx = np.mgrid[0:height, 0:width]
        
        # Fractal noise
        val = np.zeros((height, width), dtype=np.float32)
        scale = 64
        amp = 128
        
        for _ in range(4):
            noise = ((xx * 13 + yy * 7 + scale * 5) % 256).astype(np.float32) / 256.0
            val += noise * amp
            scale //= 2
            amp //= 2
        
        val = np.clip(val, 0, 255).astype(np.uint8)
        
        result = arr.copy()
        result[:, :, 0] = val
        result[:, :, 1] = val
        result[:, :, 2] = val
        result[:, :, 3] = 255
        
        return numpy_to_qimage(result)


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
    """Tile reflection effect - NumPy optimized."""
    name = "Tile Reflection"
    category = "Distort"
    
    def create_dialog(self, parent) -> QDialog:
        return TileReflectionDialog(parent)
    
    def apply(self, image: QImage, config: dict) -> QImage:
        tile_size = config.get("tile_size", 40)
        
        arr = qimage_to_numpy(image)
        height, width = arr.shape[:2]
        
        # Create coordinate grids
        yy, xx = np.mgrid[0:height, 0:width]
        
        # Tile coordinates
        tx = xx // tile_size
        ty = yy // tile_size
        
        # Position within tile
        dx = xx % tile_size
        dy = yy % tile_size
        
        # Flip mask (alternating tiles)
        flip_h = (tx % 2) == 1
        flip_v = (ty % 2) == 1
        
        # Apply flipping
        sx = np.where(flip_h, (tile_size - 1 - dx), dx) + tx * tile_size
        sy = np.where(flip_v, (tile_size - 1 - dy), dy) + ty * tile_size
        
        # Clamp to bounds
        sx = np.clip(sx, 0, width - 1)
        sy = np.clip(sy, 0, height - 1)
        
        result = arr[sy, sx]
        return numpy_to_qimage(result)


class JuliaFractalDialog(QDialog):
    """Dialog for Julia Fractal effect."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Julia Fractal")
        layout = QVBoxLayout()
        
        # Quality (iterations)
        q_layout = QHBoxLayout()
        q_layout.addWidget(QLabel("Quality:"))
        self.q_spin = QSpinBox()
        self.q_spin.setRange(10, 500)
        self.q_spin.setValue(100)
        q_layout.addWidget(self.q_spin)
        layout.addLayout(q_layout)
        
        # Zoom
        z_layout = QHBoxLayout()
        z_layout.addWidget(QLabel("Zoom:"))
        self.z_slider = QSlider(Qt.Orientation.Horizontal)
        self.z_slider.setRange(1, 100)
        self.z_slider.setValue(30)
        z_layout.addWidget(self.z_slider)
        layout.addLayout(z_layout)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
    
    def get_config(self):
        return {"quality": self.q_spin.value(), "zoom": self.z_slider.value() / 10.0}


class JuliaFractalEffect(Effect):
    """Generate Julia set fractal."""
    name = "Julia Fractal"
    category = "Render"
    
    def create_dialog(self, parent) -> QDialog:
        return JuliaFractalDialog(parent)
    
    def apply(self, image: QImage, config: dict) -> QImage:
        max_iter = config.get("quality", 100)
        zoom = config.get("zoom", 3.0)
        
        arr = qimage_to_numpy(image)
        height, width = arr.shape[:2]
        
        # Julia set constant (for a nice pattern)
        c_real, c_imag = -0.7, 0.27015
        
        # Create coordinate grid
        x = np.linspace(-zoom, zoom, width)
        y = np.linspace(-zoom, zoom, height)
        X, Y = np.meshgrid(x, y)
        Z = X + 1j * Y
        
        # Iteration count array
        iterations = np.zeros((height, width), dtype=np.int32)
        mask = np.ones((height, width), dtype=bool)
        
        for i in range(max_iter):
            Z[mask] = Z[mask] ** 2 + complex(c_real, c_imag)
            escaped = np.abs(Z) > 2
            iterations[mask & escaped] = i
            mask = mask & ~escaped
        
        # Colorize based on iteration count
        normalized = iterations / max_iter
        
        result = arr.copy()
        result[:, :, 0] = (np.sin(normalized * 5) * 127 + 128).astype(np.uint8)
        result[:, :, 1] = (np.sin(normalized * 7 + 2) * 127 + 128).astype(np.uint8)
        result[:, :, 2] = (np.sin(normalized * 11 + 4) * 127 + 128).astype(np.uint8)
        result[:, :, 3] = 255
        
        return numpy_to_qimage(result)


class MandelbrotFractalDialog(QDialog):
    """Dialog for Mandelbrot Fractal effect."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Mandelbrot Fractal")
        layout = QVBoxLayout()
        
        # Quality
        q_layout = QHBoxLayout()
        q_layout.addWidget(QLabel("Quality:"))
        self.q_spin = QSpinBox()
        self.q_spin.setRange(10, 500)
        self.q_spin.setValue(100)
        q_layout.addWidget(self.q_spin)
        layout.addLayout(q_layout)
        
        # Zoom
        z_layout = QHBoxLayout()
        z_layout.addWidget(QLabel("Zoom:"))
        self.z_slider = QSlider(Qt.Orientation.Horizontal)
        self.z_slider.setRange(1, 100)
        self.z_slider.setValue(25)
        z_layout.addWidget(self.z_slider)
        layout.addLayout(z_layout)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
    
    def get_config(self):
        return {"quality": self.q_spin.value(), "zoom": self.z_slider.value() / 10.0}


class MandelbrotFractalEffect(Effect):
    """Generate Mandelbrot set fractal."""
    name = "Mandelbrot Fractal"
    category = "Render"
    
    def create_dialog(self, parent) -> QDialog:
        return MandelbrotFractalDialog(parent)
    
    def apply(self, image: QImage, config: dict) -> QImage:
        max_iter = config.get("quality", 100)
        zoom = config.get("zoom", 2.5)
        
        arr = qimage_to_numpy(image)
        height, width = arr.shape[:2]
        
        # Center on the interesting part of Mandelbrot set
        x_center, y_center = -0.5, 0
        
        x = np.linspace(x_center - zoom, x_center + zoom, width)
        y = np.linspace(y_center - zoom, y_center + zoom, height)
        X, Y = np.meshgrid(x, y)
        C = X + 1j * Y
        Z = np.zeros_like(C)
        
        iterations = np.zeros((height, width), dtype=np.int32)
        mask = np.ones((height, width), dtype=bool)
        
        for i in range(max_iter):
            Z[mask] = Z[mask] ** 2 + C[mask]
            escaped = np.abs(Z) > 2
            iterations[mask & escaped] = i
            mask = mask & ~escaped
        
        # Colorize
        normalized = iterations / max_iter
        
        result = arr.copy()
        result[:, :, 0] = (np.sin(normalized * 3.14 * 2) * 127 + 128).astype(np.uint8)
        result[:, :, 1] = (np.sin(normalized * 3.14 * 4 + 1) * 127 + 128).astype(np.uint8)
        result[:, :, 2] = (np.sin(normalized * 3.14 * 8 + 2) * 127 + 128).astype(np.uint8)
        result[:, :, 3] = 255
        
        return numpy_to_qimage(result)
