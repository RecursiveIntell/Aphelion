from abc import ABC, abstractmethod
from ..core.document import Document
from PySide6.QtCore import QPoint

class Tool(ABC):
    def __init__(self, document: Document, session):
        self.document = document
        self.session = session
        self.name = "Unknown Tool"

    def activate(self):
        self.on_activate()

    def deactivate(self):
        self.on_deactivate()

    def on_activate(self):
        pass

    def on_deactivate(self):
        pass

    def draw_overlay(self, painter):
        pass

    @abstractmethod
    def mouse_press(self, pos: QPoint):
        pass

    @abstractmethod
    def mouse_move(self, pos: QPoint):
        pass

    @abstractmethod
    def mouse_release(self, pos: QPoint):
        pass
