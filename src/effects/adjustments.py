"""
Adjustment effects for Aphelion.

Optimized with NumPy for high-performance LUT-based transformations.
"""
from PySide6.QtGui import QImage, QColor, qRgb
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QSlider, QDialogButtonBox, QWidget
from PySide6.QtCore import Qt
from ..core.effects import Effect
from ..utils.image_processing import qimage_to_numpy, numpy_to_qimage, apply_lut
import numpy as np


class InvertEffect(Effect):
    name = "Invert Colors"
    category = "Adjustments"

    def apply(self, image: QImage, config: dict) -> QImage:
        arr = qimage_to_numpy(image)
        # Invert RGB channels (indices 0, 1, 2), preserve alpha (index 3)
        result = arr.copy()
        result[:, :, :3] = 255 - arr[:, :, :3]
        return numpy_to_qimage(result)


class BrightnessContrastDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Brightness / Contrast")
        
        layout = QVBoxLayout()
        
        # Brightness
        b_layout = QHBoxLayout()
        b_layout.addWidget(QLabel("Brightness:"))
        self.b_slider = QSlider(Qt.Orientation.Horizontal)
        self.b_slider.setRange(-100, 100)
        self.b_slider.setValue(0)
        b_layout.addWidget(self.b_slider)
        self.b_val = QLabel("0")
        self.b_slider.valueChanged.connect(lambda v: self.b_val.setText(str(v)))
        b_layout.addWidget(self.b_val)
        layout.addLayout(b_layout)
        
        # Contrast
        c_layout = QHBoxLayout()
        c_layout.addWidget(QLabel("Contrast:"))
        self.c_slider = QSlider(Qt.Orientation.Horizontal)
        self.c_slider.setRange(-100, 100)
        self.c_slider.setValue(0)
        c_layout.addWidget(self.c_slider)
        self.c_val = QLabel("0")
        self.c_slider.valueChanged.connect(lambda v: self.c_val.setText(str(v)))
        c_layout.addWidget(self.c_val)
        layout.addLayout(c_layout)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
        
    def get_config(self):
        return {
            "brightness": self.b_slider.value(),
            "contrast": self.c_slider.value()
        }


class BrightnessContrastEffect(Effect):
    name = "Brightness / Contrast"
    category = "Adjustments"
    
    def create_dialog(self, parent) -> QDialog:
        return BrightnessContrastDialog(parent)

    def apply(self, image: QImage, config: dict) -> QImage:
        brightness = config.get("brightness", 0)
        contrast = config.get("contrast", 0)
        
        if brightness == 0 and contrast == 0:
            return image.copy()
        
        # Build LUT using NumPy (vectorized)
        c = contrast
        if c == 100:
            c = 99  # Avoid div by zero
        factor = (259 * (c + 255)) / (255 * (259 - c))
        
        indices = np.arange(256, dtype=np.float32)
        lut = (indices - 128) * factor + 128 + brightness
        lut = np.clip(lut, 0, 255).astype(np.uint8)
        
        # Apply LUT
        arr = qimage_to_numpy(image)
        result = apply_lut(arr, lut, channels=(0, 1, 2))
        return numpy_to_qimage(result)


class HueSaturationDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Hue / Saturation")
        layout = QVBoxLayout()
        
        # Hue
        h_layout = QHBoxLayout()
        h_layout.addWidget(QLabel("Hue:"))
        self.h_slider = QSlider(Qt.Orientation.Horizontal)
        self.h_slider.setRange(-180, 180)
        self.h_slider.setValue(0)
        h_layout.addWidget(self.h_slider)
        self.h_val = QLabel("0")
        self.h_slider.valueChanged.connect(lambda v: self.h_val.setText(str(v)))
        h_layout.addWidget(self.h_val)
        layout.addLayout(h_layout)
        
        # Saturation
        s_layout = QHBoxLayout()
        s_layout.addWidget(QLabel("Saturation:"))
        self.s_slider = QSlider(Qt.Orientation.Horizontal)
        self.s_slider.setRange(-100, 100)
        self.s_slider.setValue(0)
        s_layout.addWidget(self.s_slider)
        self.s_val = QLabel("0")
        self.s_slider.valueChanged.connect(lambda v: self.s_val.setText(str(v)))
        s_layout.addWidget(self.s_val)
        layout.addLayout(s_layout)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.setLayout(layout)
        
    def get_config(self):
        return {
            "hue": self.h_slider.value(),
            "saturation": self.s_slider.value()
        }


