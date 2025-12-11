from PySide6.QtGui import QImage, QColor, qRgb
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QSlider, QDialogButtonBox, QWidget
from PySide6.QtCore import Qt
from ..core.effects import Effect

class InvertEffect(Effect):
    name = "Invert Colors"
    category = "Adjustments"

    def apply(self, image: QImage, config: dict) -> QImage:
        # Pyside6 QImage.invertPixels() modifies in place.
        # We should copy first if we want pure function style, but we wrap in Undo Command anyway.
        # But Effect.apply signature implies return new.
        new_img = image.copy()
        new_img.invertPixels(QImage.InvertMode.InvertRgb)
        return new_img

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
            
        # This is slow in Python for large images.
        # Optimziation: Use Lookup Table (LUT).
        # Or NumPy if available (but keeping deps plain PySide currently preferred unless slow).
        # Let's try LUT approach which is reasonably fast in Python.
        
        # Calculate LUT
        lut = [0] * 256
        
        # Contrast factor
        # Formula: new = (old - 128) * factor + 128 + brightness
        # Factor = (259 * (contrast + 255)) / (255 * (259 - contrast))
        
        c = contrast
        if c == 100: c = 99 # Avoid div by zero
        factor = (259 * (c + 255)) / (255 * (259 - c))
        
        for i in range(256):
            val = (i - 128) * factor + 128 + brightness
            val = max(0, min(255, val))
            lut[i] = int(val)
            
        new_img = image.copy()
        
        # Apply LUT
        # QImage doesn't have applyLUT.
        # We have to iterate pixels or use bits().
        # Direct bit manipulation via memoryview is fastest in pure python.
        
        ptr = new_img.bits()
        # Assume ARGB32 or RGB32 (4 bytes)
        # We need to act on R, G, B channels.
        
        # Since this might be complex to access raw bytes reliably cross-platform/qt-ver without numpy,
        # let's use a simplified approach or see if QImage has optimized calls.
        # Unfortunately no direct contrast/brightness.
        
        # Fallback: scan lines?
        # Actually, let's use the extremely slow setPixel for MVP correctness, 
        # but acknowledge it needs optimization (NumPy).
        # Wait, manipulating bytearray of bits() is standard.
        
        size = new_img.sizeInBytes()
        if new_img.format() in (QImage.Format.Format_ARGB32, QImage.Format.Format_RGB32, QImage.Format.Format_ARGB32_Premultiplied):
             # 4 bytes per pixel. B G R A (Little Endian)
             dataset = ptr.tobytes() # Copy to bytearray to modify? 
             # QImage.bits() returns memoryview equivalent.
             # We can cast to bytearray if we want to write back?
             # Actually `ptr` is a memoryview/voidptr.
             # In PySide6, bits() returns a valid memory object we can use with generic view.
             
             # Let's Skip this optimization for "Phase 5 MVP" and implementing a simpler "Sepia" or something 
             # OR just pixel-by-pixel for small images to prove concept.
             # 
             # Actually, creating a QImage from data:
             # adjusted_data = bytearray(size)
             # ... apply lut ...
             # new_img = QImage(adjusted_data, w, h, format)
             
             pass
        
        # For now, let's iterate scanlines? Still slow.
        # Let's just implement Invert correctly (fast) and maybe skip complex pixel math for B/C 
        # unless we add NumPy.
        # WAIT! We can just not implement B/C logic fully for this step if it's too risky.
        # But User asked for it. 
        # Let's use a very inefficient SetPixel loops for MVP 
        # OR just add numpy to requirements? User said "standard linux environment".
        # Let's assume standard libraries.
        
        width = new_img.width()
        height = new_img.height()
        
        for y in range(height):
            for x in range(width):
                c = new_img.pixelColor(x, y)
                r = lut[c.red()]
                g = lut[c.green()]
                b = lut[c.blue()]
                new_img.setPixelColor(x, y, QColor(r, g, b, c.alpha()))
                
        return new_img

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
            
        new_img = image.copy()
        
        # Slow pixel loop for MVP
        width = new_img.width()
        height = new_img.height()
        
        for y in range(height):
            for x in range(width):
                c = new_img.pixelColor(x, y)
                
                # Hue
                h = c.hue()
                if h != -1:
                    h = (h + hue_shift) % 360
                    
                # Saturation
                s = c.saturation()
                if sat_shift > 0:
                     # Increase: s + (255-s) * shift% 
                     s += (255 - s) * (sat_shift / 100.0)
                else:
                     s += s * (sat_shift / 100.0)
                s = int(max(0, min(255, s)))
                
                # Reconstruct
                c.setHsv(h, s, c.value(), c.alpha())
                new_img.setPixelColor(x, y, c)
                
        return new_img

class AutoLevelEffect(Effect):
    name = "Auto Level"
    category = "Adjustments"
    
    def apply(self, image: QImage, config: dict) -> QImage:
        r_min, r_max = 255, 0
        g_min, g_max = 255, 0
        b_min, b_max = 255, 0
        
        width = image.width()
        height = image.height()
        
        for y in range(0, height, 1):
            for x in range(0, width, 1):
                c = image.pixelColor(x, y)
                r, g, b = c.red(), c.green(), c.blue()
                if r < r_min: r_min = r
                if r > r_max: r_max = r
                if g < g_min: g_min = g
                if g > g_max: g_max = g
                if b < b_min: b_min = b
                if b > b_max: b_max = b
                
        def build_lut(mn, mx):
            lut = [0]*256
            denom = mx - mn
            if denom == 0: denom = 1
            for i in range(256):
                 val = (i - mn) * 255 / denom
                 lut[i] = int(max(0, min(255, val)))
            return lut
            
        r_lut = build_lut(r_min, r_max)
        g_lut = build_lut(g_min, g_max)
        b_lut = build_lut(b_min, b_max)
        
        new_img = image.copy()
        
        for y in range(height):
            for x in range(width):
                c = new_img.pixelColor(x, y)
                r = r_lut[c.red()]
                g = g_lut[c.green()]
                b = b_lut[c.blue()]
                new_img.setPixelColor(x, y, QColor(r, g, b, c.alpha()))
                
        return new_img


class InvertAlphaEffect(Effect):
    """Invert only the alpha channel, leaving RGB unchanged."""
    name = "Invert Alpha"
    category = "Adjustments"

    def apply(self, image: QImage, config: dict) -> QImage:
        new_img = image.copy()
        width = new_img.width()
        height = new_img.height()
        
        for y in range(height):
            for x in range(width):
                c = new_img.pixelColor(x, y)
                new_alpha = 255 - c.alpha()
                new_img.setPixelColor(x, y, QColor(c.red(), c.green(), c.blue(), new_alpha))
        
        return new_img


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
        
        new_img = image.copy()
        width = new_img.width()
        height = new_img.height()
        
        # Convert -100..100 to -255..255 adjustments
        r_adj = int(cyan_red * 2.55)
        g_adj = int(magenta_green * 2.55)
        b_adj = int(yellow_blue * 2.55)
        
        for y in range(height):
            for x in range(width):
                c = new_img.pixelColor(x, y)
                r = max(0, min(255, c.red() + r_adj))
                g = max(0, min(255, c.green() + g_adj))
                b = max(0, min(255, c.blue() + b_adj))
                new_img.setPixelColor(x, y, QColor(r, g, b, c.alpha()))
        
        return new_img
