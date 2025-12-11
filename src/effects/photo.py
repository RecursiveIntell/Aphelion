"""
Photo and artistic effects for Aphelion.
"""
from PySide6.QtGui import QImage, QColor
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                               QSlider, QDialogButtonBox, QSpinBox, QWidget,
                               QComboBox, QCheckBox)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPainter, QPen, QBrush
from ..core.effects import Effect
import math


# ----------------- Curves Effect -----------------

class CurvesWidget(QWidget):
    """Simple curves control widget."""
    curve_changed = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(256, 256)
        self.setMaximumSize(256, 256)
        
        # Control points (input, output) - normalized 0-1
        self.points = [(0.0, 0.0), (0.25, 0.25), (0.5, 0.5), (0.75, 0.75), (1.0, 1.0)]
        self.selected_point = -1
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Background
        painter.fillRect(self.rect(), QColor(30, 30, 30))
        
        # Grid
        painter.setPen(QPen(QColor(60, 60, 60), 1))
        for i in range(1, 4):
            x = int(self.width() * i / 4)
            y = int(self.height() * i / 4)
            painter.drawLine(x, 0, x, self.height())
            painter.drawLine(0, y, self.width(), y)
        
        # Diagonal reference
        painter.setPen(QPen(QColor(80, 80, 80), 1, Qt.PenStyle.DashLine))
        painter.drawLine(0, self.height(), self.width(), 0)
        
        # Curve
        painter.setPen(QPen(QColor(200, 200, 200), 2))
        prev = None
        for i in range(256):
            x = i / 255.0
            y = self.evaluate(x)
            px = int(x * self.width())
            py = int((1 - y) * self.height())
            if prev:
                painter.drawLine(prev[0], prev[1], px, py)
            prev = (px, py)
        
        # Control points
        for i, (x, y) in enumerate(self.points):
            px = int(x * self.width())
            py = int((1 - y) * self.height())
            
            if i == self.selected_point:
                painter.setBrush(QBrush(QColor(100, 150, 255)))
            else:
                painter.setBrush(QBrush(QColor(255, 255, 255)))
            painter.setPen(QPen(Qt.black, 1))
            painter.drawEllipse(px - 5, py - 5, 10, 10)
        
        painter.end()
    
    def evaluate(self, x: float) -> float:
        """Evaluate curve at x using linear interpolation between points."""
        for i in range(len(self.points) - 1):
            if self.points[i][0] <= x <= self.points[i+1][0]:
                t = (x - self.points[i][0]) / (self.points[i+1][0] - self.points[i][0] + 0.0001)
                return self.points[i][1] + t * (self.points[i+1][1] - self.points[i][1])
        return x
    
    def mousePressEvent(self, event):
        x = event.position().x() / self.width()
        y = 1 - event.position().y() / self.height()
        
        # Find closest point
        min_dist = float('inf')
        for i, (px, py) in enumerate(self.points):
            dist = math.sqrt((x - px)**2 + (y - py)**2)
            if dist < min_dist and dist < 0.1:
                min_dist = dist
                self.selected_point = i
        
        if self.selected_point == -1:
            # Add new point
            for i in range(len(self.points) - 1):
                if self.points[i][0] < x < self.points[i+1][0]:
                    self.points.insert(i + 1, (x, y))
                    self.selected_point = i + 1
                    break
        
        self.update()
    
    def mouseMoveEvent(self, event):
        if self.selected_point > 0 and self.selected_point < len(self.points) - 1:
            x = max(0, min(1, event.position().x() / self.width()))
            y = max(0, min(1, 1 - event.position().y() / self.height()))
            
            # Keep x between neighbors
            x = max(self.points[self.selected_point - 1][0] + 0.01, 
                   min(self.points[self.selected_point + 1][0] - 0.01, x))
            
            self.points[self.selected_point] = (x, y)
            self.curve_changed.emit()
            self.update()
        elif self.selected_point == 0:
            # First point - only adjust y
            y = max(0, min(1, 1 - event.position().y() / self.height()))
            self.points[0] = (0, y)
            self.curve_changed.emit()
            self.update()
        elif self.selected_point == len(self.points) - 1:
            # Last point - only adjust y
            y = max(0, min(1, 1 - event.position().y() / self.height()))
            self.points[-1] = (1, y)
            self.curve_changed.emit()
            self.update()
    
    def mouseReleaseEvent(self, event):
        self.selected_point = -1
    
    def get_lut(self) -> list:
        """Generate lookup table from curve."""
        lut = []
        for i in range(256):
            val = self.evaluate(i / 255.0)
            lut.append(int(max(0, min(255, val * 255))))
        return lut


class CurvesDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Curves")
        
        layout = QVBoxLayout()
        
        # Channel selector
        ch_layout = QHBoxLayout()
        ch_layout.addWidget(QLabel("Channel:"))
        self.channel_combo = QComboBox()
        self.channel_combo.addItems(["RGB", "Red", "Green", "Blue"])
        ch_layout.addWidget(self.channel_combo)
        layout.addLayout(ch_layout)
        
        # Curves widget
        self.curves_widget = CurvesWidget()
        layout.addWidget(self.curves_widget)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
    
    def get_config(self):
        return {
            "lut": self.curves_widget.get_lut(),
            "channel": self.channel_combo.currentText()
        }


class CurvesEffect(Effect):
    name = "Curves"
    category = "Adjustments"
    
    def create_dialog(self, parent) -> QDialog:
        return CurvesDialog(parent)
    
    def apply(self, image: QImage, config: dict) -> QImage:
        lut = config.get("lut", list(range(256)))
        channel = config.get("channel", "RGB")
        
        width = image.width()
        height = image.height()
        result = image.copy()
        
        for y in range(height):
            for x in range(width):
                c = image.pixelColor(x, y)
                
                if channel == "RGB":
                    r = lut[c.red()]
                    g = lut[c.green()]
                    b = lut[c.blue()]
                elif channel == "Red":
                    r = lut[c.red()]
                    g = c.green()
                    b = c.blue()
                elif channel == "Green":
                    r = c.red()
                    g = lut[c.green()]
                    b = c.blue()
                else:  # Blue
                    r = c.red()
                    g = c.green()
                    b = lut[c.blue()]
                
                result.setPixelColor(x, y, QColor(r, g, b, c.alpha()))
        
        return result


# ----------------- Levels Effect -----------------

class LevelsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Levels")
        
        layout = QVBoxLayout()
        
        # Input levels
        layout.addWidget(QLabel("Input Levels:"))
        in_layout = QHBoxLayout()
        
        self.in_black = QSpinBox()
        self.in_black.setRange(0, 255)
        self.in_black.setValue(0)
        in_layout.addWidget(QLabel("Black:"))
        in_layout.addWidget(self.in_black)
        
        self.in_white = QSpinBox()
        self.in_white.setRange(0, 255)
        self.in_white.setValue(255)
        in_layout.addWidget(QLabel("White:"))
        in_layout.addWidget(self.in_white)
        
        layout.addLayout(in_layout)
        
        # Output levels
        layout.addWidget(QLabel("Output Levels:"))
        out_layout = QHBoxLayout()
        
        self.out_black = QSpinBox()
        self.out_black.setRange(0, 255)
        self.out_black.setValue(0)
        out_layout.addWidget(QLabel("Black:"))
        out_layout.addWidget(self.out_black)
        
        self.out_white = QSpinBox()
        self.out_white.setRange(0, 255)
        self.out_white.setValue(255)
        out_layout.addWidget(QLabel("White:"))
        out_layout.addWidget(self.out_white)
        
        layout.addLayout(out_layout)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
    
    def get_config(self):
        return {
            "in_black": self.in_black.value(),
            "in_white": self.in_white.value(),
            "out_black": self.out_black.value(),
            "out_white": self.out_white.value()
        }


