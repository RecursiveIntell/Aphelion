# Aphelion Plugin Development Guide

Aphelion supports plugins to extend functionality with new Effects and Tools.

## Plugin Structure

A plugin can be a single `.py` file or a directory with an `__init__.py`.
All plugins must contain a class inheriting from `src.core.plugins.AphelionPlugin`.

### Example `sepia.py`

```python
from src.core.plugins import AphelionPlugin, PluginType
from src.core.effects import Effect
from PySide6.QtGui import QImage

class MyEffect(Effect):
    name = "My Effect"
    category = "Custom"
    
    def apply(self, image: QImage, config: dict) -> QImage:
        # Return modified QImage
        return image.copy()

class MyPlugin(AphelionPlugin):
    name = "My Plugin"
    version = "1.0"
    type = PluginType.EFFECT
    
    def initialize(self, context):
        registry = context.get("EffectRegistry")
        if registry:
            registry.register(MyEffect)
```

## Plugin Types

- **EFFECT**: Image filters and adjustments.
- **TOOL**: Canvas tools (Brush, Select, etc.). (Support in progress)
- **GENERAL**: Other extensions.

## Context

The `initialize(context)` method provides:
- `EffectRegistry`: Register `Effect` subclasses.
- `register_tool`: Logic to add tools (coming soon).

## Deployment

Place your `.py` file in the `plugins/` directory. Aphelion loads them on startup.
