from PySide6.QtWidgets import (QMainWindow, QTabWidget, QDockWidget, QScrollArea, 
                               QFileDialog, QMessageBox, QStatusBar, QLabel, QWidget, QVBoxLayout, QSlider)
from PySide6.QtGui import QAction, QIcon, QKeySequence, QPalette, QShortcut
from PySide6.QtCore import Qt

from ..core.document import Document
from ..core.session import Session
from ..core.io import ProjectIO
from .canvas import CanvasWidget
from .layer_panel import LayerPanel
from .panels.history_panel import HistoryPanel
from .panels.colors_panel import ColorsPanel
from .panels.tools_dock import ToolsDock
from .dialogs import ResizeDialog, CanvasResizeDialog
from functools import partial
from ..core.effects import EffectRegistry, Effect
from ..effects import register_all_effects
from ..core.commands import MacroCommand, CanvasCommand
from ..core.plugins import PluginManager
from .plugin_ui import PluginManagerDialog
import os
from ..core.settings import SettingsManager
from .theme import ThemeManager
from .startup_screen import StartupScreen
from PySide6.QtCore import Qt, QPoint, QTimer, QThreadPool
from PySide6.QtWidgets import QApplication, QInputDialog, QProgressDialog, QGridLayout, QScrollArea, QVBoxLayout, QWidget, QScrollBar
from ..core.adjustment_layer import AdjustmentLayer
from ..core.commands import LayerStructureCommand
from ..core.autosave import AutosaveManager
from .worker import Worker

