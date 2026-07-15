"""
Layer ViewModels for Aphelion.

Provides presentation models for layers that can be bound to UI without
direct dependency on core Layer objects.
"""
from dataclasses import dataclass
from typing import Optional
from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QImage, QPixmap
from ..core.event_bus import get_event_bus
from ..core.events import LayerChangedEvent, LayerListChangedEvent, ActiveLayerChangedEvent


@dataclass(slots=True)
class LayerViewModel:
    """
    Presentation model for a single layer.

    Provides UI-friendly representation of layer data.
    """
    id: str
    name: str
    visible: bool
    opacity: float  # 0.0 to 1.0
    opacity_percent: int  # 0 to 100 for display
    is_active: bool
    thumbnail: Optional[QPixmap] = None

    @classmethod
    def from_layer(cls, layer, is_active: bool = False, thumbnail_size: tuple[int, int] = (64, 64)):
        """
        Create ViewModel from a Layer object.

        Args:
            layer: Core Layer object
            is_active: Whether this is the active layer
            thumbnail_size: Size for thumbnail generation

        Returns:
            LayerViewModel instance
        """
        # Generate thumbnail
        thumbnail = None
        if layer.image and not layer.image.isNull():
            thumbnail = QPixmap.fromImage(
                layer.image.scaled(*thumbnail_size, aspectMode=1, mode=1)  # Keep aspect, smooth
            )

        return cls(
            id=layer.id,
            name=layer.name,
            visible=layer.visible,
            opacity=layer.opacity,
            opacity_percent=int(layer.opacity * 100),
            is_active=is_active,
            thumbnail=thumbnail
        )


class LayerListViewModel(QObject):
    """
    ViewModel for managing a list of layers.

    Emits signals when layer list changes, enabling reactive UI updates.
    """

    # Signals
    layers_changed = Signal()  # Emitted when layer list structure changes
    active_layer_changed = Signal(str)  # Emitted with new active layer ID

    def __init__(self, document=None):
        super().__init__()
        self._document = document
        self._layer_viewmodels: list[LayerViewModel] = []
        self._active_layer_id: Optional[str] = None

        # Subscribe to events
        event_bus = get_event_bus()
        event_bus.subscribe(LayerChangedEvent, self._on_layer_changed)
        event_bus.subscribe(LayerListChangedEvent, self._on_layer_list_changed)
        event_bus.subscribe(ActiveLayerChangedEvent, self._on_active_layer_changed)

        if document:
            self.refresh()

    def set_document(self, document):
        """Set the document to track."""
        self._document = document
        self.refresh()

    def refresh(self):
        """Refresh layer viewmodels from document."""
        if not self._document:
            self._layer_viewmodels = []
            self.layers_changed.emit()
            return

        # Get active layer
        active_layer = self._document.get_active_layer()
        active_id = active_layer.id if active_layer else None

        # Create viewmodels for all layers
        self._layer_viewmodels = [
            LayerViewModel.from_layer(layer, is_active=(layer.id == active_id))
            for layer in reversed(self._document.layers)  # Reverse for top-to-bottom display
        ]

        self._active_layer_id = active_id
        self.layers_changed.emit()

    def get_layers(self) -> list[LayerViewModel]:
        """Get list of layer viewmodels."""
        return self._layer_viewmodels

    def get_active_layer_id(self) -> Optional[str]:
        """Get active layer ID."""
        return self._active_layer_id

    def _on_layer_changed(self, event: LayerChangedEvent):
        """Handle layer changed event."""
        if self._document and event.document_id == id(self._document):
            self.refresh()

    def _on_layer_list_changed(self, event: LayerListChangedEvent):
        """Handle layer list changed event."""
        if self._document and event.document_id == id(self._document):
            self.refresh()

    def _on_active_layer_changed(self, event: ActiveLayerChangedEvent):
        """Handle active layer changed event."""
        if self._document and event.document_id == id(self._document):
            self._active_layer_id = event.layer_id
            self.refresh()
            if event.layer_id:
                self.active_layer_changed.emit(event.layer_id)
