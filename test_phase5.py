import sys
import unittest
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QColor, QImage
from src.core.effects import EffectRegistry
from src.effects import register_all_effects
from src.effects.adjustments import InvertEffect, AutoLevelEffect, HueSaturationEffect

# Init App
app = QApplication.instance() or QApplication(sys.argv)

class TestPhase5(unittest.TestCase):
    def setUp(self):
        register_all_effects()
        
    def test_registry(self):
        effects = EffectRegistry.get_all()
        self.assertIn("Adjustments", effects)
        adj = effects["Adjustments"]
        names = [e.name for e in adj]
        self.assertIn("Invert Colors", names)
        self.assertIn("Brightness / Contrast", names)
        self.assertIn("Hue / Saturation", names)
        self.assertIn("Auto Level", names)
        
    def test_invert_effect(self):
        img = QImage(2, 2, QImage.Format.Format_ARGB32_Premultiplied)
        img.fill(QColor(255, 0, 0)) # Red
        
        effect = InvertEffect()
        new_img = effect.apply(img, {})
        
        c = new_img.pixelColor(0, 0)
        # Invert Red (255, 0, 0) -> Cyan (0, 255, 255)
        self.assertEqual(c.red(), 0)
        self.assertEqual(c.green(), 255)
        self.assertEqual(c.blue(), 255)
        
    def test_auto_level(self):
        # Create low contrast image (values 100-150)
        img = QImage(2, 2, QImage.Format.Format_ARGB32_Premultiplied)
        img.fill(QColor(100, 100, 100)) # Fill all with min
        img.setPixelColor(1, 1, QColor(150, 150, 150)) # Set max
        
        effect = AutoLevelEffect()
        new_img = effect.apply(img, {})
        
        # Should stretch to 0-255 roughly
        c1 = new_img.pixelColor(0, 0)
        c2 = new_img.pixelColor(1, 1)
        
        # Allow some epsilon due to int math
        self.assertLess(c1.red(), 10) # Close to 0
        self.assertGreater(c2.red(), 240) # Close to 255
        
    def test_hue_saturation(self):
        img = QImage(1, 1, QImage.Format.Format_ARGB32_Premultiplied)
        img.fill(QColor(255, 0, 0)) # Red (Hue 0, Sat 255)
        
        effect = HueSaturationEffect()
        # Rotate Hue by 180 -> Cyan/Blue-ish
        new_img = effect.apply(img, {"hue": 180, "saturation": 0})
        
        c = new_img.pixelColor(0, 0)
        # Red hue 0 -> 180 is Cyan (0, 255, 255) in RGB
        self.assertEqual(c.red(), 0)
        self.assertEqual(c.green(), 255)
        self.assertEqual(c.blue(), 255)

if __name__ == '__main__':
    unittest.main()
