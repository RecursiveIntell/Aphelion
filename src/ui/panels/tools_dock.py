from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QGridLayout, QHBoxLayout
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtCore import QSize, Qt
from ...core.session import Session
from ...core.document import Document
# Import Tools
from ...tools.brush import BrushTool
from ...tools.eraser import EraserTool
from ...tools.rectangle_select import RectangleSelectTool
from ...tools.selection import EllipseSelectTool, LassoSelectTool, MagicWandTool
from ...tools.shape_tools import LineTool, RectangleTool, EllipseTool
from ...tools.fill import PaintBucketTool
from ...tools.gradient import GradientTool
from ...tools.recolor import RecolorTool
from ...tools.text_tool import TextTool
from ...tools.move import MoveSelectedPixelsTool
from ...tools.utility import ColorPickerTool
from ...tools.zoom import ZoomTool
from ...tools.clone_stamp import CloneStampTool
from ...tools.pencil import PencilTool
from ...tools.line_curve import LineCurveTool

class ToolsDock(QWidget):
    def __init__(self, session: Session):
        super().__init__()
        self.session = session
        
        self.layout = QVBoxLayout()
        self.grid = QGridLayout()
        self.grid.setSpacing(2)
        self.layout.addLayout(self.grid)
        
        # Tool Options moved to ToolOptionsBar
        
        self.layout.addStretch()

        self.layout.addStretch()
        self.setLayout(self.layout)
        
        self.tools = {}
        
        self._init_tools()
        
    def _init_tools(self):
        # Register standard tools
        # We initialize with None document initially; it will be set via set_active_document
        
        # Row 0: Selects
        self.register_tool("Rect Select", RectangleSelectTool(None, self.session), 0, 0, "rect_select.png", "S")
        self.register_tool("Ellipse Select", EllipseSelectTool(None, self.session), 0, 1, "ellipse_select.png")
        self.register_tool("Lasso Select", LassoSelectTool(None, self.session), 1, 0, "lasso.png", "L")
        self.register_tool("Magic Wand", MagicWandTool(None, self.session), 1, 1, "magic_wand.png", "W")
        
        # Row 1: Move
        self.register_tool("Move Pixel", MoveSelectedPixelsTool(None, self.session), 2, 0, "move.png", "M")
        
        # Row 2: Draw
        self.register_tool("Brush", BrushTool(None, self.session), 3, 0, "brush.png", "B")
        self.register_tool("Pencil", PencilTool(None, self.session), 3, 1, "pencil.png", "P")
        self.register_tool("Eraser", EraserTool(None, self.session), 4, 0, "eraser.png", "E")
        self.register_tool("Clone Stamp", CloneStampTool(None, self.session), 4, 1, "clone.png", "C")
        
        # Row 3: Shapes
        self.register_tool("Line", LineTool(None, self.session), 5, 0, "line.png", "O")
        self.register_tool("Curve", LineCurveTool(None, self.session), 5, 1, "curve.png")
        self.register_tool("Rect", RectangleTool(None, self.session), 6, 0, "rectangle.png")
        self.register_tool("Ellipse Shape", EllipseTool(None, self.session), 6, 1, "ellipse.png")
        
        # Row 4: Fill/Text
        self.register_tool("Bucket", PaintBucketTool(None, self.session), 7, 0, "bucket.png", "F")
        self.register_tool("Gradient", GradientTool(None, self.session), 7, 1, "gradient.png", "G")
        self.register_tool("Text", TextTool(None, self.session), 8, 0, "text.png", "T")
        self.register_tool("Picker", ColorPickerTool(None, self.session), 8, 1, "picker.png", "K")
        self.register_tool("Zoom", ZoomTool(None, self.session), 9, 0, "zoom.png", "Z")
        self.register_tool("Recolor", RecolorTool(None, self.session), 9, 1, "recolor.png", "R")
        
        # Set default
        self.select_tool("Brush")
        
    def set_active_document(self, document: Document):
        # Propagate to all tools
        for tool in self.tools.values():
            tool['instance'].document = document

    def register_tool(self, name, tool_instance, row, col, icon_name=None, shortcut=None):
        
        btn = QPushButton()
        if icon_name:
            # Assuming CWD is project root
            icon_path = f"src/assets/icons/{icon_name}"
            # Check existence or fallback?
            btn.setIcon(QIcon(icon_path))
            btn.setIconSize(QSize(24, 24))
        else:
            btn.setText(name[:2])
            
        tooltip_text = name
        if shortcut:
            tooltip_text += f" ({shortcut})"
            btn.setShortcut(shortcut)
            
        btn.setToolTip(tooltip_text)
        btn.setFixedSize(35, 35) # Slightly larger
        btn.setCheckable(True)
        btn.setProperty("toolButton", True)
        btn.clicked.connect(lambda: self.select_tool(name))
        
        self.grid.addWidget(btn, row, col)
        self.tools[name] = {'instance': tool_instance, 'button': btn}
        
    def select_tool(self, name):
        if name in self.tools:
            tool = self.tools[name]['instance']
            self.session.active_tool = tool
            
            # Update UI
            for n, t in self.tools.items():
                t['button'].setChecked(n == name)

