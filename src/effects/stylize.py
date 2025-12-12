"""Stylize effects module - Drop Shadow, Channel Shift, etc.

Optimized with NumPy for high-performance image processing.
"""
from PySide6.QtGui import QImage, QColor, QPainter
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QSlider, QDialogButtonBox, QSpinBox, QCheckBox
from PySide6.QtCore import Qt
from ..core.effects import Effect
from ..utils.image_processing import qimage_to_numpy, numpy_to_qimage, gaussian_blur_np, box_blur_np
import numpy as np
import math


class DropShadowDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Drop Shadow")
        layout = QVBoxLayout()
        
        # Offset X
        ox_layout = QHBoxLayout()
        ox_layout.addWidget(QLabel("Offset X:"))
        self.ox_spin = QSpinBox()
        self.ox_spin.setRange(-100, 100)
        self.ox_spin.setValue(5)
        ox_layout.addWidget(self.ox_spin)
        layout.addLayout(ox_layout)
        
        # Offset Y
        oy_layout = QHBoxLayout()
        oy_layout.addWidget(QLabel("Offset Y:"))
        self.oy_spin = QSpinBox()
        self.oy_spin.setRange(-100, 100)
        self.oy_spin.setValue(5)
        oy_layout.addWidget(self.oy_spin)
        layout.addLayout(oy_layout)
        
        # Blur radius
        blur_layout = QHBoxLayout()
        blur_layout.addWidget(QLabel("Blur:"))
        self.blur_slider = QSlider(Qt.Orientation.Horizontal)
        self.blur_slider.setRange(0, 50)
        self.blur_slider.setValue(10)
        blur_layout.addWidget(self.blur_slider)
        self.blur_val = QLabel("10")
        self.blur_slider.valueChanged.connect(lambda v: self.blur_val.setText(str(v)))
        blur_layout.addWidget(self.blur_val)
        layout.addLayout(blur_layout)
        
        # Opacity
        opacity_layout = QHBoxLayout()
        opacity_layout.addWidget(QLabel("Opacity:"))
        self.opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.opacity_slider.setRange(0, 100)
        self.opacity_slider.setValue(60)
        opacity_layout.addWidget(self.opacity_slider)
        self.opacity_val = QLabel("60%")
        self.opacity_slider.valueChanged.connect(lambda v: self.opacity_val.setText(f"{v}%"))
        opacity_layout.addWidget(self.opacity_val)
        layout.addLayout(opacity_layout)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.setLayout(layout)
        
    def get_config(self):
        return {
            "offset_x": self.ox_spin.value(),
            "offset_y": self.oy_spin.value(),
            "blur": self.blur_slider.value(),
            "opacity": self.opacity_slider.value()
        }


class DropShadowEffect(Effect):
    """Add a drop shadow behind non-transparent content."""
    name = "Drop Shadow"
    category = "Stylize"
    
    def create_dialog(self, parent) -> QDialog:
        return DropShadowDialog(parent)
    
    def apply(self, image: QImage, config: dict) -> QImage:
        offset_x = config.get("offset_x", 5)
        offset_y = config.get("offset_y", 5)
        blur = config.get("blur", 10)
        opacity = config.get("opacity", 60) / 100.0
        
        arr = qimage_to_numpy(image)
        height, width = arr.shape[:2]
        
        # Create shadow from alpha channel
        shadow = np.zeros_like(arr)
        
        # Shift alpha to create shadow at offset position
        alpha = arr[:, :, 3].astype(np.float32) * opacity
        
        # Create shifted shadow
        shadow_alpha = np.zeros((height, width), dtype=np.float32)
        
        # Calculate valid source and destination ranges
        src_y_start = max(0, -offset_y)
        src_y_end = min(height, height - offset_y)
        src_x_start = max(0, -offset_x)
        src_x_end = min(width, width - offset_x)
        
        dst_y_start = max(0, offset_y)
        dst_y_end = min(height, height + offset_y)
        dst_x_start = max(0, offset_x)
        dst_x_end = min(width, width + offset_x)
        
        # Copy shifted alpha
        if dst_y_end > dst_y_start and dst_x_end > dst_x_start:
            shadow_alpha[dst_y_start:dst_y_end, dst_x_start:dst_x_end] = \
                alpha[src_y_start:src_y_end, src_x_start:src_x_end]
        
        # Blur shadow alpha if needed
        if blur > 0:
            shadow_alpha = gaussian_blur_np(shadow_alpha.astype(np.uint8), blur / 3.0).astype(np.float32)
        
        # Create shadow layer (black with alpha)
        shadow[:, :, 3] = shadow_alpha.astype(np.uint8)
        
        # Composite: shadow first, then original on top
        # Alpha blending: result = fg * fg_alpha + bg * (1 - fg_alpha)
        fg_alpha = arr[:, :, 3:4].astype(np.float32) / 255.0
        bg_alpha = shadow[:, :, 3:4].astype(np.float32) / 255.0
        
        result = arr.astype(np.float32) * fg_alpha + shadow.astype(np.float32) * (1 - fg_alpha)
        result[:, :, 3] = np.maximum(arr[:, :, 3], shadow[:, :, 3])
        
        return numpy_to_qimage(np.clip(result, 0, 255).astype(np.uint8))


class ChannelShiftDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Channel Shift")
        layout = QVBoxLayout()
        
        # Red channel offset X
        rx_layout = QHBoxLayout()
        rx_layout.addWidget(QLabel("Red X:"))
        self.rx_spin = QSpinBox()
        self.rx_spin.setRange(-50, 50)
        self.rx_spin.setValue(-5)
        rx_layout.addWidget(self.rx_spin)
        layout.addLayout(rx_layout)
        
        # Red channel offset Y
        ry_layout = QHBoxLayout()
        ry_layout.addWidget(QLabel("Red Y:"))
        self.ry_spin = QSpinBox()
        self.ry_spin.setRange(-50, 50)
        self.ry_spin.setValue(0)
        ry_layout.addWidget(self.ry_spin)
        layout.addLayout(ry_layout)
        
        # Blue channel offset X
        bx_layout = QHBoxLayout()
        bx_layout.addWidget(QLabel("Blue X:"))
        self.bx_spin = QSpinBox()
        self.bx_spin.setRange(-50, 50)
        self.bx_spin.setValue(5)
        bx_layout.addWidget(self.bx_spin)
        layout.addLayout(bx_layout)
        
        # Blue channel offset Y
        by_layout = QHBoxLayout()
        by_layout.addWidget(QLabel("Blue Y:"))
        self.by_spin = QSpinBox()
        self.by_spin.setRange(-50, 50)
        self.by_spin.setValue(0)
        by_layout.addWidget(self.by_spin)
        layout.addLayout(by_layout)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.setLayout(layout)
        
    def get_config(self):
        return {
            "red_x": self.rx_spin.value(),
            "red_y": self.ry_spin.value(),
            "blue_x": self.bx_spin.value(),
            "blue_y": self.by_spin.value()
        }


class ChannelShiftEffect(Effect):
    """RGB channel displacement for chromatic aberration/glitch effects."""
    name = "Channel Shift"
    category = "Stylize"
    
    def create_dialog(self, parent) -> QDialog:
        return ChannelShiftDialog(parent)
    
    def apply(self, image: QImage, config: dict) -> QImage:
        red_x = config.get("red_x", -5)
        red_y = config.get("red_y", 0)
        blue_x = config.get("blue_x", 5)
        blue_y = config.get("blue_y", 0)
        
        arr = qimage_to_numpy(image)
        height, width = arr.shape[:2]
        
        result = arr.copy()
        
        # BGRA format: B=0, G=1, R=2, A=3
        # Shift Red channel (index 2)
        result[:, :, 2] = np.roll(np.roll(arr[:, :, 2], red_x, axis=1), red_y, axis=0)
        
        # Shift Blue channel (index 0)
        result[:, :, 0] = np.roll(np.roll(arr[:, :, 0], blue_x, axis=1), blue_y, axis=0)
        
        return numpy_to_qimage(result)


class BokehBlurDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Bokeh Blur")
        layout = QVBoxLayout()
        
        # Radius
        r_layout = QHBoxLayout()
        r_layout.addWidget(QLabel("Radius:"))
        self.radius_slider = QSlider(Qt.Orientation.Horizontal)
        self.radius_slider.setRange(1, 30)
        self.radius_slider.setValue(8)
        r_layout.addWidget(self.radius_slider)
        self.radius_val = QLabel("8")
        self.radius_slider.valueChanged.connect(lambda v: self.radius_val.setText(str(v)))
        r_layout.addWidget(self.radius_val)
        layout.addLayout(r_layout)
        
        # Brightness boost for highlights
        b_layout = QHBoxLayout()
        b_layout.addWidget(QLabel("Brightness:"))
        self.brightness_slider = QSlider(Qt.Orientation.Horizontal)
        self.brightness_slider.setRange(0, 100)
        self.brightness_slider.setValue(20)
        b_layout.addWidget(self.brightness_slider)
        self.brightness_val = QLabel("20")
        self.brightness_slider.valueChanged.connect(lambda v: self.brightness_val.setText(str(v)))
        b_layout.addWidget(self.brightness_val)
        layout.addLayout(b_layout)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.setLayout(layout)
        
    def get_config(self):
        return {
            "radius": self.radius_slider.value(),
            "brightness": self.brightness_slider.value()
        }


class BokehBlurEffect(Effect):
    """Bokeh (lens) blur with circular aperture simulation."""
    name = "Bokeh Blur"
    category = "Blurs"
    
    def create_dialog(self, parent) -> QDialog:
        return BokehBlurDialog(parent)
    
    def apply(self, image: QImage, config: dict) -> QImage:
        radius = config.get("radius", 8)
        brightness = config.get("brightness", 20) / 100.0
        
        arr = qimage_to_numpy(image)
        height, width = arr.shape[:2]
        
        # Create circular kernel points
        kernel_points = []
        for ky in range(-radius, radius + 1):
            for kx in range(-radius, radius + 1):
                if kx * kx + ky * ky <= radius * radius:
                    kernel_points.append((ky, kx))
        
        kernel_count = len(kernel_points)
        if kernel_count == 0:
            return image.copy()
        
        result = np.zeros((height, width, 4), dtype=np.float32)
        weight_sum = np.zeros((height, width), dtype=np.float32)
        
        # Calculate luminance for weighting
        lum = (arr[:, :, 0].astype(np.float32) + 
               arr[:, :, 1].astype(np.float32) + 
               arr[:, :, 2].astype(np.float32)) / 3
        
        for ky, kx in kernel_points:
            shifted = np.roll(np.roll(arr, kx, axis=1), ky, axis=0)
            shifted_lum = np.roll(np.roll(lum, kx, axis=1), ky, axis=0)
            
            weight = 1.0 + (shifted_lum / 255.0) * brightness
            
            for c in range(4):
                result[:, :, c] += shifted[:, :, c].astype(np.float32) * weight
            weight_sum += weight
        
        # Normalize
        for c in range(4):
            result[:, :, c] /= np.maximum(weight_sum, 1)
        
        return numpy_to_qimage(np.clip(result, 0, 255).astype(np.uint8))


class SketchBlurDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Sketch Blur")
        layout = QVBoxLayout()
        
        # Radius
        r_layout = QHBoxLayout()
        r_layout.addWidget(QLabel("Radius:"))
        self.radius_slider = QSlider(Qt.Orientation.Horizontal)
        self.radius_slider.setRange(1, 20)
        self.radius_slider.setValue(3)
        r_layout.addWidget(self.radius_slider)
        self.radius_val = QLabel("3")
        self.radius_slider.valueChanged.connect(lambda v: self.radius_val.setText(str(v)))
        r_layout.addWidget(self.radius_val)
        layout.addLayout(r_layout)
        
        # Edge threshold
        t_layout = QHBoxLayout()
        t_layout.addWidget(QLabel("Edge Threshold:"))
        self.threshold_slider = QSlider(Qt.Orientation.Horizontal)
        self.threshold_slider.setRange(1, 100)
        self.threshold_slider.setValue(30)
        t_layout.addWidget(self.threshold_slider)
        self.threshold_val = QLabel("30")
        self.threshold_slider.valueChanged.connect(lambda v: self.threshold_val.setText(str(v)))
        t_layout.addWidget(self.threshold_val)
        layout.addLayout(t_layout)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.setLayout(layout)
        
    def get_config(self):
        return {
            "radius": self.radius_slider.value(),
            "threshold": self.threshold_slider.value()
        }


