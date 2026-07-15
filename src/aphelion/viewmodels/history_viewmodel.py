"""
History ViewModel for Aphelion.

Provides presentation model for undo/redo history.
"""
from dataclasses import dataclass
from typing import Optional
from PySide6.QtCore import QObject, Signal
from ..core.event_bus import get_event_bus
from ..core.events import HistoryChangedEvent


@dataclass(slots=True)
class CommandViewModel:
    """
    Presentation model for a history command.

    Provides UI-friendly representation of command data.
    """
    index: int
    description: str
    is_current: bool


class HistoryViewModel(QObject):
    """
    ViewModel for undo/redo history.

    Emits signals when history state changes, enabling reactive UI updates.
    """

    # Signals
    history_changed = Signal()  # Emitted when history changes
    can_undo_changed = Signal(bool)  # Emitted when undo availability changes
    can_redo_changed = Signal(bool)  # Emitted when redo availability changes

    def __init__(self, document=None):
        super().__init__()
        self._document = document
        self._commands: list[CommandViewModel] = []
        self._can_undo = False
        self._can_redo = False

        # Subscribe to events
        event_bus = get_event_bus()
        event_bus.subscribe(HistoryChangedEvent, self._on_history_changed)

        if document:
            self.refresh()

    def set_document(self, document):
        """Set the document to track."""
        self._document = document
        self.refresh()

    def refresh(self):
        """Refresh command list from document."""
        if not self._document or not hasattr(self._document, 'history'):
            self._commands = []
            self._update_undo_redo_state(False, False)
            self.history_changed.emit()
            return

        history = self._document.history

        # Create command viewmodels
        self._commands = []
        current_index = len(history.undo_stack) - 1

        for i, cmd in enumerate(history.undo_stack):
            description = self._get_command_description(cmd)
            self._commands.append(
                CommandViewModel(
                    index=i,
                    description=description,
                    is_current=(i == current_index)
                )
            )

        # Update undo/redo availability
        can_undo = len(history.undo_stack) > 0
        can_redo = len(history.redo_stack) > 0
        self._update_undo_redo_state(can_undo, can_redo)

        self.history_changed.emit()

    def _get_command_description(self, command) -> str:
        """Get human-readable description of command."""
        # Try to get name from command
        if hasattr(command, 'name'):
            return command.name
        if hasattr(command, 'description'):
            return command.description

        # Fallback to class name
        class_name = command.__class__.__name__
        # Convert CamelCase to Title Case
        import re
        return re.sub(r'(?<!^)(?=[A-Z])', ' ', class_name.replace('Command', ''))

    def _update_undo_redo_state(self, can_undo: bool, can_redo: bool):
        """Update undo/redo state and emit signals if changed."""
        if can_undo != self._can_undo:
            self._can_undo = can_undo
            self.can_undo_changed.emit(can_undo)

        if can_redo != self._can_redo:
            self._can_redo = can_redo
            self.can_redo_changed.emit(can_redo)

    def get_commands(self) -> list[CommandViewModel]:
        """Get list of command viewmodels."""
        return self._commands

    def can_undo(self) -> bool:
        """Check if undo is available."""
        return self._can_undo

    def can_redo(self) -> bool:
        """Check if redo is available."""
        return self._can_redo

    def _on_history_changed(self, event: HistoryChangedEvent):
        """Handle history changed event."""
        if self._document and event.document_id == id(self._document):
            self._update_undo_redo_state(event.can_undo, event.can_redo)
            self.refresh()
