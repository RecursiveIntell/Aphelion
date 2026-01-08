from PySide6.QtWidgets import (QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem, 
                               QPushButton, QHeaderView, QLabel, QHBoxLayout)
from PySide6.QtCore import Qt
from ..core.plugins import PluginManager

class PluginManagerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Plugin Manager")
        self.resize(600, 400)
        
        layout = QVBoxLayout()
        
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Enabled", "Name", "Version", "Author", "Description"])
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        layout.addWidget(self.table)
        
        btn_layout = QHBoxLayout()
        self.refresh_btn = QPushButton("Reload Plugins") # MVP: Might check folder again
        self.refresh_btn.clicked.connect(self.refresh_list)
        btn_layout.addWidget(self.refresh_btn)
        
        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self.close_btn)
        
        layout.addLayout(btn_layout)
        self.setLayout(layout)
        
        self.refresh_list()
        
    def refresh_list(self):
        manager = PluginManager()
        
        # Use new method to get all plugins (including disabled ones with metadata)
        all_plugins = manager.get_all_plugins()
        disabled_list = manager.settings.get_value("plugins/disabled", [])
        
        self.table.setRowCount(0)
        
        # Populate table with all discovered plugins
        for plugin in all_plugins:
            is_enabled = plugin.name not in disabled_list
            self._add_row(plugin, is_enabled)

    def _add_row(self, plugin, enabled):
        row = self.table.rowCount()
        self.table.insertRow(row)
        
        # Checkbox
        from PySide6.QtWidgets import QCheckBox, QWidget
        chk_widget = QWidget()
        chk = QCheckBox()
        chk.setChecked(enabled)
        chk.toggled.connect(lambda checked, p=plugin.name: self.on_plugin_toggled(p, checked))
        
        chk_layout = QHBoxLayout(chk_widget)
        chk_layout.addWidget(chk)
        chk_layout.setAlignment(Qt.AlignCenter)
        chk_layout.setContentsMargins(0,0,0,0)
        
        self.table.setCellWidget(row, 0, chk_widget)
        
        self.table.setItem(row, 1, QTableWidgetItem(plugin.name))
        self.table.setItem(row, 2, QTableWidgetItem(plugin.version))
        self.table.setItem(row, 3, QTableWidgetItem(plugin.author))
        self.table.setItem(row, 4, QTableWidgetItem(plugin.description))

    def on_plugin_toggled(self, name, checked):
        manager = PluginManager()
        manager.set_plugin_enabled(name, checked)
        # Inform user
        # QLabel in dialog or just implicit.