class SketchBlurEffect(Effect):
    """Edge-preserving blur that maintains sketch-like details."""
    name = "Sketch Blur"
    category = "Blurs"
    
    def create_dialog(self, parent) -> QDialog:
        return SketchBlurDialog(parent)
    
    def apply(self, image: QImage, config: dict) -> QImage:
        radius = config.get("radius", 3)
        threshold = config.get("threshold", 30)
        
        arr = qimage_to_numpy(image)
        height, width = arr.shape[:2]
        
        # Calculate luminance
        center_lum = (arr[:, :, 0].astype(np.float32) + 
                      arr[:, :, 1].astype(np.float32) + 
                      arr[:, :, 2].astype(np.float32)) / 3
        
        result = np.zeros_like(arr, dtype=np.float32)
        count = np.zeros((height, width), dtype=np.float32)
        
        for ky in range(-radius, radius + 1):
            for kx in range(-radius, radius + 1):
                shifted = np.roll(np.roll(arr, kx, axis=1), ky, axis=0)
                shifted_lum = np.roll(np.roll(center_lum, kx, axis=1), ky, axis=0)
                
                # Edge-preserving: only include if similar luminance
                diff = np.abs(shifted_lum - center_lum)
                mask = diff < threshold
                
                for c in range(4):
                    result[:, :, c] += np.where(mask, shifted[:, :, c].astype(np.float32), 0)
                count += mask.astype(np.float32)
        
        # Normalize
        count = np.maximum(count, 1)
        for c in range(4):
            result[:, :, c] /= count
        
        return numpy_to_qimage(np.clip(result, 0, 255).astype(np.uint8))


class ReliefDialog(QDialog):
    """Dialog for Relief effect."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Relief")
        layout = QVBoxLayout()
        
        # Angle
        a_layout = QHBoxLayout()
        a_layout.addWidget(QLabel("Angle:"))
        self.a_slider = QSlider(Qt.Orientation.Horizontal)
        self.a_slider.setRange(0, 360)
        self.a_slider.setValue(315)  # Top-left light
        a_layout.addWidget(self.a_slider)
        self.a_val = QLabel("315°")
        self.a_slider.valueChanged.connect(lambda v: self.a_val.setText(f"{v}°"))
        a_layout.addWidget(self.a_val)
        layout.addLayout(a_layout)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
    
    def get_config(self):
        return {"angle": self.a_slider.value()}


class ReliefEffect(Effect):
    """Relief/emboss with configurable lighting angle."""
    name = "Relief"
    category = "Stylize"
    
    def create_dialog(self, parent) -> QDialog:
        return ReliefDialog(parent)
    
    def apply(self, image: QImage, config: dict) -> QImage:
        angle = config.get("angle", 315)
        
        arr = qimage_to_numpy(image)
        height, width = arr.shape[:2]
        
        # Convert to grayscale
        gray = (arr[:, :, 0].astype(np.float32) * 0.299 + 
                arr[:, :, 1].astype(np.float32) * 0.587 + 
                arr[:, :, 2].astype(np.float32) * 0.114)
        
        # Calculate offset based on angle
        rad = math.radians(angle)
        dx = int(round(math.cos(rad)))
        dy = int(round(math.sin(rad)))
        
        # Shift and compute difference
        shifted = np.roll(np.roll(gray, dx, axis=1), dy, axis=0)
        
        # Difference + 128 for neutral gray
        relief = np.clip((gray - shifted) + 128, 0, 255).astype(np.uint8)
        
        # Output as grayscale with original alpha
        result = arr.copy()
        result[:, :, 0] = relief
        result[:, :, 1] = relief
        result[:, :, 2] = relief
        
        return numpy_to_qimage(result)
