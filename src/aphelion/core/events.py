"""
Event types for Aphelion's event bus system.

All events are dataclasses with __slots__ for memory efficiency.
"""
from dataclasses import dataclass
from typing import Any, Optional


@dataclass(slots=True, frozen=True)
class DocumentChangedEvent:
    """Emitted when document properties change (size, etc.)."""
    document_id: str


@dataclass(slots=True, frozen=True)
class LayerChangedEvent:
    """Emitted when a layer is modified (image, mask, properties)."""
    layer_id: str
    document_id: str
    change_type: str  # "image", "mask", "properties", "added", "removed"


@dataclass(slots=True, frozen=True)
class LayerListChangedEvent:
    """Emitted when layer list structure changes (add, delete, reorder)."""
    document_id: str


@dataclass(slots=True, frozen=True)
class ActiveLayerChangedEvent:
    """Emitted when the active layer selection changes."""
    layer_id: Optional[str]
    document_id: str


@dataclass(slots=True, frozen=True)
class ToolChangedEvent:
    """Emitted when the active tool changes."""
    tool_name: str


@dataclass(slots=True, frozen=True)
class SelectionChangedEvent:
    """Emitted when the selection mask changes."""
    document_id: str
    has_selection: bool


@dataclass(slots=True, frozen=True)
class HistoryChangedEvent:
    """Emitted when undo/redo history changes."""
    document_id: str
    can_undo: bool
    can_redo: bool


@dataclass(slots=True, frozen=True)
class ColorChangedEvent:
    """Emitted when primary or secondary color changes."""
    is_primary: bool
    color: Any  # QColor


@dataclass(slots=True, frozen=True)
class BrushSizeChangedEvent:
    """Emitted when brush size changes."""
    size: int
