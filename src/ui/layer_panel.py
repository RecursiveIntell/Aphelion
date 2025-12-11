from PySide6.QtWidgets import (QWidget, QVBoxLayout, QListWidget, QPushButton, QHBoxLayout, 
                               QListWidgetItem, QCheckBox, QSlider, QComboBox, QLabel, QMenu, QInputDialog)
from PySide6.QtGui import QPainter, QAction, QCursor
from PySide6.QtCore import Qt
from ..core.document import Document
from ..core.layer import Layer
from ..core.commands import LayerPropertyCommand, LayerStructureCommand

BLK_MODES = {
    "Normal": QPainter.CompositionMode.CompositionMode_SourceOver,
    "Multiply": QPainter.CompositionMode.CompositionMode_Multiply,
    "Screen": QPainter.CompositionMode.CompositionMode_Screen,
    "Overlay": QPainter.CompositionMode.CompositionMode_Overlay,
    "Darken": QPainter.CompositionMode.CompositionMode_Darken,
    "Lighten": QPainter.CompositionMode.CompositionMode_Lighten,
    "Color Dodge": QPainter.CompositionMode.CompositionMode_ColorDodge,
    "Color Burn": QPainter.CompositionMode.CompositionMode_ColorBurn,
    "Hard Light": QPainter.CompositionMode.CompositionMode_HardLight,
    "Soft Light": QPainter.CompositionMode.CompositionMode_SoftLight,
    "Difference": QPainter.CompositionMode.CompositionMode_Difference,
    "Exclusion": QPainter.CompositionMode.CompositionMode_Exclusion,
    # Add more as needed
}

MODE_NAMES = {v: k for k, v in BLK_MODES.items()}