class LevelsEffect(Effect):
    name = "Levels"
    category = "Adjustments"
    
    def create_dialog(self, parent) -> QDialog:
        return LevelsDialog(parent)
    
    def apply(self, image: QImage, config: dict) -> QImage:
        in_black = config.get("in_black", 0)
        in_white = config.get("in_white", 255)
        out_black = config.get("out_black", 0)
        out_white = config.get("out_white", 255)
        
        # Build LUT
        lut = []
        in_range = max(1, in_white - in_black)
        out_range = out_white - out_black
        
        for i in range(256):
            val = (i - in_black) / in_range
            val = max(0, min(1, val))
            val = out_black + val * out_range
            lut.append(int(max(0, min(255, val))))
        
        width = image.width()
        height = image.height()
        result = image.copy()
        
        for y in range(height):
            for x in range(width):
                c = image.pixelColor(x, y)
                r = lut[c.red()]
                g = lut[c.green()]
                b = lut[c.blue()]
                result.setPixelColor(x, y, QColor(r, g, b, c.alpha()))
        
        return result


# ----------------- Vignette Effect -----------------

class VignetteDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Vignette")
        
        layout = QVBoxLayout()
        
        # Amount
        a_layout = QHBoxLayout()
        a_layout.addWidget(QLabel("Amount:"))
        self.a_slider = QSlider(Qt.Orientation.Horizontal)
        self.a_slider.setRange(0, 100)
        self.a_slider.setValue(50)
        a_layout.addWidget(self.a_slider)
        layout.addLayout(a_layout)
        
        # Softness
        s_layout = QHBoxLayout()
        s_layout.addWidget(QLabel("Softness:"))
        self.s_slider = QSlider(Qt.Orientation.Horizontal)
        self.s_slider.setRange(0, 100)
        self.s_slider.setValue(50)
        s_layout.addWidget(self.s_slider)
        layout.addLayout(s_layout)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
    
    def get_config(self):
        return {
            "amount": self.a_slider.value(),
            "softness": self.s_slider.value()
        }


class VignetteEffect(Effect):
    name = "Vignette"
    category = "Photo"
    
    def create_dialog(self, parent) -> QDialog:
        return VignetteDialog(parent)
    
    def apply(self, image: QImage, config: dict) -> QImage:
        amount = config.get("amount", 50) / 100.0
        softness = config.get("softness", 50) / 100.0 + 0.5
        
        width = image.width()
        height = image.height()
        result = image.copy()
        
        cx = width / 2
        cy = height / 2
        max_dist = math.sqrt(cx*cx + cy*cy)
        
        for y in range(height):
            for x in range(width):
                c = image.pixelColor(x, y)
                
                # Calculate distance from center
                dx = x - cx
                dy = y - cy
                dist = math.sqrt(dx*dx + dy*dy) / max_dist
                
                # Apply vignette falloff
                falloff = 1 - (dist ** softness) * amount
                falloff = max(0, min(1, falloff))
                
                r = int(c.red() * falloff)
                g = int(c.green() * falloff)
                b = int(c.blue() * falloff)
                
                result.setPixelColor(x, y, QColor(r, g, b, c.alpha()))
        
        return result


# ----------------- Oil Painting Effect -----------------

class OilPaintingDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Oil Painting")
        
        layout = QVBoxLayout()
        
        r_layout = QHBoxLayout()
        r_layout.addWidget(QLabel("Radius:"))
        self.r_spin = QSpinBox()
        self.r_spin.setRange(1, 10)
        self.r_spin.setValue(3)
        r_layout.addWidget(self.r_spin)
        layout.addLayout(r_layout)
        
        i_layout = QHBoxLayout()
        i_layout.addWidget(QLabel("Intensity:"))
        self.i_spin = QSpinBox()
        self.i_spin.setRange(5, 50)
        self.i_spin.setValue(20)
        i_layout.addWidget(self.i_spin)
        layout.addLayout(i_layout)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
    
    def get_config(self):
        return {
            "radius": self.r_spin.value(),
            "intensity": self.i_spin.value()
        }


