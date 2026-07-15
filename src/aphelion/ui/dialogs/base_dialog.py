"""
Generic configuration dialog builder for Aphelion effects.

Automatically generates dialogs from declarative control definitions.
"""
from typing import Dict, List, Any
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QSlider,
    QSpinBox, QDoubleSpinBox, QCheckBox, QComboBox,
    QDialogButtonBox, QPushButton, QColorDialog
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from .controls import DialogControl, ControlType


class ConfigDialog(QDialog):
    """
    Auto-generated configuration dialog from control definitions.

    This class eliminates the need for per-effect dialog code by
    automatically generating UI from declarative control definitions.

    Example:
        controls = [
            DialogControl("radius", "Radius:", ControlType.SLIDER, 10, 1, 100),
            DialogControl("strength", "Strength:", ControlType.SLIDER, 50, 0, 100),
        ]
        dialog = ConfigDialog("My Effect", controls, parent)
        if dialog.exec():
            config = dialog.get_config()
    """

    def __init__(
        self,
        title: str,
        controls: List[DialogControl],
        parent=None
    ):
        """
        Initialize the dialog.

        Args:
            title: Dialog window title
            controls: List of DialogControl definitions
            parent: Parent widget
        """
        super().__init__(parent)
        self.setWindowTitle(title)
        self.controls = controls
        self._widgets: Dict[str, Any] = {}
        self._value_labels: Dict[str, QLabel] = {}

        self._build_ui()

    def _build_ui(self):
        """Build the dialog UI from control definitions."""
        layout = QVBoxLayout()

        for control in self.controls:
            control_widget = self._create_control_widget(control)
            if control_widget:
                layout.addLayout(control_widget)

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def _create_control_widget(self, control: DialogControl):
        """
        Create a widget for a single control.

        Args:
            control: DialogControl definition

        Returns:
            QHBoxLayout containing the control and label
        """
        h_layout = QHBoxLayout()

        match control.control_type:
            case ControlType.SLIDER:
                return self._create_slider(control, h_layout)
            case ControlType.SPINBOX:
                return self._create_spinbox(control, h_layout)
            case ControlType.DOUBLE_SPINBOX:
                return self._create_double_spinbox(control, h_layout)
            case ControlType.CHECKBOX:
                return self._create_checkbox(control, h_layout)
            case ControlType.COMBOBOX:
                return self._create_combobox(control, h_layout)
            case ControlType.COLOR_PICKER:
                return self._create_color_picker(control, h_layout)
            case _:
                return None

    def _create_slider(self, control: DialogControl, h_layout: QHBoxLayout):
        """Create a slider control."""
        h_layout.addWidget(QLabel(f"{control.label}"))

        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(int(control.min_val), int(control.max_val))
        slider.setValue(int(control.default))
        h_layout.addWidget(slider)

        # Value label
        value_label = QLabel(str(control.default))
        slider.valueChanged.connect(lambda v: value_label.setText(str(v)))
        h_layout.addWidget(value_label)

        self._widgets[control.key] = slider
        self._value_labels[control.key] = value_label

        if control.tooltip:
            slider.setToolTip(control.tooltip)

        return h_layout

    def _create_spinbox(self, control: DialogControl, h_layout: QHBoxLayout):
        """Create a spinbox control."""
        h_layout.addWidget(QLabel(f"{control.label}"))

        spinbox = QSpinBox()
        spinbox.setRange(int(control.min_val), int(control.max_val))
        spinbox.setValue(int(control.default))
        h_layout.addWidget(spinbox)

        self._widgets[control.key] = spinbox

        if control.tooltip:
            spinbox.setToolTip(control.tooltip)

        return h_layout

    def _create_double_spinbox(self, control: DialogControl, h_layout: QHBoxLayout):
        """Create a double spinbox control."""
        h_layout.addWidget(QLabel(f"{control.label}"))

        spinbox = QDoubleSpinBox()
        spinbox.setRange(float(control.min_val), float(control.max_val))
        spinbox.setValue(float(control.default))
        if control.step:
            spinbox.setSingleStep(control.step)
        h_layout.addWidget(spinbox)

        self._widgets[control.key] = spinbox

        if control.tooltip:
            spinbox.setToolTip(control.tooltip)

        return h_layout

    def _create_checkbox(self, control: DialogControl, h_layout: QHBoxLayout):
        """Create a checkbox control."""
        checkbox = QCheckBox(control.label)
        checkbox.setChecked(bool(control.default))
        h_layout.addWidget(checkbox)

        self._widgets[control.key] = checkbox

        if control.tooltip:
            checkbox.setToolTip(control.tooltip)

        return h_layout

    def _create_combobox(self, control: DialogControl, h_layout: QHBoxLayout):
        """Create a combobox control."""
        h_layout.addWidget(QLabel(f"{control.label}"))

        combobox = QComboBox()
        combobox.addItems(control.options)
        if control.default in control.options:
            combobox.setCurrentText(control.default)
        h_layout.addWidget(combobox)

        self._widgets[control.key] = combobox

        if control.tooltip:
            combobox.setToolTip(control.tooltip)

        return h_layout

    def _create_color_picker(self, control: DialogControl, h_layout: QHBoxLayout):
        """Create a color picker control."""
        h_layout.addWidget(QLabel(f"{control.label}"))

        color_button = QPushButton()
        initial_color = control.default if isinstance(control.default, QColor) else QColor(255, 255, 255)
        color_button.setStyleSheet(f"background-color: {initial_color.name()};")
        color_button.setFixedSize(50, 30)

        def pick_color():
            color = QColorDialog.getColor(initial_color, self, control.label)
            if color.isValid():
                color_button.setStyleSheet(f"background-color: {color.name()};")
                self._widgets[control.key] = color

        color_button.clicked.connect(pick_color)
        h_layout.addWidget(color_button)

        self._widgets[control.key] = initial_color

        if control.tooltip:
            color_button.setToolTip(control.tooltip)

        return h_layout

    def get_config(self) -> Dict[str, Any]:
        """
        Get the current configuration from all controls.

        Returns:
            Dictionary mapping control keys to their current values
        """
        config = {}

        for control in self.controls:
            widget = self._widgets.get(control.key)
            if widget is None:
                continue

            match control.control_type:
                case ControlType.SLIDER:
                    config[control.key] = widget.value()
                case ControlType.SPINBOX:
                    config[control.key] = widget.value()
                case ControlType.DOUBLE_SPINBOX:
                    config[control.key] = widget.value()
                case ControlType.CHECKBOX:
                    config[control.key] = widget.isChecked()
                case ControlType.COMBOBOX:
                    config[control.key] = widget.currentText()
                case ControlType.COLOR_PICKER:
                    if isinstance(widget, QColor):
                        config[control.key] = widget
                    else:
                        config[control.key] = QColor(255, 255, 255)

        return config
