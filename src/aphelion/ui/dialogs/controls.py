"""
Generic dialog control system for Aphelion effects.

Provides declarative UI controls that can be automatically generated into dialogs.
"""
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Optional, Union
from PySide6.QtGui import QColor


class ControlType(Enum):
    """Types of controls available in dialogs."""
    SLIDER = auto()
    SPINBOX = auto()
    CHECKBOX = auto()
    COMBOBOX = auto()
    COLOR_PICKER = auto()
    DOUBLE_SPINBOX = auto()


@dataclass(slots=True, frozen=True)
class DialogControl:
    """
    Declarative definition of a dialog control.

    Attributes:
        key: Configuration key for this control's value
        label: Display label shown in the dialog
        control_type: Type of control to render
        default: Default value
        min_val: Minimum value (for sliders/spinboxes)
        max_val: Maximum value (for sliders/spinboxes)
        step: Step size (for double spinbox)
        options: List of options (for combobox)
        tooltip: Optional tooltip text
    """
    key: str
    label: str
    control_type: ControlType
    default: Any
    min_val: Optional[Union[int, float]] = None
    max_val: Optional[Union[int, float]] = None
    step: Optional[float] = None
    options: Optional[tuple[str, ...]] = None
    tooltip: Optional[str] = None

    def __post_init__(self):
        """Validate control configuration."""
        if self.control_type in (ControlType.SLIDER, ControlType.SPINBOX, ControlType.DOUBLE_SPINBOX):
            if self.min_val is None or self.max_val is None:
                raise ValueError(f"Control '{self.key}' requires min_val and max_val")

        if self.control_type == ControlType.COMBOBOX:
            if not self.options or len(self.options) == 0:
                raise ValueError(f"ComboBox control '{self.key}' requires options")


def create_slider_control(
    key: str,
    label: str,
    default: int,
    min_val: int,
    max_val: int,
    tooltip: Optional[str] = None
) -> DialogControl:
    """Helper to create a slider control."""
    return DialogControl(
        key=key,
        label=label,
        control_type=ControlType.SLIDER,
        default=default,
        min_val=min_val,
        max_val=max_val,
        tooltip=tooltip
    )


def create_checkbox_control(
    key: str,
    label: str,
    default: bool = False,
    tooltip: Optional[str] = None
) -> DialogControl:
    """Helper to create a checkbox control."""
    return DialogControl(
        key=key,
        label=label,
        control_type=ControlType.CHECKBOX,
        default=default,
        tooltip=tooltip
    )


def create_combobox_control(
    key: str,
    label: str,
    options: tuple[str, ...],
    default: str,
    tooltip: Optional[str] = None
) -> DialogControl:
    """Helper to create a combobox control."""
    return DialogControl(
        key=key,
        label=label,
        control_type=ControlType.COMBOBOX,
        default=default,
        options=options,
        tooltip=tooltip
    )


def create_double_spinbox_control(
    key: str,
    label: str,
    default: float,
    min_val: float,
    max_val: float,
    step: float = 0.1,
    tooltip: Optional[str] = None
) -> DialogControl:
    """Helper to create a double spinbox control."""
    return DialogControl(
        key=key,
        label=label,
        control_type=ControlType.DOUBLE_SPINBOX,
        default=default,
        min_val=min_val,
        max_val=max_val,
        step=step,
        tooltip=tooltip
    )
