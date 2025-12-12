from PySide6.QtWidgets import QWidget, QVBoxLayout, QListWidget, QListWidgetItem, QPushButton, QHBoxLayout
from PySide6.QtCore import Qt
from ...core.document import Document

class HistoryPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.document = None
        
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0,0,0,0)
        
        # Controls (Undo/Redo buttons for convenience)
        self.btn_layout = QHBoxLayout()
        self.btn_undo = QPushButton("Undo")
        self.btn_redo = QPushButton("Redo")
        self.btn_undo.clicked.connect(self.undo)
        self.btn_redo.clicked.connect(self.redo)
        self.btn_layout.addWidget(self.btn_undo)
        self.btn_layout.addWidget(self.btn_redo)
        self.layout.addLayout(self.btn_layout)
        
        # History List
        self.list_widget = QListWidget()
        self.list_widget.itemClicked.connect(self.on_item_clicked)
        self.layout.addWidget(self.list_widget)
        
        self.setLayout(self.layout)
        
    def set_document(self, document: Document):
        if self.document:
            # Disconnect old signals? HistoryManager doesn't emit 'changed' yet.
            # We need to listen to document content changed or add a history changed signal
            # For now, rely on explicit refresh or document.content_changed?
            # Ideally HistoryManager emits 'history_changed'.
            pass
            
        self.document = document
        if self.document:
             # We need to hook into history changes.
             # Let's add a signal to HistoryManager or just refresh on content_changed for now (inefficient but works)
             self.document.content_changed.connect(self.refresh)
             # Also layer ops
             self.document.layer_added.connect(lambda x: self.refresh())
             self.document.layer_removed.connect(lambda x: self.refresh())
        
        self.refresh()

    def refresh(self):
        self.list_widget.clear()
        if not self.document:
            return
            
        # Helper to get command name
        def get_name(cmd):
            return cmd.__class__.__name__.replace("Command", "")

        # Show Undo Stack
        # We want to show the stack. Top is most recent.
        # It's tricky with QListWidget to show "Active" state.
        # Paint.NET shows a list of actions. The one you are AT is highlighted?
        # Or you click to go back to that state.
        
        # Let's list all actions in undo stack + redo stack?
        # Or just undo stack.
        
        # Simplified: Just show undo stack items.
        for cmd in self.document.history.undo_stack:
            name = getattr(cmd, 'name', cmd.__class__.__name__.replace("Command", ""))
            item = QListWidgetItem(name)
            self.list_widget.addItem(item)
            
        # Select last item
        if self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(self.list_widget.count() - 1)
            
    def undo(self):
        if self.document:
            self.document.history.undo()
            self.document.content_changed.emit() # Trigger update
            # Refresh handled by signal

    def redo(self):
        if self.document:
            self.document.history.redo()
            self.document.content_changed.emit()

    def on_item_clicked(self, item):
        row = self.list_widget.row(item)
        if self.document:
             self.document.history.goto_index(row)
             # Refresh is automatic via signal/trigger? 
             # undo() emits content_changed. which calls refresh.
             # BUT refresh clears list.
             # So we might lose selection or re-generate list.
             # If we regenerate list, we are fine, provided we select the right row.
             self.document.content_changed.emit()
