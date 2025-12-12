"""
Distortion and stylize effects for Aphelion.

Optimized with NumPy for high-performance coordinate mapping.
"""
from PySide6.QtGui import QImage, QColor
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QSlider, QDialogButtonBox, QSpinBox
from PySide6.QtCore import Qt
from ..core.effects import Effect
from ..utils.image_processing import qimage_to_numpy, numpy_to_qimage
import numpy as np
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
        
        arr = qimage_to_numpy(image)
        height, width = arr.shape[:2]
        
        # Downsample then upsample for pixelation effect
        small_h = max(1, height // cell_size)
        small_w = max(1, width // cell_size)
        
        # Average each cell
        result = arr.copy()
        for cy in range(0, height, cell_size):
            for cx in range(0, width, cell_size):
                cell = arr[cy:min(cy+cell_size, height), cx:min(cx+cell_size, width)]
                avg_color = cell.mean(axis=(0, 1)).astype(np.uint8)
                result[cy:min(cy+cell_size, height), cx:min(cx+cell_size, width)] = avg_color
        
        return numpy_to_qimage(result)


class EmbossEffect(Effect):
    """Emboss effect using convolution kernel."""
    name = "Emboss"
    category = "Stylize"
    
    def apply(self, image: QImage, config: dict) -> QImage:
        arr = qimage_to_numpy(image)
        
        # Emboss kernel
        kernel = np.array([[-2, -1, 0], [-1, 1, 1], [0, 1, 2]], dtype=np.float32)
        
        result = arr.copy().astype(np.float32)
        
        # Apply convolution to RGB channels
        for c in range(3):
            channel = arr[:, :, c].astype(np.float32)
            padded = np.pad(channel, 1, mode='edge')
            
            conv_result = np.zeros_like(channel)
            for ky in range(3):
                for kx in range(3):
                    conv_result += padded[ky:ky+channel.shape[0], kx:kx+channel.shape[1]] * kernel[ky, kx]
            
            result[:, :, c] = conv_result + 128
        
        result = np.clip(result, 0, 255).astype(np.uint8)
        return numpy_to_qimage(result)


class EdgeDetectEffect(Effect):
    """Edge detection using Sobel operator."""
    name = "Edge Detect"
    category = "Stylize"
    
    def apply(self, image: QImage, config: dict) -> QImage:
        arr = qimage_to_numpy(image)
        
        # Convert to grayscale
        gray = (arr[:, :, 0].astype(np.float32) + 
                arr[:, :, 1].astype(np.float32) + 
                arr[:, :, 2].astype(np.float32)) / 3
        
        # Sobel kernels
        gx = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]], dtype=np.float32)
        gy = np.array([[-1, -2, -1], [0, 0, 0], [1, 2, 1]], dtype=np.float32)
        
        padded = np.pad(gray, 1, mode='edge')
        
        grad_x = np.zeros_like(gray)
        grad_y = np.zeros_like(gray)
        
        for ky in range(3):
            for kx in range(3):
                shifted = padded[ky:ky+gray.shape[0], kx:kx+gray.shape[1]]
                grad_x += shifted * gx[ky, kx]
                grad_y += shifted * gy[ky, kx]
        
        magnitude = np.sqrt(grad_x**2 + grad_y**2)
        magnitude = np.clip(magnitude, 0, 255).astype(np.uint8)
        
        # Create grayscale output
        result = arr.copy()
        result[:, :, 0] = magnitude
        result[:, :, 1] = magnitude
        result[:, :, 2] = magnitude
        
        return numpy_to_qimage(result)


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
        
        arr = qimage_to_numpy(image)
        height, width = arr.shape[:2]
        
        # Generate noise
        noise = np.random.randint(-intensity, intensity + 1, (height, width, 3), dtype=np.int16)
        
        result = arr.astype(np.int16)
        result[:, :, :3] += noise
        result = np.clip(result, 0, 255).astype(np.uint8)
        
        return numpy_to_qimage(result)