class MainWindow(QMainWindow):
    def __init__(self, settings=None, plugin_manager=None):
        super().__init__()
        self.setWindowTitle("Aphelion - Professional Paint for Linux")
        
        # Settings (use provided or create new)
        self.settings = settings if settings else SettingsManager()
        geometry = self.settings.get_value("window/geometry")
        if geometry:
            self.restoreGeometry(geometry)
        else:
            self.resize(1280, 800)
        
        # Theme is applied by AppController, but fallback here for standalone use
        if not settings:
            theme = self.settings.get_value("theme", "Dark")
            ThemeManager.apply_theme(QApplication.instance(), theme)
        
        # Core Session
        self.session = Session()
        self.session.active_tool_changed.connect(self.on_tool_changed)
        self.session.zoom_action_triggered.connect(self.on_zoom_action)
        self._connected_canvas = None
        
        # Install global event filter for keyboard shortcuts
        QApplication.instance().installEventFilter(self)
        # Central Widget: Tab Widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
        self.setCentralWidget(self.tab_widget)
        
        # Status Bar
        self.setup_statusbar()
        
        # Menus
        self.setup_menus()
        
        # Docks
        self.setup_docks()
        
        # Tool Options Bar (Above Docks/Central)
        from .tool_options import ToolOptionsBar
        self.addToolBar(Qt.TopToolBarArea, ToolOptionsBar(self.session))
        
        # Image Strip (Paint.NET Style)
        from .image_strip import ImageStripWidget
        self.image_strip = ImageStripWidget()
        self.image_strip.document_selected.connect(self.tab_widget.setCurrentIndex)
        
        # Central Layout
        central_container = QWidget()
        central_layout = QVBoxLayout()
        central_layout.setContentsMargins(0,0,0,0)
        central_layout.setSpacing(0)
        
        central_layout.addWidget(self.image_strip)
        central_layout.addWidget(self.tab_widget)
        
        central_container.setLayout(central_layout)
        self.setCentralWidget(central_container)
        
        # Hide native tabs
        self.tab_widget.tabBar().hide()
        self.tab_widget.currentChanged.connect(self.update_image_strip)
        
        # Initial Signal
        self.update_image_strip()
        
        # Initial Document - Don't create new by default if we want startup screen?
        # Standard behavior: Empty layout, or Startup Screen.
        # Let's create empty new doc behind the screen for now, or delay it.
        # self.new_document() 
        
        # QTimer.singleShot(0, self.show_startup_screen)
        # But wait, we need to handle "Open With" args properly in correct app lifecycle.
        # For this execution, we can just check if we want to show it.
        # Let's check sys.argv if possible? 
        # Actually, let's just trigger it via timer.
        from PySide6.QtCore import QTimer
        QTimer.singleShot(0, self.show_startup_screen)
        
        # Init Effects
        register_all_effects()
        
        # Init Plugins (use provided or create new)
        self.plugin_manager = plugin_manager if plugin_manager else PluginManager()
        
        # Setup Context Callbacks
        self.plugin_manager.set_context_callbacks({
            "register_tool": self._register_tool_from_plugin
            # "add_menu_action": ...
        })
        
        plugin_dir = os.path.expanduser("~/.aphelion/plugins")
        local_plugin_dir = os.path.join(os.getcwd(), "plugins")
        
        search_paths = []
        if os.path.exists(plugin_dir):
            search_paths.append(plugin_dir)
        if os.path.exists(local_plugin_dir):
            search_paths.append(local_plugin_dir)
            
        self.plugin_manager.discover_plugins(search_paths)
        
        self.setup_effects_menu()
        
        # Autosave
        self.autosave_manager = AutosaveManager(self)
        
        # ThreadPool
        self.threadpool = QThreadPool()
        
        # Global keyboard shortcuts (application-wide)
        self._setup_global_shortcuts()

    def setup_effects_menu(self):
        """Populate the Effects menu with all registered effect categories."""
        menu = self.menuBar()
        
        # Create Effects menu after Adjustments
        effects_menu = menu.addMenu("&Effects")
        
        # Get all categories from registry
        all_effects = EffectRegistry.get_all()
        
        # Add each category as a submenu (skip "Adjustments" which has its own menu)
        for category, effect_list in all_effects.items():
            if category == "Adjustments":
                continue  # Already in Adjustments menu
            
            if not effect_list:
                continue
                
            submenu = effects_menu.addMenu(category)
            for effect_cls in effect_list:
                submenu.addAction(effect_cls.name, partial(self.run_effect, effect_cls))
    
    def _setup_global_shortcuts(self):
        """Setup application-wide keyboard shortcuts."""
        # Shortcuts handled via eventFilter instead of QShortcut
        # to avoid conflicts and ensure proper event propagation
        pass
    
    def _swap_colors_debug(self):
        """Debug wrapper for swap colors."""
        print("DEBUG: X shortcut activated - swapping colors!")
        self.session.swap_colors()

    def eventFilter(self, obj, event):
        """Global event filter for keyboard shortcuts."""
        from PySide6.QtCore import QEvent
        
        if event.type() == QEvent.Type.KeyPress:
            # X key - swap colors (Paint.NET style)
            if event.key() == Qt.Key.Key_X and not event.modifiers():
                # Don't trigger if we're in a text input
                from PySide6.QtWidgets import QLineEdit, QTextEdit, QPlainTextEdit
                focused = QApplication.focusWidget()
                if not isinstance(focused, (QLineEdit, QTextEdit, QPlainTextEdit)):
                    self.session.swap_colors()
                    return True  # Event handled
        
        return super().eventFilter(obj, event)

    def setup_menus(self):
        menu = self.menuBar()
        
        # File
        file_menu = menu.addMenu("&File")
        file_menu.addAction("&New", self.new_document, QKeySequence.New)
        file_menu.addAction("&Open Project...", self.open_project, QKeySequence.Open)
        file_menu.addAction("Open &Image...", self.open_image, QKeySequence("Ctrl+Shift+O"))
        file_menu.addSeparator()
        file_menu.addAction("&Save", self.save_project, QKeySequence.Save)
        file_menu.addAction("Save &As...", self.save_project_as, QKeySequence.SaveAs)
        file_menu.addSeparator()
        file_menu.addAction("&Export...", self.export_image)
        file_menu.addSeparator()
        
        # Recents
        self.recents_menu = file_menu.addMenu("Recent &Files")
        self.update_recents_menu()
        
        file_menu.addSeparator()
        file_menu.addAction("E&xit", self.close)
        
        # Edit
        edit_menu = menu.addMenu("&Edit")
        edit_menu.addAction("&Undo", self.undo, QKeySequence.Undo)
        edit_menu.addAction("&Redo", self.redo, QKeySequence.Redo)
        edit_menu.addSeparator()
        edit_menu.addAction("Cu&t", self.cut, QKeySequence.Cut)
        edit_menu.addAction("&Copy", self.copy, QKeySequence.Copy)
        edit_menu.addAction("&Paste", self.paste, QKeySequence.Paste)
        edit_menu.addSeparator()
        edit_menu.addAction("Swap &Colors (X)", self.session.swap_colors)
        
        # Select
        select_menu = menu.addMenu("&Select")
        select_menu.addAction("Select &All", lambda: self.active_document().select_all() if self.active_document() else None, QKeySequence.SelectAll)
        select_menu.addAction("&Deselect", lambda: self.active_document().clear_selection() if self.active_document() else None, QKeySequence("Ctrl+D"))
        select_menu.addAction("&Invert Selection", lambda: self.active_document().invert_selection() if self.active_document() else None, QKeySequence("Ctrl+I"))
        select_menu.addSeparator()
        select_menu.addAction("&Feather...", self.feather_selection)
        select_menu.addAction("E&xpand...", self.expand_selection)
        select_menu.addAction("&Contract...", self.contract_selection)
        
        # View
        view_menu = menu.addMenu("&View")
        self.act_zoom_fit = view_menu.addAction("Fit to &Window", self.zoom_fit, QKeySequence("Ctrl+0"))
        self.act_actual_size = view_menu.addAction("&Actual Size", lambda: self.set_zoom(1.0), QKeySequence("Ctrl+1"))
        view_menu.addSeparator()
        
        # Theme Toggle
        theme_menu = view_menu.addMenu("Theme")
        action_dark = QAction("Dark", self)
        action_dark.triggered.connect(lambda: self.change_theme("Dark"))
        theme_menu.addAction(action_dark)
        
        action_light = QAction("Light", self)
        action_light.triggered.connect(lambda: self.change_theme("Light"))
        theme_menu.addAction(action_light)
        
        view_menu.addSeparator()
        self.act_console = view_menu.addAction("Script &Console", lambda: self.console_dock.setVisible(not self.console_dock.isVisible()))
        
        # Image
        image_menu = menu.addMenu("&Image")
        image_menu.addAction("Resize Image...", self.open_resize_image_dialog, QKeySequence("Ctrl+R"))
        image_menu.addAction("Canvas Size...", self.open_resize_canvas_dialog, QKeySequence("Ctrl+Shift+R"))
        image_menu.addSeparator()
        image_menu.addAction("Flip Horizontal", lambda: self.flip_image(True, False))
        image_menu.addAction("Flip Vertical", lambda: self.flip_image(False, True))
        image_menu.addSeparator()
        image_menu.addAction("Rotate 90° CW", lambda: self.rotate_image(90), QKeySequence("Ctrl+H"))
        image_menu.addAction("Rotate 90° CCW", lambda: self.rotate_image(-90), QKeySequence("Ctrl+G"))
        image_menu.addAction("Rotate 180°", lambda: self.rotate_image(180), QKeySequence("Ctrl+J"))
        image_menu.addSeparator()
        image_menu.addAction("Flatten", self.flatten_image, QKeySequence("Ctrl+Shift+F"))
        
        # Adjustments
        adj_menu = menu.addMenu("&Adjustments")
        # Populate dynamically
        effects = EffectRegistry.get_all().get("Adjustments", [])
        for effect_cls in effects:
             # Capture class in closure
             adj_menu.addAction(effect_cls.name, partial(self.run_effect, effect_cls))
        
        # Layers
        layer_menu = menu.addMenu("&Layers")
        layer_menu.addAction("Add New Layer", lambda: self.active_document().add_layer() if self.active_document() else None, QKeySequence("Ctrl+Shift+N"))
        
        # New Adjustment Layer Submenu
        new_adj_menu = layer_menu.addMenu("Add New Adjustment Layer")
        for effect_cls in effects:
             new_adj_menu.addAction(effect_cls.name, partial(self.add_adjustment_layer, effect_cls))
             
        layer_menu.addSeparator()
        layer_menu.addAction("Duplicate Layer", self.duplicate_layer, QKeySequence("Ctrl+Shift+D"))
        layer_menu.addAction("Merge Layer Down", self.merge_layer_down, QKeySequence("Ctrl+M"))
        layer_menu.addAction("Delete Layer", lambda: self.active_document().delete_layer(self.active_document()._active_layer_index) if self.active_document() else None, QKeySequence.Delete)
        layer_menu.addSeparator()
        layer_menu.addAction("Layer Properties...", self.open_layer_properties, QKeySequence("F4"))

        # Help
        help_menu = menu.addMenu("&Help")
        help_menu.addAction("Plugin Manager...", self.open_plugin_manager)
        help_menu.addAction("About", self.show_about)

    def open_plugin_manager(self):
        dlg = PluginManagerDialog(self)
        dlg.exec()

    def show_about(self):
        QMessageBox.about(self, "About Aphelion", "Aphelion Image Editor\n\nA modern, layer-based image editor for Linux.")


    def _register_tool_from_plugin(self, name, tool_cls, icon=None, shortcut=None):
        # Calculate position based on current tool count
        count = len(self.tools_dock_widget.tools)
        cols = 2
        
        # Determine next available row/col
        # We assume standard tools fill rows 0-7 consecutively?
        # Not strictly true if there are gaps, but close enough.
        # Ideally we check the max row in the grid.
        
        # Simple approach: Start from Row 8, fill linearly
        # Or just append based on count.
        # If count=15 (0-14), next is 15.
        # 15 // 2 = 7, 15 % 2 = 1. (Occupied by Zoom if logic held strict, but Zoom is manually at 7,1).
        # Actually standard tools are manually placed.
        # We should start after the last occupied row.
        
        # Let's just find the max active row in the grid or hardcode start
        # Zoom is at 7,1. So next is 8,0.
        
        # We can ask ToolsDock for next slot? No method.
        # Let's derive it from count assuming dense packing.
        # 16th tool -> 8,0.
        # 17th tool -> 8,1.
        
        r = count // cols
        c = count % cols
        
        # Instantiate tool
        doc = self.active_document()
        try:
            tool_instance = tool_cls(doc, self.session)
            # Use default icon if None?
            if not icon:
                # No default icon provided by plugin? 
                # ToolsDock handles text fallback.
                pass
                
            self.tools_dock_widget.register_tool(name, tool_instance, r, c, icon, shortcut)
        except Exception as e:
            print(f"Failed to instantiate plugin tool {name}: {e}")
        
    def setup_docks(self):
        # 1. Tools (Left)
        self.tools_dock = QDockWidget("Tools", self)
        self.tools_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.tools_dock.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
        
        self.tools_dock_widget = ToolsDock(self.session)
        self.tools_dock.setWidget(self.tools_dock_widget)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.tools_dock)
        
        # 2. Colors (Right Top)
        self.colors_dock = QDockWidget("Colors", self)
        self.colors_dock_widget = ColorsPanel(self.session) # Assuming we have this
        self.colors_dock.setWidget(self.colors_dock_widget)
        self.addDockWidget(Qt.RightDockWidgetArea, self.colors_dock)
        
        # 3. History (Right Middle)
        self.history_dock = QDockWidget("History", self)
        self.history_panel = HistoryPanel() # Needs doc connection
        self.history_dock.setWidget(self.history_panel)
        self.addDockWidget(Qt.RightDockWidgetArea, self.history_dock)
        
        # 4. Layers (Right Bottom)
        self.layer_dock = QDockWidget("Layers", self)
        self.layer_panel = LayerPanel(None, self.session) # Init empty
        self.layer_dock.setWidget(self.layer_panel)
        self.addDockWidget(Qt.RightDockWidgetArea, self.layer_dock)
        
        # Menu toggle actions
        # ... (Assuming menu setup handles this or we add it)
        
        # Tabify Docks on Right?
        # self.tabifyDockWidget(self.layer_dock, self.history_dock) 
        
        # Script Console Dock (Bottom)
        self.console_dock = QDockWidget("Script Console", self)
        from ..core.api import AphelionAPI
        from .script_console import ScriptConsole
        
        self.api = AphelionAPI(self.session)
        # Wire active doc getter
        self.api.set_doc_getter(self.active_document)
        
        self.console_widget = ScriptConsole(self.api)
        self.console_dock.setWidget(self.console_widget)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.console_dock)
        self.console_dock.hide() # Hidden by default

    def setup_statusbar(self):
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
        
        self.lbl_cursor = QLabel("0, 0")
        self.lbl_cursor.setMinimumWidth(100)
        self.statusbar.addPermanentWidget(self.lbl_cursor)
        
        # Zoom Controls
        self.slider_zoom = QSlider(Qt.Horizontal)
        self.slider_zoom.setRange(10, 500) # 10% to 500%
        self.slider_zoom.setValue(100)
        self.slider_zoom.setFixedWidth(100)
        self.slider_zoom.valueChanged.connect(self.on_zoom_slider)
        self.statusbar.addPermanentWidget(self.slider_zoom)
        
        self.lbl_zoom = QLabel("100%")
        self.lbl_zoom.setMinimumWidth(50)
        self.statusbar.addPermanentWidget(self.lbl_zoom)
        
        self.lbl_size = QLabel("0 x 0")
        self.statusbar.addPermanentWidget(self.lbl_size)

    def active_document(self) -> Document | None:
        current_widget = self.tab_widget.currentWidget()
        if current_widget:
            return current_widget.canvas.document
        return None
        
    def active_canvas(self) -> CanvasWidget | None:
        current_widget = self.tab_widget.currentWidget()
        if current_widget:
            return current_widget.canvas
        return None
        
    def zoom_in(self):
        canvas = self.active_canvas()
        if canvas: canvas.zoom_in()

    def zoom_out(self):
        canvas = self.active_canvas()
        if canvas: canvas.zoom_out()

    def zoom_fit(self):
        canvas = self.active_canvas()
        if canvas: canvas.zoom_to_fit()

    def set_zoom(self, value):
        canvas = self.active_canvas()
        if canvas: canvas.set_zoom(value)

    def on_zoom_changed(self, value):
        txt = f"{int(value * 100)}%"
        self.lbl_zoom.setText(txt)
        # Update slider without signal loop?
        self.slider_zoom.blockSignals(True)
        # Map 10% - 500% to 1-100? Or just set value if range matches logic.
        # Slider logic is tricky with non-linear or float scale.
        # Let's keep it simple: Slider 1 to 200 (10% to 2000%? No 5000% is limit).
        # Let's say slider is percent.
        self.slider_zoom.setValue(int(value * 100))
        self.slider_zoom.blockSignals(False)
        
        # Update title bar with document name and zoom
        self.update_window_title()
    
    def update_window_title(self):
        """Update window title to show current document and zoom (Paint.NET style)."""
        doc = self.active_document()
        canvas = self.active_canvas()
        
        if doc and canvas:
            # Get document name from tab
            idx = self.tab_widget.currentIndex()
            name = self.tab_widget.tabText(idx) if idx >= 0 else "Untitled"
            zoom_pct = int(canvas.scale * 100)
            self.setWindowTitle(f"{name} @ {zoom_pct}% - Aphelion")
        else:
            self.setWindowTitle("Aphelion - Professional Paint for Linux")

    def on_zoom_slider(self, value):
        # value is percent
        scale = value / 100.0
        self.set_zoom(scale)

    def on_zoom_action(self, factor):
        canvas = self.active_canvas()
        if canvas:
            new_zoom = canvas.scale * factor
            self.set_zoom(new_zoom)

    def cut(self):
        self.copy()
        # Clear selection or active layer content?
        # If selection active: clear selection.
        # Else: clear layer.
        doc = self.active_document()
        if doc: 
            # Check if selection active?
            # doc.clear_selection_content() # Need this method?
            # Or use CanvasCommand to clear.
            # Simplified:
            pass

    def copy(self):
        doc = self.active_document()
        if not doc: return
        layer = doc.get_active_layer()
        if not layer: return
        
        # If selection, copy cropped.
        if doc.has_selection:
            # Crop to selection
            r = doc.get_selection_region().boundingRect()
            img = layer.image.copy(r)
            # Mask?
            # Ideal: Mask out non-selected.
            # Convert Selection Mask to Bitmap, apply clip.
            # TODO: Proper masked copy. 
            pass
        else:
            img = layer.image.copy()
            
        clipboard = QApplication.clipboard()
        clipboard.setImage(img)

    def paste(self):
        doc = self.active_document()
        if not doc: return
        clipboard = QApplication.clipboard()
        img = clipboard.image()
        if img.isNull(): return
        
        # Add as new layer
        new_layer = doc.add_layer("Pasted Layer")
        # Draw img onto new layer
        # Ensure size matches or center?
        if img.size() != doc.size:
             # Center
             x = (doc.size.width() - img.width()) // 2
             y = (doc.size.height() - img.height()) // 2
             
             # Create full size image
             full_img = QImage(doc.size, QImage.Format.Format_ARGB32_Premultiplied)
             full_img.fill(0)
             p = QPainter(full_img)
             p.drawImage(x, y, img)
             p.end()
             new_layer.image = full_img
        else:
             new_layer.image = img
        
        doc.content_changed.emit()

    def add_adjustment_layer(self, effect_cls):
        doc = self.active_document()
        if not doc: return
        
        # 1. Config Dialog
        effect = effect_cls()
        dlg = effect.create_dialog(self)
        if dlg:
            if dlg.exec():
                config = dlg.get_config()
            else:
                return # Cancelled
        else:
            config = {}
            
        # 2. Create Layer
        layer = AdjustmentLayer(doc.size.width(), doc.size.height(), effect_cls.name, effect_cls, config)
        
        # 3. Add to Document (above active)
        index = doc._active_layer_index + 1
        if index > len(doc.layers): index = len(doc.layers)
        
        cmd = LayerStructureCommand(doc, "add", layer=layer, index=index)
        doc.history.push(cmd)
        cmd.execute()

    def new_document(self):
        doc = Document(800, 600)
        # Add default layer
        bg = doc.add_layer("Background")
        from PySide6.QtGui import QColor
        bg.image.fill(QColor(255, 255, 255))
        
        self.create_tab(doc, "Untitled")

    def update_image_strip(self):
        # Gather docs
        docs = []
        for i in range(self.tab_widget.count()):
            widget = self.tab_widget.widget(i)
            # Find CanvasWidget in the grid layout (it's inside scroll area)
            # grid -> scroll -> canvas
            # We can findChild CanvasWidget
            canvas = widget.findChild(CanvasWidget)
            if canvas:
                docs.append(canvas.document)
            else:
                docs.append(None)
                
        if hasattr(self, 'image_strip'):
            self.image_strip.sync(docs, self.tab_widget.currentIndex())

    def create_tab(self, document: Document, title: str):
        # Container
        container = QWidget()
        # Custom GRID layout for Rulers
        from PySide6.QtWidgets import QGridLayout
        layout = QGridLayout()
        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(0)
        
        # Rulers
        from .ruler import RulerWidget
        ruler_h = RulerWidget(RulerWidget.HORIZONTAL)
        ruler_v = RulerWidget(RulerWidget.VERTICAL)
        # Corner box
        corner = QWidget()
        corner.setStyleSheet("background-color: #e0e0e0;")
        
        scroll = QScrollArea()
        scroll.setBackgroundRole(QPalette.ColorRole.Dark)
        scroll.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        canvas = CanvasWidget(document, session=self.session)
        scroll.setWidget(canvas)
        canvas.setFixedSize(document.size)
        
        # Add to Grid
        # Row 0: Corner | Ruler H
        # Row 1: Ruler V | Scroll
        layout.addWidget(corner, 0, 0)
        layout.addWidget(ruler_h, 0, 1)
        layout.addWidget(ruler_v, 1, 0)
        layout.addWidget(scroll, 1, 1)
        
        # Store refs
        container.canvas = canvas
        container.scroll = scroll
        container.ruler_h = ruler_h
        container.ruler_v = ruler_v
        
        container.setLayout(layout)
        
        self.tab_widget.addTab(container, title)
        self.tab_widget.setCurrentWidget(container)
        
        # Explicitly set tools' document reference immediately
        self.tools_dock_widget.set_active_document(document)
        canvas.set_tool(self.session.active_tool)
        
        # Update Strip
        self.update_image_strip()
        
        # Connect updates
        # Zoom
        def update_rulers_zoom(scale):
            ruler_h.set_zoom(scale)
            ruler_v.set_zoom(scale)
            
        canvas.zoom_changed.connect(update_rulers_zoom)
        
        # Scroll / Pan Offset
        # We need to track the visible area of the scroll bar
        v_bar = scroll.verticalScrollBar()
        h_bar = scroll.horizontalScrollBar()
        
        # This is tricky: Ruler offset should match document coordinates.
        # When scrolled to 0,0 (top left of canvas visible), ruler should show 0.
        # But canvas is centered if smaller than view.
        # Also canvas has "offset" (pan).
        
        # Let's link Ruler offset to:
        # 1. Scrollbar position?
        # If scrollbar is at 0, and canvas is centered, we have a gap.
        
        # Let's simplify: Ruler shows Canvas coordinates.
        # Ruler needs to know "Which doc coordinate is at the top-left of the viewport?"
        
        def update_ruler_offset():
            # Calculate what doc coordinate is at (0,0) of the scroll viewport
            # Scroll Area viewport coordinates relative to Canvas Widget?
            # Canvas is child of scroll.
            # viewport top-left in canvas coords = -canvas.pos()? 
            # Not quite.
            
            # Simple approach: relative position
            # Canvas position in viewport coords
            # When centered, canvas.x() > 0.
            # When scrolled, canvas.x() < 0 (effectively).
            
            # Ruler 0 should align with Canvas 0.
            # If Canvas is at x=50 in viewport, Ruler should start at -50 (doc coords)? 
            # No. Ruler draws relative to ITSELF.
            # If Ruler x=50 is aligned with Canvas x=0.
            # Then Ruler x=0 corresponds to Canvas x=-50.
            # So offset = -50 / scale.
            
            # Use mapFromGlobal?
            # Start of Ruler Widget in Global
            ruler_origin = ruler_h.mapToGlobal(QPoint(0,0))
            # Start of Canvas Widget in Global
            canvas_origin = canvas.mapToGlobal(QPoint(0,0))
            
            diff_x = canvas_origin.x() - ruler_origin.x()
            diff_y = canvas_origin.y() - ruler_v.mapToGlobal(QPoint(0,0)).y()
            
            # Doc coord at Ruler 0 = (0 - diff) / scale
            # offset = -diff / scale
            
            scale = canvas.scale
            off_x = -diff_x / scale
            off_y = -diff_y / scale
            
            ruler_h.set_offset(off_x)
            ruler_v.set_offset(off_y)
            
        # Connect scroll bars
        v_bar.valueChanged.connect(update_ruler_offset)
        h_bar.valueChanged.connect(update_ruler_offset)
        # Also on resize?
        # scroll.resizeEvent? 
        # We can implement a timer or event filter?
        # Or just connect canvas paint/update?
        
        # For MVP: Connect to canvas 'content_changed' or 'cursor_moved' triggers update? 
        # Or just standard scroll/zoom triggers.
        canvas.zoom_changed.connect(lambda: update_ruler_offset())
        
        # Initial
        # We need to wait for layout?
        QTimer.singleShot(100, update_ruler_offset)
        
        pass
            
    def close_tab(self, index):
        self.tab_widget.removeTab(index)
        
    def on_tab_changed(self, index):
        doc = self.active_document()
        if doc:
            # Update Docks
            self.layer_panel.set_document(doc)
            # self.layer_panel.refresh() # handled by set_document
            self.layer_panel.list_widget.selectionModel().clear() # Reset selection UI
            
            self.history_panel.set_document(doc)
            self.tools_dock_widget.set_active_document(doc)
            
            # Connect status updates
            # Connect status updates
            current_canvas = self.active_canvas()
            
            # Disconnect previous
            if self._connected_canvas and self._connected_canvas != current_canvas:
                try:
                    self._connected_canvas.cursor_moved.disconnect(self.update_cursor_label)
                except: pass
                try:
                    self._connected_canvas.zoom_changed.disconnect(self.on_zoom_changed)
                except: pass
                self._connected_canvas = None
                
            # Connect new
            if current_canvas and current_canvas != self._connected_canvas:
                current_canvas.cursor_moved.connect(self.update_cursor_label)
                current_canvas.zoom_changed.connect(self.on_zoom_changed)
                self._connected_canvas = current_canvas
                
                # Update zoom UI now
                self.on_zoom_changed(current_canvas.scale)
            
            self.lbl_size.setText(f"{doc.size.width()} x {doc.size.height()}")
            
            # Apply active tool to new canvas
            if self.session.active_tool:
                self.active_canvas().set_tool(self.session.active_tool)

    def on_tool_changed(self, tool):
        canvas = self.active_canvas()
        if canvas:
            canvas.set_tool(tool)
        self.statusbar.showMessage(f"Tool: {tool.name}")

    def update_cursor_label(self, pos):
        self.lbl_cursor.setText(f"{pos.x()}, {pos.y()}")

    def undo(self):
        if self.history_panel:
            self.history_panel.undo()
            
    def redo(self):
        if self.history_panel:
            self.history_panel.redo()

    def open_project(self, filepath=None):
        if not filepath:
            filepath, _ = QFileDialog.getOpenFileName(self, "Open Project", "", "Aphelion Project (*.aphelion)")
            
        if filepath:
            try:
                doc = ProjectIO.load_project(filepath)
                # Add to Recents
                self.settings.add_recent_file(filepath)
                self.update_recents_menu()
                
                name = filepath.split("/")[-1]
                self.create_tab(doc, name)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to open: {e}")

    def open_image(self, filepath=None):
        """Open a standard image file (PNG, JPEG, WebP, TIFF, etc.)"""
        if not filepath:
            filepath, _ = QFileDialog.getOpenFileName(
                self, "Open Image", "", 
                ProjectIO.get_supported_import_formats()
            )
            
        if filepath:
            try:
                img = QImage(filepath)
                if img.isNull():
                    raise ValueError("Could not load image")
                
                # Create new document from image
                doc = Document(img.width(), img.height())
                layer = doc.add_layer("Background")
                
                # Copy image to layer (ensure ARGB32 format)
                if img.format() != QImage.Format.Format_ARGB32_Premultiplied:
                    img = img.convertToFormat(QImage.Format.Format_ARGB32_Premultiplied)
                
                from PySide6.QtGui import QPainter
                p = QPainter(layer.image)
                p.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source)
                p.drawImage(0, 0, img)
                p.end()
                
                # Set file path for reference
                doc.file_path = filepath
                
                # Add to recents
                self.settings.add_recent_file(filepath)
                self.update_recents_menu()
                
                name = os.path.basename(filepath)
                self.create_tab(doc, name)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to open image: {e}")

    def save_project(self):
        self.save_project_as() # TODO: cache path in tab

    def save_project_as(self):
        doc = self.active_document()
        if not doc: return
        filepath, _ = QFileDialog.getSaveFileName(self, "Save Project", "", "Aphelion Project (*.aphelion)")
        if filepath:
            if not filepath.endswith(".aphelion"): filepath += ".aphelion"
            try:
                ProjectIO.save_project(doc, filepath)
                # Add to Recents
                self.settings.add_recent_file(filepath)
                self.update_recents_menu()
                
                # Update tab title (MVP: just rudimentary check)
                idx = self.tab_widget.currentIndex()
                self.tab_widget.setTabText(idx, os.path.basename(filepath))
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save: {e}")

    def export_image(self):
        doc = self.active_document()
        if not doc: return
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Export Image", "", 
            ProjectIO.get_supported_export_formats()
        )
        if filepath:
            try:
                ProjectIO.export_flat(doc, filepath)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export: {e}")

    def open_resize_image_dialog(self):
        doc = self.active_document()
        if not doc: return
        dlg = ResizeDialog(self, doc.size.width(), doc.size.height(), "Resize Image")
        if dlg.exec():
            w, h = dlg.get_values()
            doc.resize_image(w, h)
            # Update canvas view size? On Tab Change/Content Change it should happen.
            # create_tab sets FixedSize once. We need to update it.
            # We connect Document.content_changed but that's generic.
            # We should probably connect Document.size_changed signal or check content changed.
            # Currently resize emits content_changed.
            # We need to update scroll/canvas fixed size.
            self.active_canvas().setFixedSize(doc.size)
            self.lbl_size.setText(f"{w} x {h}")

    def open_resize_canvas_dialog(self):
        doc = self.active_document()
        if not doc: return
        dlg = CanvasResizeDialog(self, doc.size.width(), doc.size.height())
        if dlg.exec():
            w, h = dlg.get_values()
            anchor = dlg.get_anchor()
            doc.resize_canvas(w, h, anchor)
            self.active_canvas().setFixedSize(doc.size)
            self.lbl_size.setText(f"{w} x {h}")

    def flip_image(self, h, v):
        doc = self.active_document()
        if doc: doc.flip_image(h, v)

    def rotate_image(self, angle):
        doc = self.active_document()
        if doc: 
            doc.rotate_image(angle)
            self.active_canvas().setFixedSize(doc.size) # If size changed
            self.lbl_size.setText(f"{doc.size.width()} x {doc.size.height()}")

    def flatten_image(self):
        doc = self.active_document()
        if doc: doc.flatten_image()

    def merge_layer_down(self):
        doc = self.active_document()
        if doc: doc.merge_layer_down(doc._active_layer_index)

    def duplicate_layer(self):
        doc = self.active_document()
        if doc: doc.duplicate_layer(doc._active_layer_index)

    def open_layer_properties(self):
        print("DEBUG: open_layer_properties called")
        doc = self.active_document()
        if not doc: 
            print("DEBUG: No active document")
            return
        layer = doc.get_active_layer()
        if not layer: 
            print("DEBUG: No active layer")
            return
        
        print(f"DEBUG: Opening dialog for layer {layer.name}")
        try:
            from .dialogs.layer_properties import LayerPropertiesDialog
            print("DEBUG: Import successful")
            dlg = LayerPropertiesDialog(self, layer)
            if dlg.exec():
                print("DEBUG: Dialog accepted")
                name, opacity, blend_mode = dlg.get_values()

            
                print("DEBUG: Dialog accepted")
                name, opacity, blend_mode = dlg.get_values()
                
                # Check changes
                if layer.name == name and abs(layer.opacity - opacity) < 0.01 and layer.blend_mode == blend_mode:
                    return
                
                cmd = MacroCommand("Layer Properties")
                
                # Name
                if layer.name != name:
                    pass # TODO: Command for rename? Or just property command handles it?
                    # LayerPropertyCommand handles name, opacity, blend_mode
                
                from ..core.commands import LayerPropertyCommand
                cmd.add_command(LayerPropertyCommand(layer, name, opacity, blend_mode))
                
                doc.history.push(cmd)
                cmd.execute()
        except Exception as e:
            print(f"DEBUG: Error in open_layer_properties: {e}")
            import traceback
            traceback.print_exc()
                

    def run_effect(self, effect_cls):
        doc = self.active_document()
        if not doc: return
        
        layer = doc.get_active_layer()
        if not layer: return
        
        # Instantiate
        effect = effect_cls()
        
        # Dialog
        config = {}
        dlg = effect.create_dialog(self)
        if dlg:
            if dlg.exec():
                config = dlg.get_config()
            else:
                return # Cancelled
        
        # Show progress dialog
        progress = QProgressDialog(f"Applying {effect.name}...", "Please wait", 0, 0, self)
        progress.setWindowModality(Qt.WindowModal)
        progress.setCancelButton(None)  # Can't cancel mid-operation
        progress.show()
        QApplication.processEvents()
        
        # Execute synchronously but with UI update
        try:
            # Copy image for processing (safer for memory)
            src_image = layer.image.copy()
            
            # Apply effect
            new_img = effect.apply(src_image, config)
            
            if new_img and not new_img.isNull():
                # Create undo command
                cmd = CanvasCommand(layer)
                layer.image = new_img
                cmd.capture_after()
                doc.history.push(cmd)
                doc.content_changed.emit()
            else:
                QMessageBox.warning(self, "Effect Error", f"Effect {effect.name} returned invalid image")
        except Exception as e:
            QMessageBox.critical(self, "Effect Error", f"Effect failed: {e}")
            import traceback
            traceback.print_exc()
        finally:
            progress.close()

    def keyPressEvent(self, event):
        """Handle global keyboard shortcuts."""
        if event.key() == Qt.Key.Key_X and not event.modifiers():
            print("DEBUG: X pressed via keyPressEvent!")
            self.session.swap_colors()
            event.accept()
            return
        super().keyPressEvent(event)

    def closeEvent(self, event):
        # Save Settings
        self.settings.set_value("window/geometry", self.saveGeometry())
        super().closeEvent(event)

    def update_recents_menu(self):
        self.recents_menu.clear()
        recents = self.settings.get_recent_files()
        for path in recents:
            action = QAction(os.path.basename(path), self)
            action.triggered.connect(partial(self.open_project, path))
            self.recents_menu.addAction(action)

    def change_theme(self, theme_name):
        self.settings.set_value("theme", theme_name)
        ThemeManager.apply_theme(QApplication.instance(), theme_name)

    def show_startup_screen(self):
        dlg = StartupScreen(self)
        
        def on_open(path):
            if path:
                self.open_project(path)
            else:
                self.open_project() # Trigger dialog
                
        dlg.open_file.connect(on_open)
        dlg.new_file.connect(self.new_document)
        
        dlg.exec()

    def feather_selection(self):
        """Open dialog to feather selection."""
        doc = self.active_document()
        if not doc or not doc.has_selection:
            return
        from PySide6.QtWidgets import QInputDialog
        radius, ok = QInputDialog.getInt(self, "Feather Selection", "Radius (pixels):", 5, 1, 100)
        if ok:
            doc.feather_selection(radius)
            if self.active_canvas():
                self.active_canvas().update()

    def expand_selection(self):
        """Open dialog to expand selection."""
        doc = self.active_document()
        if not doc or not doc.has_selection:
            return
        from PySide6.QtWidgets import QInputDialog
        amount, ok = QInputDialog.getInt(self, "Expand Selection", "Amount (pixels):", 5, 1, 100)
        if ok:
            doc.expand_selection(amount)
            if self.active_canvas():
                self.active_canvas().update()

    def contract_selection(self):
        """Open dialog to contract selection."""
        doc = self.active_document()
        if not doc or not doc.has_selection:
            return
        from PySide6.QtWidgets import QInputDialog
        amount, ok = QInputDialog.getInt(self, "Contract Selection", "Amount (pixels):", 5, 1, 100)
        if ok:
            doc.contract_selection(amount)
            if self.active_canvas():
                self.active_canvas().update()
