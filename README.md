# Aphelion Image Editor
![Screenshot](https://github.com/RecursiveIntell/Aphelion/blob/main/Screenshot_20251211_121416.png)

**Aphelion** is a professional, layer-based image editor for Linux, built with Python and PySide6. It provides Paint.NET-like functionality with 35 image effects, 20 tools, and extensive file format support.

## ✨ Features

### 🎨 Tools (20)
| Category | Tools |
|----------|-------|
| **Selection** | Rectangle, Ellipse, Lasso, Magic Wand |
| **Drawing** | Brush, Pencil, Eraser (with tablet pressure) |
| **Shapes** | Line, Curve, Rectangle, Ellipse |
| **Fill** | Paint Bucket, Gradient (linear/radial) |
| **Retouching** | Clone Stamp, Recolor |
| **Utility** | Text, Color Picker, Zoom, Move |

### 🖼️ Effects (35)
| Category | Effects |
|----------|---------|
| **Adjustments** | Invert, Brightness/Contrast, Hue/Saturation, Auto Level, Sepia, Curves, Levels, Posterize, Black & White |
| **Blurs** | Gaussian, Sharpen, Motion, Radial, Zoom, Surface, Median |
| **Distort** | Pixelate, Bulge, Twist, Tile Reflection, Dents, Crystallize |
| **Stylize** | Emboss, Edge Detect, Outline, Fragment |
| **Artistic** | Oil Painting, Pencil Sketch, Ink Sketch |
| **Photo** | Vignette, Glow, Red Eye Removal |
| **Noise** | Add Noise, Reduce Noise |
| **Render** | Clouds |

### 📁 File Formats (11)
- **Import**: PNG, JPEG, WebP, TIFF, BMP, GIF, TGA, ICO, PPM, SVG
- **Export**: PNG, JPEG, WebP, TIFF, BMP, GIF, TGA, ICO, PPM
- **Project**: `.aphelion` (non-destructive layer preservation)

### 🎭 Additional Features
- **Layer System**: Unlimited layers with blend modes, opacity, and masks
- **Undo/Redo**: Full history with visual timeline
- **Plugin System**: Extend with Python scripts
- **Themes**: Light and Dark mode
- **Tablet Support**: Pressure sensitivity for Brush and Eraser

## 🚀 Quick Start

```bash
# Clone repository
git clone https://github.com/RecursiveIntell/Aphelion.git
cd Aphelion

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install PySide6

# Run
./run.sh
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
- Linux (tested on Fedora/Nobara)

## 📄 License

MIT License

---

*Aphelion - A professional image editor for Linux*
