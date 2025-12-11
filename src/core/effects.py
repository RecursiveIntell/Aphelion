from abc import ABC, abstractmethod
from typing import Dict, Type
from PySide6.QtGui import QImage
from PySide6.QtWidgets import QDialog

class Effect(ABC):
    name: str = "Effect"
    category: str = "Uncategorized"
    
    @abstractmethod
    def apply(self, image: QImage, config: dict) -> QImage:
        """
        Apply the effect to the image and return a new QImage.
        This must be a pure function if possible, or at least not modify the input image in place
        unless explicitly intended (but returning a copy is safer for Undo).
        """
        pass

    def create_dialog(self, parent) -> QDialog | None:
        """
        Create and return a configuration dialog.
        If None, the effect is applied immediately with default/empty config.
        The Dialog must have a `get_config() -> dict` method expected by the caller if it returns Accepted.
        """
        return None

class EffectRegistry:
    _instance = None
    _effects: Dict[str, list[Type[Effect]]] = {} # Category -> List of Effect Classes

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EffectRegistry, cls).__new__(cls)
            cls._effects = {}
        return cls._instance

    @classmethod
    def register(cls, effect_class: Type[Effect]):
        cat = effect_class.category
        if cat not in cls._effects:
            cls._effects[cat] = []
        cls._effects[cat].append(effect_class)

    @classmethod
    def get_all(cls) -> Dict[str, list[Type[Effect]]]:
        return cls._effects
