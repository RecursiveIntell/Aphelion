from PySide6.QtGui import QImage, QPainter, QColor
import uuid

class Layer:
    def __init__(self, width: int, height: int, name: str = "New Layer"):
        self.id = str(uuid.uuid4())
        self.name = name
        self.visible = True
        self.opacity = 1.0
        self.blend_mode = QPainter.CompositionMode.CompositionMode_SourceOver
        
        # Initialize transparent image
        self.image = QImage(width, height, QImage.Format.Format_ARGB32_Premultiplied)
        self.image.fill(QColor(0, 0, 0, 0))
        self.mask = None # QImage(Format_Alpha8)
        self.is_adjustment = False

    def clear(self):
        self.image.fill(QColor(0, 0, 0, 0))

    def resize(self, width: int, height: int):
        new_image = QImage(width, height, QImage.Format.Format_ARGB32_Premultiplied)
        new_image.fill(QColor(0, 0, 0, 0))
        
        # Draw old image onto new centered? or top-left. Top-left is standard.
        painter = QPainter(new_image)
        painter.drawImage(0, 0, self.image)
        painter.end()
        
        self.image = new_image
        if self.mask:
            new_mask = QImage(width, height, QImage.Format.Format_Alpha8)
            new_mask.fill(255) # Default opaque
            painter = QPainter(new_mask)
            painter.drawImage(0, 0, self.mask)
            painter.end()
            self.mask = new_mask

    def create_mask(self):
        if self.mask: return
        self.mask = QImage(self.image.width(), self.image.height(), QImage.Format.Format_Alpha8)
        self.mask.fill(255) # White = Opaque

    def delete_mask(self):
        self.mask = None
