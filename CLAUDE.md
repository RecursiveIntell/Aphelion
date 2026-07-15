# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Aphelion is a professional, layer-based image editor for Linux built with Python 3.10+ and PySide6. It provides Paint.NET-like functionality with 49 image effects, 21 tools, and extensive file format support. The rendering backend uses PyCairo for accurate layer compositing.

## Commands

```bash
# Run the application
./run.sh
# OR
export PYTHONPATH=src && python3 -m aphelion

# Run all tests
python verify_all.py

# Run individual test files
python test_cairo_renderer.py
python test_canvas.py
python test_image_processing.py
python test_io.py
python test_tools.py
```

## Architecture

### Core Components (src/aphelion/core/)
- **Document**: Layer container with selection mask, uses CairoRenderer for compositing
- **Layer**: Image data (Format_ARGB32_Premultiplied) with optional mask, blend mode, opacity
- **HistoryManager**: Command-based undo/redo with 500MB memory limit
- **Session**: Global state (active tool, colors, brush size, edit target)
- **CairoRenderer**: Layer compositing engine using NumPy and Cairo

### UI Components (src/aphelion/ui/)
- **MainWindow**: Central hub with tabs, menus, docking panels
- **CanvasWidget**: Drawing surface with zoom/pan and tool event routing
- **Panels**: ToolsDock, ColorsPanel, HistoryPanel, LayerPanel

### Key Patterns

**Command Pattern for Undo/Redo:**
```python
cmd = CanvasCommand(layer, target="image")
# ... make changes ...
cmd.capture_after()
self.document.history.push(cmd)
```

**Effect Implementation:**
```python
class MyEffect(Effect):
    def apply(self, image: QImage, config: dict) -> QImage:
        # Process image
        return result
```

**Tool Implementation:**
```python
class MyTool(Tool):
    def mouse_press(self, event, canvas): ...
    def mouse_move(self, event, canvas): ...
    def mouse_release(self, event, canvas): ...
```

### Adding New Effects
1. Create class inheriting from `Effect` in effects/
2. Implement `apply(image, config)` and optionally `create_dialog(parent)`
3. Register in `effects/__init__.py` via `register_all_effects()`

### Adding New Tools
1. Create class inheriting from `Tool` in tools/
2. Implement mouse event handlers, use `CanvasCommand` for undo
3. Register in `ui/panels/tools_dock.py`

## File Formats
- **Project**: `.aphelion` (ZIP with manifest.json + layer PNGs)
- **Import/Export**: PNG, JPEG, WebP, TIFF, BMP, GIF, TGA, ICO, PPM, SVG

## Plugin System
Plugins in `./plugins/` or `~/.aphelion/plugins/` are auto-discovered. Inherit from `AphelionPlugin` and implement `initialize(context)`.

## Dependencies
PySide6, NumPy, SciPy, PyCairo
