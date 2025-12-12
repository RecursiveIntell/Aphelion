from aphelion.core.plugins import AphelionPlugin, PluginType
from aphelion.core.effects import Effect
from PySide6.QtGui import QImage, QColor

class SepiaEffect(Effect):
    name = "Sepia"
    category = "Artistic"
    
    def apply(self, image: QImage, config: dict) -> QImage:
        # Simple Sepia implementation
        # For optimum speed in Python, we'd use LUT or direct byte access, 
        # but for example readability we iterate (or use optimized loop if shown).
        
        # Let's use QImage.pixel() optimization style for reasonable performance
        width = image.width()
        height = image.height()
        result = image.copy()
        
        for y in range(height):
            for x in range(width):
                c_int = image.pixel(x, y)
                r = (c_int >> 16) & 0xFF
                g = (c_int >> 8) & 0xFF
                b = c_int & 0xFF
                
                # Sepia formula
                tr = int(0.393 * r + 0.769 * g + 0.189 * b)
                tg = int(0.349 * r + 0.686 * g + 0.168 * b)
                tb = int(0.272 * r + 0.534 * g + 0.131 * b)
                
                if tr > 255: tr = 255
                if tg > 255: tg = 255
                if tb > 255: tb = 255
                
                result.setPixel(x, y, (0xFF << 24) | (tr << 16) | (tg << 8) | tb)
                
        return result

class SepiaPlugin(AphelionPlugin):
    name = "Sepia Filter"
    version = "1.0"
    author = "Aphelion Team"
    description = "Adds a classic Sepia filter."
    type = PluginType.EFFECT
    
    def initialize(self, context):
        registry = context.get("EffectRegistry")
        if registry:
            registry.register(SepiaEffect)