class OilPaintingEffect(Effect):
    """Oil painting effect using intensity binning."""
    name = "Oil Painting"
    category = "Artistic"
    
    def create_dialog(self, parent) -> QDialog:
        return OilPaintingDialog(parent)
    
    def apply(self, image: QImage, config: dict) -> QImage:
        radius = config.get("radius", 3)
        intensity = config.get("intensity", 20)
        
        width = image.width()
        height = image.height()
        result = image.copy()
        
        for y in range(radius, height - radius):
            for x in range(radius, width - radius):
                # Bin pixels by intensity
                bins = [[] for _ in range(intensity)]
                
                for dy in range(-radius, radius + 1):
                    for dx in range(-radius, radius + 1):
                        c = image.pixelColor(x + dx, y + dy)
                        gray = (c.red() + c.green() + c.blue()) // 3
                        bin_idx = min(intensity - 1, gray * intensity // 256)
                        bins[bin_idx].append((c.red(), c.green(), c.blue()))
                
                # Find most populated bin
                max_bin = max(range(intensity), key=lambda i: len(bins[i]))
                
                if bins[max_bin]:
                    avg_r = sum(c[0] for c in bins[max_bin]) // len(bins[max_bin])
                    avg_g = sum(c[1] for c in bins[max_bin]) // len(bins[max_bin])
                    avg_b = sum(c[2] for c in bins[max_bin]) // len(bins[max_bin])
                    result.setPixelColor(x, y, QColor(avg_r, avg_g, avg_b, image.pixelColor(x, y).alpha()))
        
        return result


# ----------------- Posterize Effect -----------------

class PosterizeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Posterize")
        
        layout = QVBoxLayout()
        
        l_layout = QHBoxLayout()
        l_layout.addWidget(QLabel("Levels:"))
        self.l_spin = QSpinBox()
        self.l_spin.setRange(2, 32)
        self.l_spin.setValue(4)
        l_layout.addWidget(self.l_spin)
        layout.addLayout(l_layout)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
    
    def get_config(self):
        return {"levels": self.l_spin.value()}


class PosterizeEffect(Effect):
    name = "Posterize"
    category = "Adjustments"
    
    def create_dialog(self, parent) -> QDialog:
        return PosterizeDialog(parent)
    
    def apply(self, image: QImage, config: dict) -> QImage:
        levels = config.get("levels", 4)
        
        width = image.width()
        height = image.height()
        result = image.copy()
        
        step = 256 // levels
        
        for y in range(height):
            for x in range(width):
                c = image.pixelColor(x, y)
                
                r = (c.red() // step) * step + step // 2
                g = (c.green() // step) * step + step // 2
                b = (c.blue() // step) * step + step // 2
                
                r = min(255, r)
                g = min(255, g)
                b = min(255, b)
                
                result.setPixelColor(x, y, QColor(r, g, b, c.alpha()))
        
        return result


# ----------------- Black & White Effect -----------------

class BlackWhiteEffect(Effect):
    """Convert to grayscale."""
    name = "Black && White"
    category = "Adjustments"
    
    def apply(self, image: QImage, config: dict) -> QImage:
        width = image.width()
        height = image.height()
        result = image.copy()
        
        for y in range(height):
            for x in range(width):
                c = image.pixelColor(x, y)
                # Weighted grayscale (luminosity)
                gray = int(c.red() * 0.299 + c.green() * 0.587 + c.blue() * 0.114)
                result.setPixelColor(x, y, QColor(gray, gray, gray, c.alpha()))
        
        return result


# ----------------- Red Eye Removal Effect -----------------

class RedEyeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Red Eye Removal")
        
        layout = QVBoxLayout()
        
        t_layout = QHBoxLayout()
        t_layout.addWidget(QLabel("Tolerance:"))
        self.t_slider = QSlider(Qt.Orientation.Horizontal)
        self.t_slider.setRange(10, 100)
        self.t_slider.setValue(50)
        t_layout.addWidget(self.t_slider)
        layout.addLayout(t_layout)
        
        s_layout = QHBoxLayout()
        s_layout.addWidget(QLabel("Saturation:"))
        self.s_slider = QSlider(Qt.Orientation.Horizontal)
        self.s_slider.setRange(10, 100)
        self.s_slider.setValue(70)
        s_layout.addWidget(self.s_slider)
        layout.addLayout(s_layout)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
    
    def get_config(self):
        return {
            "tolerance": self.t_slider.value(),
            "saturation": self.s_slider.value()
        }


class RedEyeRemovalEffect(Effect):
    """Red eye removal - detects and desaturates red pixels."""
    name = "Red Eye Removal"
    category = "Photo"
    
    def create_dialog(self, parent) -> QDialog:
        return RedEyeDialog(parent)
    
    def apply(self, image: QImage, config: dict) -> QImage:
        tolerance = config.get("tolerance", 50) / 100.0
        sat_threshold = config.get("saturation", 70) / 100.0
        
        width = image.width()
        height = image.height()
        result = image.copy()
        
        for y in range(height):
            for x in range(width):
                c = image.pixelColor(x, y)
                
                r = c.red()
                g = c.green()
                b = c.blue()
                
                # Check if pixel is "red" (high red, low green/blue)
                max_gb = max(g, b)
                
                if r > 50 and r > max_gb * (1 + tolerance):
                    # Calculate saturation
                    max_c = max(r, g, b)
                    min_c = min(r, g, b)
                    sat = (max_c - min_c) / max(max_c, 1)
                    
                    if sat > sat_threshold:
                        # Desaturate the red - replace with average
                        avg = (r + g + b) // 3
                        # Make it darker (pupils are dark)
                        new_val = min(avg, max_gb)
                        result.setPixelColor(x, y, QColor(new_val, new_val, new_val, c.alpha()))
        
        return result


# ----------------- Surface Blur Effect -----------------

class SurfaceBlurDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Surface Blur")
        
        layout = QVBoxLayout()
        
        r_layout = QHBoxLayout()
        r_layout.addWidget(QLabel("Radius:"))
        self.r_spin = QSpinBox()
        self.r_spin.setRange(1, 10)
        self.r_spin.setValue(3)
        r_layout.addWidget(self.r_spin)
        layout.addLayout(r_layout)
        
        t_layout = QHBoxLayout()
        t_layout.addWidget(QLabel("Threshold:"))
        self.t_slider = QSlider(Qt.Orientation.Horizontal)
        self.t_slider.setRange(5, 100)
        self.t_slider.setValue(30)
        t_layout.addWidget(self.t_slider)
        layout.addLayout(t_layout)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
    
    def get_config(self):
        return {
            "radius": self.r_spin.value(),
            "threshold": self.t_slider.value()
        }


class SurfaceBlurEffect(Effect):
    """Surface blur - edge-preserving blur."""
    name = "Surface Blur"
    category = "Blurs"
    
    def create_dialog(self, parent) -> QDialog:
        return SurfaceBlurDialog(parent)
    
    def apply(self, image: QImage, config: dict) -> QImage:
        radius = config.get("radius", 3)
        threshold = config.get("threshold", 30)
        
        width = image.width()
        height = image.height()
        result = image.copy()
        
        for y in range(radius, height - radius):
            for x in range(radius, width - radius):
                center = image.pixelColor(x, y)
                center_lum = (center.red() + center.green() + center.blue()) // 3
                
                r_sum = g_sum = b_sum = 0
                count = 0
                
                for dy in range(-radius, radius + 1):
                    for dx in range(-radius, radius + 1):
                        neighbor = image.pixelColor(x + dx, y + dy)
                        neighbor_lum = (neighbor.red() + neighbor.green() + neighbor.blue()) // 3
                        
                        # Only include if within threshold
                        if abs(neighbor_lum - center_lum) <= threshold:
                            r_sum += neighbor.red()
                            g_sum += neighbor.green()
                            b_sum += neighbor.blue()
                            count += 1
                
                if count > 0:
                    result.setPixelColor(x, y, QColor(
                        r_sum // count,
                        g_sum // count,
                        b_sum // count,
                        center.alpha()
                    ))
        
        return result