class HueSaturationEffect(Effect):
    name = "Hue / Saturation"
    category = "Adjustments"
    
    def create_dialog(self, parent) -> QDialog:
        return HueSaturationDialog(parent)
        
    def apply(self, image: QImage, config: dict) -> QImage:
        hue_shift = config.get("hue", 0)
        sat_shift = config.get("saturation", 0)
        
        if hue_shift == 0 and sat_shift == 0:
            return image.copy()
        
        arr = qimage_to_numpy(image)
        
        # Convert BGRA to RGB for HSV conversion
        b, g, r, a = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2], arr[:, :, 3]
        
        # RGB to HSV conversion (vectorized)
        rgb = np.stack([r, g, b], axis=-1).astype(np.float32) / 255.0
        
        cmax = rgb.max(axis=-1)
        cmin = rgb.min(axis=-1)
        delta = cmax - cmin
        
        # Hue calculation
        h = np.zeros_like(cmax)
        mask_r = (cmax == rgb[:, :, 0]) & (delta > 0)
        mask_g = (cmax == rgb[:, :, 1]) & (delta > 0) & ~mask_r
        mask_b = (cmax == rgb[:, :, 2]) & (delta > 0) & ~mask_r & ~mask_g
        
        h[mask_r] = 60 * (((rgb[:, :, 1] - rgb[:, :, 2]) / np.maximum(delta, 1e-10)) % 6)[mask_r]
        h[mask_g] = 60 * (((rgb[:, :, 2] - rgb[:, :, 0]) / np.maximum(delta, 1e-10)) + 2)[mask_g]
        h[mask_b] = 60 * (((rgb[:, :, 0] - rgb[:, :, 1]) / np.maximum(delta, 1e-10)) + 4)[mask_b]
        
        # Saturation calculation
        s = np.where(cmax > 0, delta / np.maximum(cmax, 1e-10), 0)
        v = cmax
        
        # Apply hue shift
        h = (h + hue_shift) % 360
        
        # Apply saturation shift
        if sat_shift > 0:
            s = s + (1 - s) * (sat_shift / 100.0)
        else:
            s = s + s * (sat_shift / 100.0)
        s = np.clip(s, 0, 1)
        
        # HSV to RGB conversion
        c = v * s
        x = c * (1 - np.abs((h / 60) % 2 - 1))
        m = v - c
        
        h_segment = (h / 60).astype(np.int32) % 6
        
        r_out = np.zeros_like(h)
        g_out = np.zeros_like(h)
        b_out = np.zeros_like(h)
        
        # Segment 0: r=c, g=x, b=0
        mask = h_segment == 0
        r_out[mask], g_out[mask], b_out[mask] = c[mask], x[mask], 0
        # Segment 1: r=x, g=c, b=0
        mask = h_segment == 1
        r_out[mask], g_out[mask], b_out[mask] = x[mask], c[mask], 0
        # Segment 2: r=0, g=c, b=x
        mask = h_segment == 2
        r_out[mask], g_out[mask], b_out[mask] = 0, c[mask], x[mask]
        # Segment 3: r=0, g=x, b=c
        mask = h_segment == 3
        r_out[mask], g_out[mask], b_out[mask] = 0, x[mask], c[mask]
        # Segment 4: r=x, g=0, b=c
        mask = h_segment == 4
        r_out[mask], g_out[mask], b_out[mask] = x[mask], 0, c[mask]
        # Segment 5: r=c, g=0, b=x
        mask = h_segment == 5
        r_out[mask], g_out[mask], b_out[mask] = c[mask], 0, x[mask]
        
        r_out = ((r_out + m) * 255).astype(np.uint8)
        g_out = ((g_out + m) * 255).astype(np.uint8)
        b_out = ((b_out + m) * 255).astype(np.uint8)
        
        result = np.stack([b_out, g_out, r_out, a], axis=-1)
        return numpy_to_qimage(result)


