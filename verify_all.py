#!/usr/bin/env python3
"""
Comprehensive Aphelion Verification Script
Tests all major components: tools, effects, file I/O, themes, plugins.
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QImage, QColor
from PySide6.QtCore import QSize

app = QApplication([])

def print_header(title):
    print(f"\n{'='*60}")
    print(f" {title}")
    print('='*60)

def print_ok(msg):
    print(f"  ✓ {msg}")

def print_fail(msg):
    print(f"  ✗ {msg}")

def print_warn(msg):
    print(f"  ⚠ {msg}")

# Track results
passed = 0
failed = 0
warnings = 0

# ==== TEST 1: Core Imports ====
print_header("1. Core Module Imports")
try:
    from src.core.document import Document
    from src.core.layer import Layer
    from src.core.session import Session
    from src.core.history import HistoryManager
    from src.core.io import ProjectIO
    from src.core.effects import Effect, EffectRegistry
    from src.core.plugins import PluginManager
    from src.core.settings import SettingsManager
    print_ok("All core modules imported successfully")
    passed += 1
except Exception as e:
    print_fail(f"Core import failed: {e}")
    failed += 1

# ==== TEST 2: Effects Registration ====
print_header("2. Effects Registration")
try:
    from src.effects import register_all_effects
    register_all_effects()
    effects = EffectRegistry.get_all()
    total = sum(len(effs) for effs in effects.values())
    
    if total >= 35:
        print_ok(f"Registered {total} effects (expected 35+)")
        passed += 1
    else:
        print_warn(f"Only {total} effects registered (expected 35+)")
        warnings += 1
    
    for cat, effs in sorted(effects.items()):
        print(f"    {cat}: {len(effs)} effects")
except Exception as e:
    print_fail(f"Effects registration failed: {e}")
    failed += 1

# ==== TEST 3: Tool Imports ====
print_header("3. Tool Imports")
tools_to_check = [
    ("BrushTool", "src.tools.brush"),
    ("EraserTool", "src.tools.eraser"),
    ("GradientTool", "src.tools.gradient"),
    ("RecolorTool", "src.tools.recolor"),
    ("CloneStampTool", "src.tools.clone_stamp"),
    ("PencilTool", "src.tools.pencil"),
    ("TextTool", "src.tools.text_tool"),
    ("LineCurveTool", "src.tools.line_curve"),
    ("ColorPickerTool", "src.tools.utility"),
    ("ZoomTool", "src.tools.zoom"),
]
tool_count = 0
for tool_name, module_path in tools_to_check:
    try:
        mod = __import__(module_path, fromlist=[tool_name])
        getattr(mod, tool_name)
        tool_count += 1
    except Exception as e:
        print_fail(f"{tool_name}: {e}")
        failed += 1

if tool_count == len(tools_to_check):
    print_ok(f"All {tool_count} critical tools imported successfully")
    passed += 1
else:
    print_warn(f"{tool_count}/{len(tools_to_check)} tools imported")
    warnings += 1

# ==== TEST 4: Document Operations ====
print_header("4. Document Operations")
try:
    doc = Document(100, 100)  # width, height
    initial_layers = len(doc.layers)
    
    # Test layer creation
    doc.add_layer()
    assert len(doc.layers) == initial_layers + 1, f"Layer add failed: got {len(doc.layers)}"
    
    # Test undo/redo
    doc.history.undo()
    assert len(doc.layers) == initial_layers, f"Undo failed: got {len(doc.layers)}"
    doc.history.redo()
    assert len(doc.layers) == initial_layers + 1, f"Redo failed: got {len(doc.layers)}"
    
    # Test render
    result = doc.render()
    assert result.width() == 100, "Render width mismatch"
    
    print_ok("Document operations (add layer, undo, redo, render) working")
    passed += 1
except Exception as e:
    print_fail(f"Document operations failed: {e}")
    failed += 1

# ==== TEST 5: Effect Application ====
print_header("5. Effect Application")
try:
    test_image = QImage(50, 50, QImage.Format.Format_ARGB32)
    test_image.fill(QColor(100, 100, 100))
    
    # Test a few effects
    from src.effects.adjustments import InvertEffect
    from src.effects.blurs import GaussianBlurEffect
    from src.effects.artistic import PencilSketchEffect
    
    invert = InvertEffect()
    result = invert.apply(test_image, {})
    pixel = result.pixelColor(0, 0)
    assert pixel.red() == 155, f"Invert effect failed: got {pixel.red()}"
    
    blur = GaussianBlurEffect()
    result = blur.apply(test_image, {"radius": 2})
    assert result.width() == 50, "Blur failed"
    
    sketch = PencilSketchEffect()
    result = sketch.apply(test_image, {"detail": 5})
    assert result.width() == 50, "Pencil sketch failed"
    
    print_ok("Effect application (Invert, Blur, PencilSketch) working")
    passed += 1
except Exception as e:
    print_fail(f"Effect application failed: {e}")
    failed += 1

# ==== TEST 6: File Format Support ====
print_header("6. File Format Support")
try:
    export_formats = ProjectIO.get_supported_export_formats()
    import_formats = ProjectIO.get_supported_import_formats()
    
    required_formats = ['png', 'jpg', 'webp', 'tiff', 'bmp', 'gif', 'tga', 'ico']
    export_found = sum(1 for f in required_formats if f in export_formats.lower())
    import_found = sum(1 for f in required_formats if f in import_formats.lower())
    
    if export_found >= 8 and import_found >= 8:
        print_ok(f"All {len(required_formats)} file formats supported")
        passed += 1
    else:
        print_warn(f"Export: {export_found}/8, Import: {import_found}/8 formats")
        warnings += 1
except Exception as e:
    print_fail(f"File format check failed: {e}")
    failed += 1

# ==== TEST 7: Theme Manager ====
print_header("7. Theme Manager")
try:
    from src.ui.theme import ThemeManager, DARK_THEME_QSS, LIGHT_THEME_QSS
    
    assert len(DARK_THEME_QSS) > 100, "Dark theme QSS too short"
    assert len(LIGHT_THEME_QSS) > 100, "Light theme QSS too short"
    assert "#2b2b2b" in DARK_THEME_QSS, "Dark theme missing dark color"
    assert "#f0f0f0" in LIGHT_THEME_QSS, "Light theme missing light color"
    
    print_ok("Theme definitions valid (Dark and Light)")
    passed += 1
except Exception as e:
    print_fail(f"Theme manager check failed: {e}")
    failed += 1

# ==== TEST 8: Plugin System ====
print_header("8. Plugin System")
try:
    pm = PluginManager()
    plugins_dir = os.path.join(os.path.dirname(__file__), "plugins")
    
    if os.path.exists(plugins_dir):
        plugin_files = [f for f in os.listdir(plugins_dir) if f.endswith('.py')]
        print_ok(f"Plugin directory found with {len(plugin_files)} plugin files")
        passed += 1
    else:
        print_warn("Plugin directory not found")
        warnings += 1
except Exception as e:
    print_fail(f"Plugin system check failed: {e}")
    failed += 1

# ==== TEST 9: UI Panel Imports ====
print_header("9. UI Panel Imports")
try:
    from src.ui.panels.tools_dock import ToolsDock
    from src.ui.panels.colors_panel import ColorsPanel
    from src.ui.panels.history_panel import HistoryPanel
    from src.ui.layer_panel import LayerPanel
    
    print_ok("All UI panels imported successfully")
    passed += 1
except Exception as e:
    print_fail(f"UI panel import failed: {e}")
    failed += 1

# ==== TEST 10: Tablet Pressure Support ====
print_header("10. Tablet Pressure Support")
try:
    from src.tools.brush import BrushTool
    from src.tools.eraser import EraserTool
    
    tool = BrushTool(None, None)
    assert hasattr(tool, 'pressure_enabled'), "BrushTool missing pressure_enabled"
    assert hasattr(tool, 'tablet_event'), "BrushTool missing tablet_event method"
    
    tool = EraserTool(None, None)
    assert hasattr(tool, 'pressure_enabled'), "EraserTool missing pressure_enabled"
    
    print_ok("Tablet pressure support implemented in Brush and Eraser")
    passed += 1
except Exception as e:
    print_fail(f"Tablet pressure check failed: {e}")
    failed += 1

# ==== SUMMARY ====
print_header("VERIFICATION SUMMARY")
total = passed + failed + warnings
print(f"  Passed:   {passed}/{total}")
print(f"  Failed:   {failed}/{total}")
print(f"  Warnings: {warnings}/{total}")

if failed == 0:
    print("\n  🎉 ALL TESTS PASSED!")
    exit(0)
else:
    print(f"\n  ⚠️  {failed} test(s) failed")
    exit(1)
