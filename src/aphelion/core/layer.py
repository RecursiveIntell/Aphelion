from dataclasses import dataclass, field
from typing import Final, Optional
from PySide6.QtGui import QImage, QPainter, QColor
import uuid

@dataclass(slots=True)
class Layer:
    width: int
    height: int
    name: str = "New Layer"
    id: Final[str] = field(default_factory=lambda: str(uuid.uuid4()))
    visible: bool = True
    opacity: float = 1.0
    blend_mode: QPainter.CompositionMode = QPainter.CompositionMode.CompositionMode_SourceOver
    image: QImage = field(init=False)
    mask: Optional[QImage] = None
    is_adjustment: bool = False

    def __post_init__(self):
        # Initialize transparent image
        self.image = QImage(self.width, self.height, QImage.Format.Format_ARGB32_Premultiplied)
        self.image.fill(QColor(0, 0, 0, 0))

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
