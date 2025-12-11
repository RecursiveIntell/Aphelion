"""Stylize effects module - Drop Shadow, Channel Shift, etc."""
from PySide6.QtGui import QImage, QColor, QPainter
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QSlider, QDialogButtonBox, QSpinBox, QCheckBox
from PySide6.QtCore import Qt
from ..core.effects import Effect
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
        
        width = image.width()
        height = image.height()
        
        # Create shadow layer from alpha
        shadow = QImage(width, height, QImage.Format.Format_ARGB32_Premultiplied)
        shadow.fill(QColor(0, 0, 0, 0))
        
        # Copy alpha as black shadow
        for y in range(height):
            for x in range(width):
                c = image.pixelColor(x, y)
                if c.alpha() > 0:
                    # Shadow pixel at offset position
                    sx = x + offset_x
                    sy = y + offset_y
                    if 0 <= sx < width and 0 <= sy < height:
                        shadow_alpha = int(c.alpha() * opacity)
                        shadow.setPixelColor(sx, sy, QColor(0, 0, 0, shadow_alpha))
        
        # Simple box blur for shadow
        if blur > 0:
            shadow = self._box_blur(shadow, blur)
        
        # Composite: shadow first, then original on top
        result = QImage(width, height, QImage.Format.Format_ARGB32_Premultiplied)
        result.fill(QColor(0, 0, 0, 0))
        
        painter = QPainter(result)
        painter.drawImage(0, 0, shadow)
        painter.drawImage(0, 0, image)
        painter.end()
        
        return result
    
    def _box_blur(self, img: QImage, radius: int) -> QImage:
        """Simple box blur implementation."""
        width = img.width()
        height = img.height()
        result = img.copy()
        
        # Horizontal pass
        temp = QImage(width, height, QImage.Format.Format_ARGB32_Premultiplied)
        temp.fill(QColor(0, 0, 0, 0))
        
        for y in range(height):
            for x in range(width):
                r_sum, g_sum, b_sum, a_sum = 0, 0, 0, 0
                count = 0
                for dx in range(-radius, radius + 1):
                    nx = x + dx
                    if 0 <= nx < width:
                        c = img.pixelColor(nx, y)
                        r_sum += c.red()
                        g_sum += c.green()
                        b_sum += c.blue()
                        a_sum += c.alpha()
                        count += 1
                if count > 0:
                    temp.setPixelColor(x, y, QColor(
                        r_sum // count, g_sum // count, 
                        b_sum // count, a_sum // count
                    ))
        
        # Vertical pass
        for y in range(height):
            for x in range(width):
                r_sum, g_sum, b_sum, a_sum = 0, 0, 0, 0
                count = 0
                for dy in range(-radius, radius + 1):
                    ny = y + dy
                    if 0 <= ny < height:
                        c = temp.pixelColor(x, ny)
                        r_sum += c.red()
                        g_sum += c.green()
                        b_sum += c.blue()
                        a_sum += c.alpha()
                        count += 1
                if count > 0:
                    result.setPixelColor(x, y, QColor(
                        r_sum // count, g_sum // count,
                        b_sum // count, a_sum // count
                    ))
        
        return result


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
        
        width = image.width()
        height = image.height()
        
        result = QImage(width, height, QImage.Format.Format_ARGB32_Premultiplied)
        result.fill(QColor(0, 0, 0, 0))
        
        for y in range(height):
            for x in range(width):
                # Get green from original position
                g_c = image.pixelColor(x, y)
                g = g_c.green()
                a = g_c.alpha()
                
                # Get red from shifted position
                rx = x - red_x
                ry = y - red_y
                if 0 <= rx < width and 0 <= ry < height:
                    r = image.pixelColor(rx, ry).red()
                else:
                    r = 0
                
                # Get blue from shifted position
                bx = x - blue_x
                by = y - blue_y
                if 0 <= bx < width and 0 <= by < height:
                    b = image.pixelColor(bx, by).blue()
                else:
                    b = 0
                
                result.setPixelColor(x, y, QColor(r, g, b, a))
        
        return result


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
        
        width = image.width()
        height = image.height()
        
        result = QImage(width, height, QImage.Format.Format_ARGB32_Premultiplied)
        
        # Create circular kernel
        kernel_size = radius * 2 + 1
        kernel = []
        for ky in range(-radius, radius + 1):
            for kx in range(-radius, radius + 1):
                dist = math.sqrt(kx * kx + ky * ky)
                if dist <= radius:
                    kernel.append((kx, ky))
        
        kernel_count = len(kernel)
        if kernel_count == 0:
            return image.copy()
        
        for y in range(height):
            for x in range(width):
                r_sum, g_sum, b_sum, a_sum = 0.0, 0.0, 0.0, 0.0
                max_lum = 0
                
                for kx, ky in kernel:
                    nx, ny = x + kx, y + ky
                    if 0 <= nx < width and 0 <= ny < height:
                        c = image.pixelColor(nx, ny)
                        # Weight brighter pixels more (bokeh effect)
                        lum = (c.red() + c.green() + c.blue()) / 3
                        weight = 1.0 + (lum / 255.0) * brightness
                        r_sum += c.red() * weight
                        g_sum += c.green() * weight
                        b_sum += c.blue() * weight
                        a_sum += c.alpha()
                        max_lum = max(max_lum, lum)
                
                # Normalize
                total_weight = kernel_count * (1.0 + (max_lum / 255.0) * brightness * 0.5)
                r = int(min(255, r_sum / total_weight))
                g = int(min(255, g_sum / total_weight))
                b = int(min(255, b_sum / total_weight))
                a = int(a_sum / kernel_count)
                
                result.setPixelColor(x, y, QColor(r, g, b, a))
        
        return result


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
        
        width = image.width()
        height = image.height()
        
        result = QImage(width, height, QImage.Format.Format_ARGB32_Premultiplied)
        
        for y in range(height):
            for x in range(width):
                center = image.pixelColor(x, y)
                center_lum = (center.red() + center.green() + center.blue()) / 3
                
                r_sum, g_sum, b_sum, a_sum = 0, 0, 0, 0
                count = 0
                
                for ky in range(-radius, radius + 1):
                    for kx in range(-radius, radius + 1):
                        nx, ny = x + kx, y + ky
                        if 0 <= nx < width and 0 <= ny < height:
                            c = image.pixelColor(nx, ny)
                            c_lum = (c.red() + c.green() + c.blue()) / 3
                            
                            # Only include if similar luminance (edge-preserving)
                            if abs(c_lum - center_lum) < threshold:
                                r_sum += c.red()
                                g_sum += c.green()
                                b_sum += c.blue()
                                a_sum += c.alpha()
                                count += 1
                
                if count > 0:
                    result.setPixelColor(x, y, QColor(
                        r_sum // count, g_sum // count,
                        b_sum // count, a_sum // count
                    ))
                else:
                    result.setPixelColor(x, y, center)
        
        return result
