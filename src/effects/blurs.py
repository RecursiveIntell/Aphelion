"""
Blur and Sharpen effects for Aphelion.
"""
from PySide6.QtGui import QImage, QColor
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QSlider, QDialogButtonBox, QSpinBox, QComboBox
from PySide6.QtCore import Qt
from ..core.effects import Effect
import math


class GaussianBlurDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Gaussian Blur")
        
        layout = QVBoxLayout()
        
        # Radius
        r_layout = QHBoxLayout()
        r_layout.addWidget(QLabel("Radius:"))
        self.r_spin = QSpinBox()
        self.r_spin.setRange(1, 50)
        self.r_spin.setValue(3)
        r_layout.addWidget(self.r_spin)
        layout.addLayout(r_layout)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
    
    def get_config(self):
        return {"radius": self.r_spin.value()}


class GaussianBlurEffect(Effect):
    name = "Gaussian Blur"
    category = "Blurs"
    
    def create_dialog(self, parent) -> QDialog:
        return GaussianBlurDialog(parent)
    
    def apply(self, image: QImage, config: dict) -> QImage:
        radius = config.get("radius", 3)
        
        if radius <= 0:
            return image.copy()
        
        # Build Gaussian kernel
        kernel_size = radius * 2 + 1
        kernel = self._build_gaussian_kernel(radius)
        
        # Apply convolution
        return self._apply_convolution(image, kernel, kernel_size)
    
    def _build_gaussian_kernel(self, radius: int) -> list:
        """Build 1D Gaussian kernel (for separable convolution)."""
        sigma = radius / 3.0
        if sigma == 0:
            sigma = 1
        
        kernel_size = radius * 2 + 1
        kernel = []
        total = 0.0
        
        for i in range(kernel_size):
            x = i - radius
            val = math.exp(-(x * x) / (2 * sigma * sigma))
            kernel.append(val)
            total += val
        
        # Normalize
        kernel = [k / total for k in kernel]
        return kernel
    
    def _apply_convolution(self, image: QImage, kernel: list, kernel_size: int) -> QImage:
        """Apply separable Gaussian blur (horizontal then vertical pass)."""
        width = image.width()
        height = image.height()
        radius = kernel_size // 2
        
        # First pass: horizontal
        temp = image.copy()
        for y in range(height):
            for x in range(width):
                r_sum = g_sum = b_sum = a_sum = 0.0
                
                for k in range(kernel_size):
                    sx = x + k - radius
                    sx = max(0, min(width - 1, sx))
                    
                    c = image.pixelColor(sx, y)
                    weight = kernel[k]
                    r_sum += c.red() * weight
                    g_sum += c.green() * weight
                    b_sum += c.blue() * weight
                    a_sum += c.alpha() * weight
                
                temp.setPixelColor(x, y, QColor(
                    int(min(255, max(0, r_sum))),
                    int(min(255, max(0, g_sum))),
                    int(min(255, max(0, b_sum))),
                    int(min(255, max(0, a_sum)))
                ))
        
        # Second pass: vertical
        result = temp.copy()
        for y in range(height):
            for x in range(width):
                r_sum = g_sum = b_sum = a_sum = 0.0
                
                for k in range(kernel_size):
                    sy = y + k - radius
                    sy = max(0, min(height - 1, sy))
                    
                    c = temp.pixelColor(x, sy)
                    weight = kernel[k]
                    r_sum += c.red() * weight
                    g_sum += c.green() * weight
                    b_sum += c.blue() * weight
                    a_sum += c.alpha() * weight
                
                result.setPixelColor(x, y, QColor(
                    int(min(255, max(0, r_sum))),
                    int(min(255, max(0, g_sum))),
                    int(min(255, max(0, b_sum))),
                    int(min(255, max(0, a_sum)))
                ))
        
        return result


class SharpenDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Sharpen")
        
        layout = QVBoxLayout()
        
        # Amount
        a_layout = QHBoxLayout()
        a_layout.addWidget(QLabel("Amount:"))
        self.a_slider = QSlider(Qt.Orientation.Horizontal)
        self.a_slider.setRange(1, 100)
        self.a_slider.setValue(50)
        a_layout.addWidget(self.a_slider)
        self.a_val = QLabel("50")
        self.a_slider.valueChanged.connect(lambda v: self.a_val.setText(str(v)))
        a_layout.addWidget(self.a_val)
        layout.addLayout(a_layout)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
    
    def get_config(self):
        return {"amount": self.a_slider.value()}


class SharpenEffect(Effect):
    """Unsharp mask sharpening."""
    name = "Sharpen"
    category = "Blurs"
    
    def create_dialog(self, parent) -> QDialog:
        return SharpenDialog(parent)
    
    def apply(self, image: QImage, config: dict) -> QImage:
        amount = config.get("amount", 50) / 100.0
        
        # Unsharp mask: Original + (Original - Blurred) * amount
        blur_effect = GaussianBlurEffect()
        blurred = blur_effect.apply(image, {"radius": 1})
        
        result = image.copy()
        width = image.width()
        height = image.height()
        
        for y in range(height):
            for x in range(width):
                orig = image.pixelColor(x, y)
                blur = blurred.pixelColor(x, y)
                
                r = int(orig.red() + (orig.red() - blur.red()) * amount)
                g = int(orig.green() + (orig.green() - blur.green()) * amount)
                b = int(orig.blue() + (orig.blue() - blur.blue()) * amount)
                
                r = max(0, min(255, r))
                g = max(0, min(255, g))
                b = max(0, min(255, b))
                
                result.setPixelColor(x, y, QColor(r, g, b, orig.alpha()))
        
        return result


class MotionBlurDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Motion Blur")
        
        layout = QVBoxLayout()
        
        # Distance
        d_layout = QHBoxLayout()
        d_layout.addWidget(QLabel("Distance:"))
        self.d_spin = QSpinBox()
        self.d_spin.setRange(1, 50)
        self.d_spin.setValue(10)
        d_layout.addWidget(self.d_spin)
        layout.addLayout(d_layout)
        
        # Angle
        a_layout = QHBoxLayout()
        a_layout.addWidget(QLabel("Angle:"))
        self.a_spin = QSpinBox()
        self.a_spin.setRange(0, 360)
        self.a_spin.setValue(0)
        a_layout.addWidget(self.a_spin)
        layout.addLayout(a_layout)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
    
    def get_config(self):
        return {"distance": self.d_spin.value(), "angle": self.a_spin.value()}


class MotionBlurEffect(Effect):
    name = "Motion Blur"
    category = "Blurs"
    
    def create_dialog(self, parent) -> QDialog:
        return MotionBlurDialog(parent)
    
    def apply(self, image: QImage, config: dict) -> QImage:
        distance = config.get("distance", 10)
        angle = config.get("angle", 0)
        
        # Convert angle to radians
        rad = math.radians(angle)
        dx = math.cos(rad)
        dy = math.sin(rad)
        
        width = image.width()
        height = image.height()
        result = image.copy()
        
        for y in range(height):
            for x in range(width):
                r_sum = g_sum = b_sum = a_sum = 0.0
                count = 0
                
                for i in range(distance):
                    sx = int(x + dx * i)
                    sy = int(y + dy * i)
                    
                    if 0 <= sx < width and 0 <= sy < height:
                        c = image.pixelColor(sx, sy)
                        r_sum += c.red()
                        g_sum += c.green()
                        b_sum += c.blue()
                        a_sum += c.alpha()
                        count += 1
                
                if count > 0:
                    result.setPixelColor(x, y, QColor(
                        int(r_sum / count),
                        int(g_sum / count),
                        int(b_sum / count),
                        int(a_sum / count)
                    ))
        
        return result


class SepiaEffect(Effect):
    """Sepia tone effect."""
    name = "Sepia"
    category = "Adjustments"
    
    def apply(self, image: QImage, config: dict) -> QImage:
        result = image.copy()
        width = image.width()
        height = image.height()
        
        for y in range(height):
            for x in range(width):
                c = image.pixelColor(x, y)
                r, g, b = c.red(), c.green(), c.blue()
                
                # Sepia formula
                new_r = int(r * 0.393 + g * 0.769 + b * 0.189)
                new_g = int(r * 0.349 + g * 0.686 + b * 0.168)
                new_b = int(r * 0.272 + g * 0.534 + b * 0.131)
                
                new_r = min(255, new_r)
                new_g = min(255, new_g)
                new_b = min(255, new_b)
                
                result.setPixelColor(x, y, QColor(new_r, new_g, new_b, c.alpha()))
        
        return result


class MedianDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Median")
        
        layout = QVBoxLayout()
        
        r_layout = QHBoxLayout()
        r_layout.addWidget(QLabel("Radius:"))
        self.r_spin = QSpinBox()
        self.r_spin.setRange(1, 5)
        self.r_spin.setValue(1)
        r_layout.addWidget(self.r_spin)
        layout.addLayout(r_layout)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
    
    def get_config(self):
        return {"radius": self.r_spin.value()}


class MedianEffect(Effect):
    """Median filter for noise reduction."""
    name = "Median"
    category = "Blurs"
    
    def create_dialog(self, parent) -> QDialog:
        return MedianDialog(parent)
    
    def apply(self, image: QImage, config: dict) -> QImage:
        radius = config.get("radius", 1)
        
        width = image.width()
        height = image.height()
        result = image.copy()
        
        for y in range(radius, height - radius):
            for x in range(radius, width - radius):
                reds = []
                greens = []
                blues = []
                
                for dy in range(-radius, radius + 1):
                    for dx in range(-radius, radius + 1):
                        c = image.pixelColor(x + dx, y + dy)
                        reds.append(c.red())
                        greens.append(c.green())
                        blues.append(c.blue())
                
                reds.sort()
                greens.sort()
                blues.sort()
                
                mid = len(reds) // 2
                result.setPixelColor(x, y, QColor(
                    reds[mid],
                    greens[mid],
                    blues[mid],
                    image.pixelColor(x, y).alpha()
                ))
        
        return result
