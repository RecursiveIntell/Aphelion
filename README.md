# Aphelion Image Editor

**Aphelion** is a layer-based image editor for Linux, built with Python and PySide6. It includes drawing and selection tools, image effects, Cairo compositing, and a layered project format. The package version is maintained in [pyproject.toml](pyproject.toml).

## ✨ Features

### 🎨 Tools
| Category | Tools |
|----------|-------|
| **Selection** | Rectangle, Ellipse, Lasso, Magic Wand |
| **Drawing** | Brush, Pencil, Eraser (pressure sensitive), **Smudge** |
| **Shapes** | Line, Curve, Rectangle, Ellipse |
| **Fill** | Paint Bucket, Gradient (Linear, Radial, Conical, Diamond, Reflected) |
| **Retouching** | Clone Stamp, Recolor |
| **Utility** | Text, Color Picker, Zoom, Move Selected Pixels |

### 🖼️ Effects
| Category | Effects |
|----------|---------|
| **Adjustments** | Invert, Invert Alpha, Brightness/Contrast, Hue/Saturation, Auto Level, Sepia, Curves, Levels, Posterize, Black & White, **Color Balance** |
| **Blurs** | Gaussian, Sharpen, Motion, Radial, Zoom, Surface, Median, **Bokeh**, **Sketch**, **Unfocus** |
| **Distort** | Pixelate, Bulge, Twist, Tile Reflection, Dents, Crystallize, **3D Rotate/Zoom**, **Polar Inversion**, **Frosted Glass** |
| **Stylize** | Emboss, Edge Detect, Outline, Fragment, **Drop Shadow**, **Channel Shift**, **Relief** |
| **Artistic** | Oil Painting, Pencil Sketch, Ink Sketch |
| **Photo** | Vignette, Glow, Red Eye Removal |
| **Noise** | Add Noise, Reduce Noise |
| **Render** | Clouds, **Julia Fractal**, **Mandelbrot Fractal** |

### 📁 File Formats
- **Import**: PNG, JPEG, WebP, TIFF, BMP, GIF, TGA, ICO, PPM, SVG
- **Export**: PNG, JPEG, WebP, TIFF, BMP, GIF, TGA, ICO, PPM
- **Project**: `.aphelion` (non-destructive layer preservation)

### 🎭 Additional Features
- **Layer System**: Layers with blend modes, opacity, and masks. Practical document size depends on available memory.
- **Visual Thumbnails**: Real-time layer previews.
- **Selection Tools**: Advance operations like **Feather**, **Expand**, **Contract**, Invert.
- **Undo/Redo**: Command history with a visual timeline and a default 500 MiB memory budget; older undo entries can be evicted.
- **Plugin System**: Extend with Python scripts.
- **Themes**: Light and Dark mode.
- **Image Strip**: Paint.NET-style open document thumbnails.

## 🚀 Quick Start

```bash
# Clone repository
git clone https://github.com/RecursiveIntell/Aphelion.git
cd Aphelion

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
python -m pip install -e .

# Run the installed entry point
aphelion
# Or run from the source checkout
PYTHONPATH=src python -m aphelion
```

The optional `run.sh` launcher expects an environment named `venv` and forces Qt's `xcb` backend, so it needs an X11/XWayland session. The commands above avoid that launcher-specific requirement.

Raster format availability also depends on the Qt image plugins installed on the host. Save a layered `.aphelion` copy before exporting a flattened image.

## 🔌 Plugin Development

Aphelion supports plugins for adding custom effects and tools.

**Plugin locations:**
- `./plugins/` (project directory)
- `~/.aphelion/plugins/` (user directory)

See [PLUGIN_DEV.md](PLUGIN_DEV.md) for the development guide. Plugins execute Python in the application process; load only code you trust.

**Included plugins:**
- Sepia Filter
- Star Stamp Tool

## 🧪 Testing

```bash
# Run the bundled component verification script
python verify_all.py
```

`verify_all.py` checks selected imports, document operations, effects, formats, themes and plugins. It is not a complete GUI or file-compatibility suite. Individual `test_*.py` scripts provide additional checks. A Qt-capable environment is required; no desktop validation result is implied by this README.

## 📋 Requirements

- Python 3.10+
- PySide6
- NumPy, SciPy
- PyCairo (Cairo-based rendering backend)
- Linux desktop; Qt, Cairo and display-system dependencies must be available

### Installing PyCairo

```bash
# pip (usually works)
pip install pycairo

# Fedora/RHEL (if pip fails)
sudo dnf install cairo-devel

# Ubuntu/Debian (if pip fails)
sudo apt install libcairo2-dev
```

## 📄 License

MIT, as declared by the package metadata. This checkout does not include a standalone `LICENSE` file.
