from .layer import Layer
from PySide6.QtGui import QImage
from .effects import Effect

class AdjustmentLayer(Layer):
    def __init__(self, width: int, height: int, name: str, effect_cls: type[Effect], config: dict = None):
        super().__init__(width, height, name)
        self.effect_cls = effect_cls
        self.config = config or {}
        # Adjustment layers generally don't have their own "image" content in the same way,
        # but they might have a mask. For now, we assume global application.
        # We can keep self.image as a mask (all white = full apply) later.
        # For MVP, we ignore self.image content for the effect application itself, 
        # or treat it as a mask if we want. Let's stick to global effect for Tier 1.
        self.is_adjustment = True

    def render_effect(self, source_image: QImage) -> QImage:
        """
        Apply the effect to the source image.
        Returns a new QImage.
        """
        if not self.visible:
            return source_image
            
        effect = self.effect_cls()
        return effect.apply(source_image, self.config)
