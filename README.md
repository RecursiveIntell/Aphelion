# Aphelion Image Editor

**Aphelion** is a professional, layer-based image editor for Linux, built with Python and PySide6. It provides Paint.NET-like functionality with **49 image effects**, **21 tools**, and extensive file format support.

## ✨ Features

### 🎨 Tools (21)
| Category | Tools |
|----------|-------|
| **Selection** | Rectangle, Ellipse, Lasso, Magic Wand |
| **Drawing** | Brush, Pencil, Eraser (pressure sensitive), **Smudge** |
| **Shapes** | Line, Curve, Rectangle, Ellipse |
| **Fill** | Paint Bucket, Gradient (Linear, Radial, Conical, Diamond, Reflected) |
| **Retouching** | Clone Stamp, Recolor |
| **Utility** | Text, Color Picker, Zoom, Move Selected Pixels |

### 🖼️ Effects (49)
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
- **Layer System**: Unlimited layers with blend modes, opacity, and masks.
- **Visual Thumbnails**: Real-time layer previews.
- **Selection Tools**: Advance operations like **Feather**, **Expand**, **Contract**, Invert.
- **Undo/Redo**: Full history with visual timeline.
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
pip install PySide6 numpy scipy

# Run
./run.sh
# OR
export PYTHONPATH=src
python3 -m aphelion
```

## 🔌 Plugin Development

Aphelion supports plugins for adding custom effects and tools.

**Plugin locations:**
- `./plugins/` (project directory)
- `~/.aphelion/plugins/` (user directory)

See [PLUGIN_DEV.md](PLUGIN_DEV.md) for development guide.

**Included plugins:**
- Sepia Filter
- Star Stamp Tool

## 🧪 Testing

```bash
# Run all verification tests
python verify_all.py
```

## 📋 Requirements

- Python 3.10+
- PySide6
- NumPy, SciPy
- Linux (tested on Fedora/Nobara)

## 📄 License

MIT License

---

*Aphelion - A professional image editor for Linux*
