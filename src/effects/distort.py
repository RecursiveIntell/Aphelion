"""
Distortion and stylize effects for Aphelion.
"""
from PySide6.QtGui import QImage, QColor
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QSlider, QDialogButtonBox, QSpinBox
from PySide6.QtCore import Qt
from ..core.effects import Effect
import math
import random


class PixelateDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Pixelate")
        
        layout = QVBoxLayout()
        
        # Cell size
        s_layout = QHBoxLayout()
        s_layout.addWidget(QLabel("Cell Size:"))
        self.s_spin = QSpinBox()
        self.s_spin.setRange(2, 100)
        self.s_spin.setValue(8)
        s_layout.addWidget(self.s_spin)
        layout.addLayout(s_layout)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
    
    def get_config(self):
        return {"cell_size": self.s_spin.value()}


class PixelateEffect(Effect):
    name = "Pixelate"
    category = "Distort"
    
    def create_dialog(self, parent) -> QDialog:
        return PixelateDialog(parent)
    
    def apply(self, image: QImage, config: dict) -> QImage:
        cell_size = config.get("cell_size", 8)
        
        width = image.width()
        height = image.height()
        result = image.copy()
        
        for cy in range(0, height, cell_size):
            for cx in range(0, width, cell_size):
                # Average color in cell
                r_sum = g_sum = b_sum = a_sum = 0
                count = 0
                
                for dy in range(cell_size):
                    for dx in range(cell_size):
                        x = cx + dx
                        y = cy + dy
                        if x < width and y < height:
                            c = image.pixelColor(x, y)
                            r_sum += c.red()
                            g_sum += c.green()
                            b_sum += c.blue()
                            a_sum += c.alpha()
                            count += 1
                
                if count > 0:
                    avg_color = QColor(
                        r_sum // count,
                        g_sum // count,
                        b_sum // count,
                        a_sum // count
                    )
                    
                    # Fill cell with average
                    for dy in range(cell_size):
                        for dx in range(cell_size):
                            x = cx + dx
                            y = cy + dy
                            if x < width and y < height:
                                result.setPixelColor(x, y, avg_color)
        
        return result


class EmbossEffect(Effect):
    """Emboss effect using convolution kernel."""
    name = "Emboss"
    category = "Stylize"
    
    def apply(self, image: QImage, config: dict) -> QImage:
        # Emboss kernel
        kernel = [
            [-2, -1, 0],
            [-1,  1, 1],
            [ 0,  1, 2]
        ]
        
        width = image.width()
        height = image.height()
        result = image.copy()
        
        for y in range(1, height - 1):
            for x in range(1, width - 1):
                r_sum = g_sum = b_sum = 0
                
                for ky in range(3):
                    for kx in range(3):
                        px = x + kx - 1
                        py = y + ky - 1
                        c = image.pixelColor(px, py)
                        weight = kernel[ky][kx]
                        
                        r_sum += c.red() * weight
                        g_sum += c.green() * weight
                        b_sum += c.blue() * weight
                
                # Add 128 to shift to middle gray
                r = max(0, min(255, r_sum + 128))
                g = max(0, min(255, g_sum + 128))
                b = max(0, min(255, b_sum + 128))
                
                result.setPixelColor(x, y, QColor(r, g, b, image.pixelColor(x, y).alpha()))
        
        return result


class EdgeDetectEffect(Effect):
    """Edge detection using Sobel operator."""
    name = "Edge Detect"
    category = "Stylize"
    
    def apply(self, image: QImage, config: dict) -> QImage:
        # Sobel kernels
        gx = [[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]]
        gy = [[-1, -2, -1], [0, 0, 0], [1, 2, 1]]
        
        width = image.width()
        height = image.height()
        result = image.copy()
        
        for y in range(1, height - 1):
            for x in range(1, width - 1):
                rx, ry = 0, 0
                
                for ky in range(3):
                    for kx in range(3):
                        px = x + kx - 1
                        py = y + ky - 1
                        c = image.pixelColor(px, py)
                        gray = (c.red() + c.green() + c.blue()) // 3
                        
                        rx += gray * gx[ky][kx]
                        ry += gray * gy[ky][kx]
                
                magnitude = int(min(255, math.sqrt(rx*rx + ry*ry)))
                result.setPixelColor(x, y, QColor(magnitude, magnitude, magnitude, image.pixelColor(x, y).alpha()))
        
        return result


class AddNoiseDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Noise")
        
        layout = QVBoxLayout()
        
        # Intensity
        i_layout = QHBoxLayout()
        i_layout.addWidget(QLabel("Intensity:"))
        self.i_slider = QSlider(Qt.Orientation.Horizontal)
        self.i_slider.setRange(1, 100)
        self.i_slider.setValue(25)
        i_layout.addWidget(self.i_slider)
        self.i_val = QLabel("25")
        self.i_slider.valueChanged.connect(lambda v: self.i_val.setText(str(v)))
        i_layout.addWidget(self.i_val)
        layout.addLayout(i_layout)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
    
    def get_config(self):
        return {"intensity": self.i_slider.value()}


class AddNoiseEffect(Effect):
    name = "Add Noise"
    category = "Noise"
    
    def create_dialog(self, parent) -> QDialog:
        return AddNoiseDialog(parent)
    
    def apply(self, image: QImage, config: dict) -> QImage:
        intensity = config.get("intensity", 25)
        
        width = image.width()
        height = image.height()
        result = image.copy()
        
        for y in range(height):
            for x in range(width):
                c = image.pixelColor(x, y)
                noise = random.randint(-intensity, intensity)
                
                r = max(0, min(255, c.red() + noise))
                g = max(0, min(255, c.green() + noise))
                b = max(0, min(255, c.blue() + noise))
                
                result.setPixelColor(x, y, QColor(r, g, b, c.alpha()))
        
        return result


class ReduceNoiseEffect(Effect):
    """Simple median filter for noise reduction."""
    name = "Reduce Noise"
    category = "Noise"
    
    def apply(self, image: QImage, config: dict) -> QImage:
        width = image.width()
        height = image.height()
        result = image.copy()
        
        for y in range(1, height - 1):
            for x in range(1, width - 1):
                r_vals = []
                g_vals = []
                b_vals = []
                
                # 3x3 neighborhood
                for dy in range(-1, 2):
                    for dx in range(-1, 2):
                        c = image.pixelColor(x + dx, y + dy)
                        r_vals.append(c.red())
                        g_vals.append(c.green())
                        b_vals.append(c.blue())
                
                # Median
                r_vals.sort()
                g_vals.sort()
                b_vals.sort()
                
                result.setPixelColor(x, y, QColor(
                    r_vals[4], g_vals[4], b_vals[4],
                    image.pixelColor(x, y).alpha()
                ))
        
        return result


class RadialBlurDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Radial Blur")
        
        layout = QVBoxLayout()
        
        a_layout = QHBoxLayout()
        a_layout.addWidget(QLabel("Amount:"))
        self.a_slider = QSlider(Qt.Orientation.Horizontal)
        self.a_slider.setRange(1, 50)
        self.a_slider.setValue(10)
        a_layout.addWidget(self.a_slider)
        layout.addLayout(a_layout)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
    
    def get_config(self):
        return {"amount": self.a_slider.value()}


class RadialBlurEffect(Effect):
    """Radial/spin blur from center."""
    name = "Radial Blur"
    category = "Blurs"
    
    def create_dialog(self, parent) -> QDialog:
        return RadialBlurDialog(parent)
    
    def apply(self, image: QImage, config: dict) -> QImage:
        amount = config.get("amount", 10)
        
        width = image.width()
        height = image.height()
        result = image.copy()
        
        cx = width // 2
        cy = height // 2
        
        for y in range(height):
            for x in range(width):
                r_sum = g_sum = b_sum = a_sum = 0.0
                
                for i in range(amount):
                    angle = (i / amount) * 0.05  # Small rotation
                    cos_a = math.cos(angle)
                    sin_a = math.sin(angle)
                    
                    # Rotate around center
                    dx = x - cx
                    dy = y - cy
                    sx = int(cx + dx * cos_a - dy * sin_a)
                    sy = int(cy + dx * sin_a + dy * cos_a)
                    
                    if 0 <= sx < width and 0 <= sy < height:
                        c = image.pixelColor(sx, sy)
                        r_sum += c.red()
                        g_sum += c.green()
                        b_sum += c.blue()
                        a_sum += c.alpha()
                
                result.setPixelColor(x, y, QColor(
                    int(r_sum / amount),
                    int(g_sum / amount),
                    int(b_sum / amount),
                    int(a_sum / amount)
                ))
        
        return result


class ZoomBlurDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Zoom Blur")
        
        layout = QVBoxLayout()
        
        a_layout = QHBoxLayout()
        a_layout.addWidget(QLabel("Amount:"))
        self.a_slider = QSlider(Qt.Orientation.Horizontal)
        self.a_slider.setRange(1, 100)
        self.a_slider.setValue(20)
        a_layout.addWidget(self.a_slider)
        layout.addLayout(a_layout)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
    
    def get_config(self):
        return {"amount": self.a_slider.value()}


class ZoomBlurEffect(Effect):
    """Zoom blur - radial blur that zooms from center."""
    name = "Zoom Blur"
    category = "Blurs"
    
    def create_dialog(self, parent) -> QDialog:
        return ZoomBlurDialog(parent)
    
    def apply(self, image: QImage, config: dict) -> QImage:
        amount = config.get("amount", 20)
        
        width = image.width()
        height = image.height()
        result = image.copy()
        
        cx = width // 2
        cy = height // 2
        
        samples = max(2, amount // 5)
        
        for y in range(height):
            for x in range(width):
                r_sum = g_sum = b_sum = a_sum = 0
                
                for i in range(samples):
                    # Scale factor from center
                    scale = 1.0 - (i / samples) * (amount / 100.0)
                    
                    sx = int(cx + (x - cx) * scale)
                    sy = int(cy + (y - cy) * scale)
                    
                    sx = max(0, min(width - 1, sx))
                    sy = max(0, min(height - 1, sy))
                    
                    c = image.pixelColor(sx, sy)
                    r_sum += c.red()
                    g_sum += c.green()
                    b_sum += c.blue()
                    a_sum += c.alpha()
                
                result.setPixelColor(x, y, QColor(
                    r_sum // samples,
                    g_sum // samples,
                    b_sum // samples,
                    a_sum // samples
                ))
        
        return result


class BulgeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Bulge")
        
        layout = QVBoxLayout()
        
        a_layout = QHBoxLayout()
        a_layout.addWidget(QLabel("Amount:"))
        self.a_slider = QSlider(Qt.Orientation.Horizontal)
        self.a_slider.setRange(-100, 100)
        self.a_slider.setValue(50)
        a_layout.addWidget(self.a_slider)
        layout.addLayout(a_layout)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
    
    def get_config(self):
        return {"amount": self.a_slider.value()}


class BulgeEffect(Effect):
    """Bulge/Pinch distortion from center."""
    name = "Bulge"
    category = "Distort"
    
    def create_dialog(self, parent) -> QDialog:
        return BulgeDialog(parent)
    
    def apply(self, image: QImage, config: dict) -> QImage:
        amount = config.get("amount", 50) / 100.0
        
        width = image.width()
        height = image.height()
        result = image.copy()
        
        cx = width / 2
        cy = height / 2
        radius = min(cx, cy)
        
        for y in range(height):
            for x in range(width):
                dx = x - cx
                dy = y - cy
                dist = math.sqrt(dx*dx + dy*dy)
                
                if dist < radius and dist > 0:
                    # Bulge formula
                    factor = (1 - (dist / radius)) * amount
                    new_dist = dist * (1 - factor)
                    
                    sx = int(cx + dx * (new_dist / dist))
                    sy = int(cy + dy * (new_dist / dist))
                    
                    sx = max(0, min(width - 1, sx))
                    sy = max(0, min(height - 1, sy))
                    
                    result.setPixelColor(x, y, image.pixelColor(sx, sy))
        
        return result


class TwistDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Twist")
        
        layout = QVBoxLayout()
        
        a_layout = QHBoxLayout()
        a_layout.addWidget(QLabel("Angle:"))
        self.a_slider = QSlider(Qt.Orientation.Horizontal)
        self.a_slider.setRange(-180, 180)
        self.a_slider.setValue(45)
        a_layout.addWidget(self.a_slider)
        layout.addLayout(a_layout)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
    
    def get_config(self):
        return {"angle": self.a_slider.value()}


class TwistEffect(Effect):
    """Twist/Swirl distortion from center."""
    name = "Twist"
    category = "Distort"
    
    def create_dialog(self, parent) -> QDialog:
        return TwistDialog(parent)
    
    def apply(self, image: QImage, config: dict) -> QImage:
        angle = math.radians(config.get("angle", 45))
        
        width = image.width()
        height = image.height()
        result = image.copy()
        
        cx = width / 2
        cy = height / 2
        radius = min(cx, cy)
        
        for y in range(height):
            for x in range(width):
                dx = x - cx
                dy = y - cy
                dist = math.sqrt(dx*dx + dy*dy)
                
                if dist < radius:
                    # Twist amount decreases with distance from center
                    twist = angle * (1 - dist / radius)
                    
                    cos_t = math.cos(twist)
                    sin_t = math.sin(twist)
                    
                    sx = int(cx + dx * cos_t - dy * sin_t)
                    sy = int(cy + dx * sin_t + dy * cos_t)
                    
                    sx = max(0, min(width - 1, sx))
                    sy = max(0, min(height - 1, sy))
                    
                    result.setPixelColor(x, y, image.pixelColor(sx, sy))
        
        return result


class DentsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Dents")
        
        layout = QVBoxLayout()
        
        a_layout = QHBoxLayout()
        a_layout.addWidget(QLabel("Amount:"))
        self.a_slider = QSlider(Qt.Orientation.Horizontal)
        self.a_slider.setRange(1, 50)
        self.a_slider.setValue(10)
        a_layout.addWidget(self.a_slider)
        layout.addLayout(a_layout)
        
        s_layout = QHBoxLayout()
        s_layout.addWidget(QLabel("Scale:"))
        self.s_spin = QSpinBox()
        self.s_spin.setRange(5, 50)
        self.s_spin.setValue(20)
        s_layout.addWidget(self.s_spin)
        layout.addLayout(s_layout)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
    
    def get_config(self):
        return {"amount": self.a_slider.value(), "scale": self.s_spin.value()}


class DentsEffect(Effect):
    """Dents - random displacement distortion."""
    name = "Dents"
    category = "Distort"
    
    def create_dialog(self, parent) -> QDialog:
        return DentsDialog(parent)
    
    def apply(self, image: QImage, config: dict) -> QImage:
        amount = config.get("amount", 10)
        scale = config.get("scale", 20)
        
        width = image.width()
        height = image.height()
        result = image.copy()
        
        # Generate displacement map using simple noise
        random.seed(42)  # Reproducible results
        
        for y in range(height):
            for x in range(width):
                # Use sine waves for smooth dents
                dx = int(amount * math.sin(y / scale * 2 * math.pi))
                dy = int(amount * math.sin(x / scale * 2 * math.pi))
                
                sx = x + dx
                sy = y + dy
                
                sx = max(0, min(width - 1, sx))
                sy = max(0, min(height - 1, sy))
                
                result.setPixelColor(x, y, image.pixelColor(sx, sy))
        
        return result


class Rotate3DDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("3D Rotate / Zoom")
        layout = QVBoxLayout()
        
        # Rotation X
        rx_layout = QHBoxLayout()
        rx_layout.addWidget(QLabel("Rotate X:"))
        self.rx_slider = QSlider(Qt.Orientation.Horizontal)
        self.rx_slider.setRange(-60, 60)
        self.rx_slider.setValue(0)
        rx_layout.addWidget(self.rx_slider)
        self.rx_val = QLabel("0°")
        self.rx_slider.valueChanged.connect(lambda v: self.rx_val.setText(f"{v}°"))
        rx_layout.addWidget(self.rx_val)
        layout.addLayout(rx_layout)
        
        # Rotation Y
        ry_layout = QHBoxLayout()
        ry_layout.addWidget(QLabel("Rotate Y:"))
        self.ry_slider = QSlider(Qt.Orientation.Horizontal)
        self.ry_slider.setRange(-60, 60)
        self.ry_slider.setValue(0)
        ry_layout.addWidget(self.ry_slider)
        self.ry_val = QLabel("0°")
        self.ry_slider.valueChanged.connect(lambda v: self.ry_val.setText(f"{v}°"))
        ry_layout.addWidget(self.ry_val)
        layout.addLayout(ry_layout)
        
        # Zoom
        z_layout = QHBoxLayout()
        z_layout.addWidget(QLabel("Zoom:"))
        self.z_slider = QSlider(Qt.Orientation.Horizontal)
        self.z_slider.setRange(50, 200)
        self.z_slider.setValue(100)
        z_layout.addWidget(self.z_slider)
        self.z_val = QLabel("100%")
        self.z_slider.valueChanged.connect(lambda v: self.z_val.setText(f"{v}%"))
        z_layout.addWidget(self.z_val)
        layout.addLayout(z_layout)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.setLayout(layout)
        
    def get_config(self):
        return {
            "rotate_x": self.rx_slider.value(),
            "rotate_y": self.ry_slider.value(),
            "zoom": self.z_slider.value()
        }


class Rotate3DEffect(Effect):
    """3D Rotate / Zoom perspective transformation."""
    name = "3D Rotate / Zoom"
    category = "Distort"
    
    def create_dialog(self, parent) -> QDialog:
        return Rotate3DDialog(parent)
    
    def apply(self, image: QImage, config: dict) -> QImage:
        rotate_x = config.get("rotate_x", 0)
        rotate_y = config.get("rotate_y", 0)
        zoom = config.get("zoom", 100) / 100.0
        
        width = image.width()
        height = image.height()
        cx, cy = width / 2, height / 2
        
        result = QImage(width, height, QImage.Format.Format_ARGB32_Premultiplied)
        result.fill(QColor(0, 0, 0, 0))
        
        # Convert angles to radians
        ax = math.radians(rotate_x)
        ay = math.radians(rotate_y)
        
        # Distance from camera (affects perspective strength)
        focal_length = max(width, height) * 2
        
        for y in range(height):
            for x in range(width):
                # Normalize to center
                nx = (x - cx) / zoom
                ny = (y - cy) / zoom
                nz = 0
                
                # Rotate around X axis
                y1 = ny * math.cos(ax) - nz * math.sin(ax)
                z1 = ny * math.sin(ax) + nz * math.cos(ax)
                
                # Rotate around Y axis
                x2 = nx * math.cos(ay) + z1 * math.sin(ay)
                z2 = -nx * math.sin(ay) + z1 * math.cos(ay)
                
                # Perspective projection
                if focal_length + z2 > 0:
                    scale = focal_length / (focal_length + z2)
                    sx = x2 * scale + cx
                    sy = y1 * scale + cy
                    
                    # Sample from source
                    if 0 <= sx < width and 0 <= sy < height:
                        sx_int = int(sx)
                        sy_int = int(sy)
                        result.setPixelColor(x, y, image.pixelColor(sx_int, sy_int))
        
        return result


class PolarInversionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Polar Inversion")
        layout = QVBoxLayout()
        
        # Amount
        a_layout = QHBoxLayout()
        a_layout.addWidget(QLabel("Amount:"))
        self.a_slider = QSlider(Qt.Orientation.Horizontal)
        self.a_slider.setRange(-100, 100)
        self.a_slider.setValue(100)
        a_layout.addWidget(self.a_slider)
        self.a_val = QLabel("100")
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


class PolarInversionEffect(Effect):
    """Convert between rectangular and polar coordinates."""
    name = "Polar Inversion"
    category = "Distort"
    
    def create_dialog(self, parent) -> QDialog:
        return PolarInversionDialog(parent)
    
    def apply(self, image: QImage, config: dict) -> QImage:
        amount = config.get("amount", 100) / 100.0
        
        width = image.width()
        height = image.height()
        cx, cy = width / 2, height / 2
        max_radius = math.sqrt(cx * cx + cy * cy)
        
        result = QImage(width, height, QImage.Format.Format_ARGB32_Premultiplied)
        result.fill(QColor(0, 0, 0, 0))
        
        for y in range(height):
            for x in range(width):
                # Convert to polar
                dx = x - cx
                dy = y - cy
                r = math.sqrt(dx * dx + dy * dy)
                theta = math.atan2(dy, dx)
                
                if amount > 0:
                    # Polar to rectangular
                    # Map theta to x, radius to y
                    sx = ((theta + math.pi) / (2 * math.pi)) * width
                    sy = (r / max_radius) * height
                else:
                    # Rectangular to polar
                    norm_x = x / width
                    norm_y = y / height
                    new_theta = norm_x * 2 * math.pi - math.pi
                    new_r = norm_y * max_radius
                    sx = cx + new_r * math.cos(new_theta)
                    sy = cy + new_r * math.sin(new_theta)
                
                # Blend based on amount
                blend = abs(amount)
                fx = x * (1 - blend) + sx * blend
                fy = y * (1 - blend) + sy * blend
                
                fx = int(max(0, min(width - 1, fx)))
                fy = int(max(0, min(height - 1, fy)))
                
                result.setPixelColor(x, y, image.pixelColor(fx, fy))
        
        return result