class ReduceNoiseEffect(Effect):
    """Simple median filter for noise reduction."""
    name = "Reduce Noise"
    category = "Noise"
    
    def apply(self, image: QImage, config: dict) -> QImage:
        arr = qimage_to_numpy(image)
        height, width = arr.shape[:2]
        result = arr.copy()
        
        # 3x3 median filter
        radius = 1
        window_size = 3
        
        for c in range(3):
            padded = np.pad(arr[:, :, c], radius, mode='edge')
            neighborhoods = np.lib.stride_tricks.sliding_window_view(
                padded, (window_size, window_size)
            )
            result[:, :, c] = np.median(
                neighborhoods.reshape(height, width, -1), 
                axis=2
            ).astype(np.uint8)
        
        return numpy_to_qimage(result)


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
        
        arr = qimage_to_numpy(image)
        height, width = arr.shape[:2]
        
        cx, cy = width / 2, height / 2
        
        # Create coordinate grids
        y_coords, x_coords = np.mgrid[0:height, 0:width].astype(np.float32)
        
        result = np.zeros_like(arr, dtype=np.float32)
        
        for i in range(amount):
            angle = (i / amount) * 0.05
            cos_a, sin_a = np.cos(angle), np.sin(angle)
            
            dx = x_coords - cx
            dy = y_coords - cy
            
            sx = (cx + dx * cos_a - dy * sin_a).astype(np.int32)
            sy = (cy + dx * sin_a + dy * cos_a).astype(np.int32)
            
            sx = np.clip(sx, 0, width - 1)
            sy = np.clip(sy, 0, height - 1)
            
            result += arr[sy, sx].astype(np.float32)
        
        result = (result / amount).astype(np.uint8)
        return numpy_to_qimage(result)


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
        
        arr = qimage_to_numpy(image)
        height, width = arr.shape[:2]
        
        cx, cy = width / 2, height / 2
        samples = max(2, amount // 5)
        
        y_coords, x_coords = np.mgrid[0:height, 0:width].astype(np.float32)
        
        result = np.zeros_like(arr, dtype=np.float32)
        
        for i in range(samples):
            scale = 1.0 - (i / samples) * (amount / 100.0)
            
            sx = (cx + (x_coords - cx) * scale).astype(np.int32)
            sy = (cy + (y_coords - cy) * scale).astype(np.int32)
            
            sx = np.clip(sx, 0, width - 1)
            sy = np.clip(sy, 0, height - 1)
            
            result += arr[sy, sx].astype(np.float32)
        
        result = (result / samples).astype(np.uint8)
        return numpy_to_qimage(result)


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
        
        arr = qimage_to_numpy(image)
        height, width = arr.shape[:2]
        
        cx, cy = width / 2, height / 2
        radius = min(cx, cy)
        
        y_coords, x_coords = np.mgrid[0:height, 0:width].astype(np.float32)
        
        dx = x_coords - cx
        dy = y_coords - cy
        dist = np.sqrt(dx**2 + dy**2)
        
        # Bulge formula
        mask = (dist < radius) & (dist > 0)
        factor = np.zeros_like(dist)
        factor[mask] = (1 - (dist[mask] / radius)) * amount
        new_dist = np.where(mask, dist * (1 - factor), dist)
        
        scale = np.ones_like(dist)
        scale[mask] = new_dist[mask] / dist[mask]
        
        sx = (cx + dx * scale).astype(np.int32)
        sy = (cy + dy * scale).astype(np.int32)
        
        sx = np.clip(sx, 0, width - 1)
        sy = np.clip(sy, 0, height - 1)
        
        result = arr[sy, sx]
        return numpy_to_qimage(result)


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
        
        arr = qimage_to_numpy(image)
        height, width = arr.shape[:2]
        
        cx, cy = width / 2, height / 2
        radius = min(cx, cy)
        
        y_coords, x_coords = np.mgrid[0:height, 0:width].astype(np.float32)
        
        dx = x_coords - cx
        dy = y_coords - cy
        dist = np.sqrt(dx**2 + dy**2)
        
        # Twist amount decreases with distance from center
        twist = np.where(dist < radius, angle * (1 - dist / radius), 0)
        
        cos_t = np.cos(twist)
        sin_t = np.sin(twist)
        
        sx = (cx + dx * cos_t - dy * sin_t).astype(np.int32)
        sy = (cy + dx * sin_t + dy * cos_t).astype(np.int32)
        
        sx = np.clip(sx, 0, width - 1)
        sy = np.clip(sy, 0, height - 1)
        
        result = arr[sy, sx]
        return numpy_to_qimage(result)


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
        
        arr = qimage_to_numpy(image)
        height, width = arr.shape[:2]
        
        y_coords, x_coords = np.mgrid[0:height, 0:width].astype(np.float32)
        
        # Use sine waves for smooth dents
        dx = (amount * np.sin(y_coords / scale * 2 * np.pi)).astype(np.int32)
        dy = (amount * np.sin(x_coords / scale * 2 * np.pi)).astype(np.int32)
        
        sx = np.clip(x_coords.astype(np.int32) + dx, 0, width - 1)
        sy = np.clip(y_coords.astype(np.int32) + dy, 0, height - 1)
        
        result = arr[sy, sx]
        return numpy_to_qimage(result)


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
        
        arr = qimage_to_numpy(image)
        height, width = arr.shape[:2]
        cx, cy = width / 2, height / 2
        
        result = np.zeros_like(arr)
        
        ax = math.radians(rotate_x)
        ay = math.radians(rotate_y)
        
        focal_length = max(width, height) * 2
        
        y_coords, x_coords = np.mgrid[0:height, 0:width].astype(np.float32)
        
        # Normalize to center
        nx = (x_coords - cx) / zoom
        ny = (y_coords - cy) / zoom
        nz = np.zeros_like(nx)
        
        # Rotate around X axis
        y1 = ny * np.cos(ax) - nz * np.sin(ax)
        z1 = ny * np.sin(ax) + nz * np.cos(ax)
        
        # Rotate around Y axis
        x2 = nx * np.cos(ay) + z1 * np.sin(ay)
        z2 = -nx * np.sin(ay) + z1 * np.cos(ay)
        
        # Perspective projection
        valid = (focal_length + z2) > 0
        scale = np.where(valid, focal_length / (focal_length + z2), 1)
        
        sx = (x2 * scale + cx).astype(np.int32)
        sy = (y1 * scale + cy).astype(np.int32)
        
        # Check bounds and sample
        valid_mask = valid & (sx >= 0) & (sx < width) & (sy >= 0) & (sy < height)
        
        for i in range(height):
            for j in range(width):
                if valid_mask[i, j]:
                    result[i, j] = arr[sy[i, j], sx[i, j]]
        
        return numpy_to_qimage(result)


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
        
        arr = qimage_to_numpy(image)
        height, width = arr.shape[:2]
        cx, cy = width / 2, height / 2
        max_radius = np.sqrt(cx * cx + cy * cy)
        
        result = np.zeros_like(arr)
        
        y_coords, x_coords = np.mgrid[0:height, 0:width].astype(np.float32)
        
        if amount > 0:
            # Rectangular to Polar
            dx = x_coords - cx
            dy = y_coords - cy
            r = np.sqrt(dx * dx + dy * dy)
            theta = np.arctan2(dy, dx)
            
            sx = ((theta + np.pi) / (2 * np.pi) * width).astype(np.int32)
            sy = (r / max_radius * height).astype(np.int32)
        else:
            # Polar to Rectangular
            norm_x = x_coords / width
            norm_y = y_coords / height
            new_theta = norm_x * 2 * np.pi - np.pi
            new_r = norm_y * max_radius
            
            sx = (cx + new_r * np.cos(new_theta)).astype(np.int32)
            sy = (cy + new_r * np.sin(new_theta)).astype(np.int32)
        
        sx = np.clip(sx, 0, width - 1)
        sy = np.clip(sy, 0, height - 1)
        
        result = arr[sy, sx]
        return numpy_to_qimage(result)


class FrostedGlassDialog(QDialog):
    """Dialog for Frosted Glass effect."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Frosted Glass")
        
        layout = QVBoxLayout()
        
        # Amount (scatter radius)
        a_layout = QHBoxLayout()
        a_layout.addWidget(QLabel("Amount:"))
        self.a_spin = QSpinBox()
        self.a_spin.setRange(1, 20)
        self.a_spin.setValue(4)
        a_layout.addWidget(self.a_spin)
        layout.addLayout(a_layout)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
    
    def get_config(self):
        return {"amount": self.a_spin.value()}


class FrostedGlassEffect(Effect):
    """Frosted/etched glass effect - randomly scatters pixels to create frosted appearance."""
    name = "Frosted Glass"
    category = "Distort"
    
    def create_dialog(self, parent) -> QDialog:
        return FrostedGlassDialog(parent)
    
    def apply(self, image: QImage, config: dict) -> QImage:
        amount = config.get("amount", 4)
        
        arr = qimage_to_numpy(image)
        height, width = arr.shape[:2]
        
        # Create random offsets within the scatter radius
        np.random.seed(42)  # For reproducibility
        offset_x = np.random.randint(-amount, amount + 1, size=(height, width))
        offset_y = np.random.randint(-amount, amount + 1, size=(height, width))
        
        # Create coordinate grids
        y_coords, x_coords = np.mgrid[0:height, 0:width]
        
        # Apply offsets
        src_x = np.clip(x_coords + offset_x, 0, width - 1)
        src_y = np.clip(y_coords + offset_y, 0, height - 1)
        
        # Sample from offset positions
        result = arr[src_y, src_x]
        
        return numpy_to_qimage(result)
