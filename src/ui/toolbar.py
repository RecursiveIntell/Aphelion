from PySide6.QtWidgets import QToolBar, QWidget, QLabel
from PySide6.QtGui import QAction, QIcon
from ..core.document import Document
from ..tools.brush import BrushTool
from ..tools.eraser import EraserTool
from ..tools.rectangle_select import RectangleSelectTool
from .canvas import CanvasWidget

class Toolbar(QToolBar):
    def __init__(self, document: Document, canvas: CanvasWidget):
        super().__init__("Tools")
        self.document = document
        self.canvas = canvas
        self.setMovable(False)

        # Actions
        self.brush_action = QAction("Brush", self)
        self.brush_action.triggered.connect(self.select_brush)
        self.addAction(self.brush_action)

        self.eraser_action = QAction("Eraser", self)
        self.eraser_action.triggered.connect(self.select_eraser)
        self.addAction(self.eraser_action)

        self.rect_select_action = QAction("Select", self)
        self.rect_select_action.triggered.connect(self.select_rect_select)
        self.addAction(self.rect_select_action)

        self.addSeparator()

        self.undo_action = QAction("Undo", self)
        self.undo_action.triggered.connect(self.undo)
        self.addAction(self.undo_action)

        self.redo_action = QAction("Redo", self)
        self.redo_action.triggered.connect(self.redo)
        self.addAction(self.redo_action)
        
        # Tools
        self.brush_tool = BrushTool(document)
        self.eraser_tool = EraserTool(document)
        self.rect_select_tool = RectangleSelectTool(document)
        
        # Default
        self.select_brush()
        
    def select_brush(self):
        self.canvas.set_tool(self.brush_tool)
        
    def select_eraser(self):
        self.canvas.set_tool(self.eraser_tool)

    def select_rect_select(self):
        self.canvas.set_tool(self.rect_select_tool)
        
    def undo(self):
        if self.document.history.undo():
            self.document.content_changed.emit()
            
    def redo(self):
        if self.document.history.redo():
             self.document.content_changed.emit()