class LayerPanel(QWidget):
    def __init__(self, document: Document, session):
        super().__init__()
        self.document = document
        self.session = session
        
        self.layout = QVBoxLayout()
        
        # Controls Row 1
        ctrl_layout = QHBoxLayout()
        
        self.combo_mode = QComboBox()
        self.combo_mode.addItems(BLK_MODES.keys())
        self.combo_mode.currentTextChanged.connect(self.on_blend_mode_changed)
        ctrl_layout.addWidget(self.combo_mode)
        
        self.btn_props = QPushButton("...")
        self.btn_props.setFixedSize(30, 25)
        self.btn_props.clicked.connect(self.open_properties)
        ctrl_layout.addWidget(self.btn_props)
        ctrl_layout.addWidget(self.btn_props)
        
        self.chk_edit_mask = QCheckBox("Edit Mask")
        self.chk_edit_mask.clicked.connect(self.on_edit_mask_toggled)
        ctrl_layout.addWidget(self.chk_edit_mask)
        
        self.layout.addLayout(ctrl_layout)
        
        # Controls Row 2: Opacity
        op_layout = QHBoxLayout()
        op_layout.addWidget(QLabel("Opacity:"))
        self.slider_opacity = QSlider(Qt.Horizontal)
        self.slider_opacity.setRange(0, 255)
        self.slider_opacity.setValue(255)
        self.slider_opacity.valueChanged.connect(self.on_opacity_changed)
        op_layout.addWidget(self.slider_opacity)
        self.layout.addLayout(op_layout)
        
        # Tools (Add/Remove/Dup/Merge)
        self.button_layout = QHBoxLayout()
        self.btn_add = QPushButton("+")
        self.btn_add.setToolTip("Add New Layer")
        self.btn_add.clicked.connect(self.on_add)
        
        self.btn_remove = QPushButton("-")
        self.btn_remove.setToolTip("Delete Layer")
        self.btn_remove.clicked.connect(self.on_remove)
        
        self.btn_dup = QPushButton("Dup")
        self.btn_dup.clicked.connect(self.on_duplicate)
        
        self.btn_up = QPushButton("▲")
        self.btn_up.setFixedSize(25, 25)
        self.btn_up.clicked.connect(self.on_move_up)
        
        self.btn_down = QPushButton("▼")
        self.btn_down.setFixedSize(25, 25)
        self.btn_down.clicked.connect(self.on_move_down)
        
        self.btn_merge = QPushButton("M")
        self.btn_merge.setToolTip("Merge Down")
        self.btn_merge.clicked.connect(self.on_merge_down)
        
        self.button_layout.addWidget(self.btn_add)
        self.button_layout.addWidget(self.btn_remove)
        self.button_layout.addWidget(self.btn_up)
        self.button_layout.addWidget(self.btn_down)
        self.button_layout.addWidget(self.btn_dup)
        self.button_layout.addWidget(self.btn_merge)
        self.layout.addLayout(self.button_layout)
        
        # List
        self.list_widget = QListWidget()
        self.list_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self.show_context_menu)
        self.list_widget.itemChanged.connect(self.on_item_changed) # For checkbox
        self.list_widget.itemDoubleClicked.connect(self.on_double_click)
        self.list_widget.currentRowChanged.connect(self.on_row_changed)
        self.layout.addWidget(self.list_widget)
        
        self.setLayout(self.layout)
        
        if self.document:
            # Subscribe
            self.document.layer_added.connect(self.refresh)
            self.document.layer_removed.connect(lambda l: self.refresh())
            self.refresh()
            
    def set_document(self, document: Document):
         self.document = document
         self.list_widget.clear()
         if self.document:
             self.document.layer_added.connect(self.refresh)
             self.document.layer_removed.connect(lambda l: self.refresh())
             self.refresh()

    def refresh(self):
        self.list_widget.clear()
        # Document layers are bottom to top (0..N).
        # List widget should probably show Top to Bottom?
        # Usually Layer panel shows Top layer at Top.
        # So we iterate reversed.
        
        for i in range(len(self.document.layers) - 1, -1, -1):
            layer = self.document.layers[i]
            item = QListWidgetItem(self.list_widget)
            if layer.is_adjustment:
                item.setText(f"⚡ {layer.name}")
                font = item.font()
                font.setItalic(True)
                item.setFont(font)
            else:
                name = layer.name
                if layer.mask:
                    name += " [Mask]"
                item.setText(name)
                
            item.setCheckState(Qt.CheckState.Checked if layer.visible else Qt.CheckState.Unchecked)
            # Associating data? 
            # We can use item.setData(Qt.UserRole, i) for index logic
            item.setData(Qt.UserRole, i)
            
        # Restore selection
        # active_index = self.document._active_layer_index
        # But list is reversed. 
        # index 0 in list = index N-1 in doc.
        # list_index = (N-1) - doc_index
        self.update_selection_from_model()

    def update_selection_from_model(self):
         doc_index = self.document._active_layer_index
         if doc_index != -1:
             count = len(self.document.layers)
             list_index = (count - 1) - doc_index
             list_index = (count - 1) - doc_index
             self.list_widget.setCurrentRow(list_index)
             self.update_controls()

    def on_blend_mode_changed(self, text):
        layer = self.document.get_active_layer()
        if not layer: return
        mode = BLK_MODES.get(text, QPainter.CompositionMode.CompositionMode_SourceOver)
        if layer.blend_mode != mode:
            # TODO: Command
            layer.blend_mode = mode
            self.document.content_changed.emit()

    def on_opacity_changed(self, value):
        layer = self.document.get_active_layer()
        if not layer: return
        if layer.opacity != value:
            # TODO: Command
            layer.opacity = value
            self.document.content_changed.emit()

    def update_controls(self):
        layer = self.document.get_active_layer()
        if not layer:
            self.slider_opacity.setEnabled(False)
            self.combo_mode.setEnabled(False)
            return

        self.slider_opacity.setEnabled(True)
        self.combo_mode.setEnabled(True)
        
        # Block signals
        self.slider_opacity.blockSignals(True)
        self.combo_mode.blockSignals(True)
        self.chk_edit_mask.blockSignals(True)
        
        self.slider_opacity.setValue(layer.opacity)
        mode_name = MODE_NAMES.get(layer.blend_mode, "Normal")
        self.combo_mode.setCurrentText(mode_name)
        
        # Mask Controls
        if layer.mask:
            self.chk_edit_mask.setEnabled(True)
            is_mask_target = (self.session.edit_target == "mask")
            self.chk_edit_mask.setChecked(is_mask_target)
        else:
            self.chk_edit_mask.setEnabled(False)
            self.chk_edit_mask.setChecked(False)
            if self.session.edit_target == "mask":
                self.session.edit_target = "image"
        
        self.slider_opacity.blockSignals(False)
        self.combo_mode.blockSignals(False)
        self.chk_edit_mask.blockSignals(False)

    def on_row_changed(self, row):
        if row == -1: return
        # Convert list row (reversed) to doc index
        count = len(self.document.layers)
        doc_index = (count - 1) - row
        self.document.set_active_layer(doc_index)
        self.update_controls()

    def on_item_changed(self, item):
        # Checkbox toggled
        row = self.list_widget.row(item)
        count = len(self.document.layers)
        doc_index = (count - 1) - row
        layer = self.document.layers[doc_index]
        visible = (item.checkState() == Qt.CheckState.Checked)
        if layer.visible != visible:
            layer.visible = visible
            self.document.content_changed.emit()

    def on_double_click(self, item):
        self.rename_layer()

    def rename_layer(self):
        layer = self.document.get_active_layer()
        if not layer: return
        name, ok = QInputDialog.getText(self, "Rename Layer", "Name:", text=layer.name)
        if ok and name:
            layer.name = name
            self.refresh() # Update label
            
    def show_context_menu(self, pos):
        menu = QMenu()
        menu.addAction("Rename", self.rename_layer)
        menu.addAction("Duplicate", self.on_duplicate)
        menu.addAction("Merge Down", self.on_merge_down)
        menu.addSeparator()
        
        # Mask Actions
        layer = self.document.get_active_layer()
        if layer and not layer.mask:
            menu.addAction("Add Mask", self.on_add_mask)
        elif layer and layer.mask:
            menu.addAction("Delete Mask", self.on_delete_mask)
            
        menu.addSeparator()
        menu.addAction("Delete", self.on_remove)
        menu.addAction("Properties...", self.open_properties)
        menu.exec(self.list_widget.mapToGlobal(pos))
        
    def on_add_mask(self):
        layer = self.document.get_active_layer()
        if layer:
            layer.create_mask()
            self.refresh()
            self.document.content_changed.emit()
            
    def on_delete_mask(self):
        layer = self.document.get_active_layer()
        if layer:
            layer.delete_mask()
             # If we were editing mask, switch back to image
            if self.session.edit_target == "mask":
                self.session.edit_target = "image"
            self.refresh()
            self.document.content_changed.emit()

    def on_edit_mask_toggled(self):
        # Update session
        target = "mask" if self.chk_edit_mask.isChecked() else "image"
        # Only allow setting to mask if mask exists
        layer = self.document.get_active_layer()
        if target == "mask" and (not layer or not layer.mask):
            self.chk_edit_mask.setChecked(False)
            target = "image"
            
        self.session.edit_target = target
        
    def open_properties(self):
        layer = self.document.get_active_layer()
        if not layer: return
        
        if layer.is_adjustment:
            # Open Effect Dialog
            effect = layer.effect_cls()
            dlg = effect.create_dialog(self)
            if dlg:
                # Load current config
                # Dialogs usually init with defaults. We might need a way to set config.
                # Since our EffectDialogs are simple getters, we might need a set_config or init arg.
                # For MVP, just opening it resets to default or we patch it manually if we knew the fields.
                # Let's assume user wants to edit settings from scratch or we enhance Dialogs later to load.
                # Actually, see adjustments.py, they init to 0. 
                # Let's just run it.
                if dlg.exec():
                    new_config = dlg.get_config()
                    layer.config = new_config
                    self.document.content_changed.emit()
        else:
            # Image Layer Properties (Opacity, Blend - already in panel)
            # Maybe show a dialog for Name, Opacity, Blend Mode?
            pass

    def on_add(self):
        self.document.add_layer()
        self.refresh()

    def on_remove(self):
        index = self.document._active_layer_index
        self.document.delete_layer(index)
        self.refresh()

    def on_duplicate(self):
        index = self.document._active_layer_index
        self.document.duplicate_layer(index)
        self.refresh()
        
    def on_merge_down(self):
        index = self.document._active_layer_index
        self.document.merge_layer_down(index)
        self.refresh()

    def on_move_up(self):
        self.document.move_layer_up()
        self.refresh()

    def on_move_down(self):
        self.document.move_layer_down()
        self.refresh()