class AutoLevelEffect(Effect):
    name = "Auto Level"
    category = "Adjustments"
    
    def apply(self, image: QImage, config: dict) -> QImage:
        arr = qimage_to_numpy(image)
        
        # Find min/max for each channel
        result = arr.copy()
        
        for c in range(3):  # B, G, R channels
            channel = arr[:, :, c]
            cmin = channel.min()
            cmax = channel.max()
            
            if cmax > cmin:
                # Build and apply LUT
                lut = np.arange(256, dtype=np.float32)
                lut = (lut - cmin) * 255 / (cmax - cmin)
                lut = np.clip(lut, 0, 255).astype(np.uint8)
                result[:, :, c] = lut[channel]
        
        return numpy_to_qimage(result)


class InvertAlphaEffect(Effect):
    """Invert only the alpha channel, leaving RGB unchanged."""
    name = "Invert Alpha"
    category = "Adjustments"

    def apply(self, image: QImage, config: dict) -> QImage:
        arr = qimage_to_numpy(image)
        result = arr.copy()
        result[:, :, 3] = 255 - arr[:, :, 3]  # Alpha channel is index 3
        return numpy_to_qimage(result)


class ColorBalanceDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Color Balance")
        layout = QVBoxLayout()
        
        # Cyan-Red
        cr_layout = QHBoxLayout()
        cr_layout.addWidget(QLabel("Cyan"))
        self.cr_slider = QSlider(Qt.Orientation.Horizontal)
        self.cr_slider.setRange(-100, 100)
        self.cr_slider.setValue(0)
        cr_layout.addWidget(self.cr_slider)
        cr_layout.addWidget(QLabel("Red"))
        self.cr_val = QLabel("0")
        self.cr_slider.valueChanged.connect(lambda v: self.cr_val.setText(str(v)))
        cr_layout.addWidget(self.cr_val)
        layout.addLayout(cr_layout)
        
        # Magenta-Green
        mg_layout = QHBoxLayout()
        mg_layout.addWidget(QLabel("Magenta"))
        self.mg_slider = QSlider(Qt.Orientation.Horizontal)
        self.mg_slider.setRange(-100, 100)
        self.mg_slider.setValue(0)
        mg_layout.addWidget(self.mg_slider)
        mg_layout.addWidget(QLabel("Green"))
        self.mg_val = QLabel("0")
        self.mg_slider.valueChanged.connect(lambda v: self.mg_val.setText(str(v)))
        mg_layout.addWidget(self.mg_val)
        layout.addLayout(mg_layout)
        
        # Yellow-Blue
        yb_layout = QHBoxLayout()
        yb_layout.addWidget(QLabel("Yellow"))
        self.yb_slider = QSlider(Qt.Orientation.Horizontal)
        self.yb_slider.setRange(-100, 100)
        self.yb_slider.setValue(0)
        yb_layout.addWidget(self.yb_slider)
        yb_layout.addWidget(QLabel("Blue"))
        self.yb_val = QLabel("0")
        self.yb_slider.valueChanged.connect(lambda v: self.yb_val.setText(str(v)))
        yb_layout.addWidget(self.yb_val)
        layout.addLayout(yb_layout)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.setLayout(layout)
        
    def get_config(self):
        return {
            "cyan_red": self.cr_slider.value(),
            "magenta_green": self.mg_slider.value(),
            "yellow_blue": self.yb_slider.value()
        }


class ColorBalanceEffect(Effect):
    """Adjust color balance between complementary color pairs."""
    name = "Color Balance"
    category = "Adjustments"
    
    def create_dialog(self, parent) -> QDialog:
        return ColorBalanceDialog(parent)
    
    def apply(self, image: QImage, config: dict) -> QImage:
        cyan_red = config.get("cyan_red", 0)
        magenta_green = config.get("magenta_green", 0)
        yellow_blue = config.get("yellow_blue", 0)
        
        if cyan_red == 0 and magenta_green == 0 and yellow_blue == 0:
            return image.copy()
        
        arr = qimage_to_numpy(image)
        result = arr.astype(np.int16)  # Prevent overflow
        
        # BGRA format: B=0, G=1, R=2
        # Cyan-Red affects R channel
        result[:, :, 2] += int(cyan_red * 2.55)
        # Magenta-Green affects G channel
        result[:, :, 1] += int(magenta_green * 2.55)
        # Yellow-Blue affects B channel
        result[:, :, 0] += int(yellow_blue * 2.55)
        
        result = np.clip(result, 0, 255).astype(np.uint8)
        return numpy_to_qimage(result)
