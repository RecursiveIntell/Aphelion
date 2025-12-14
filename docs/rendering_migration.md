# Cairo Rendering Pipeline Migration

This document describes the architecture of Aphelion's Cairo-based rendering backend.

## Overview

The rendering pipeline has been migrated from Qt's `QPainter` to PyCairo for layer compositing. This provides a standardized vector graphics API with better control over compositing operations.

```
┌─────────────────────────────────────────────────────────────┐
│                    Document Rendering                        │
├─────────────────────────────────────────────────────────────┤
│  Layer.image (QImage)  →  CairoRenderer  →  QImage output   │
│     ARGB32_Pre            Cairo surfaces    for Qt display  │
└─────────────────────────────────────────────────────────────┘
```

## Pixel Format Contract

### Qt QImage
- Format: `Format_ARGB32_Premultiplied`
- Memory layout on little-endian: `BGRA` (Blue, Green, Red, Alpha)
- Alpha: Premultiplied (RGB values scaled by alpha)

### Cairo ImageSurface
- Format: `FORMAT_ARGB32`
- Memory layout on little-endian: `BGRA`
- Alpha: Premultiplied

### Key Insight
Both Qt and Cairo use the same memory layout on little-endian systems (x86, ARM). No channel reordering is needed for conversion—only stride handling.

## Conversion Utilities

Located in `core/renderer_cairo.py`:

| Function | Description |
|----------|-------------|
| `numpy_to_cairo_surface(arr)` | NumPy BGRA → Cairo surface |
| `cairo_surface_to_numpy(surface)` | Cairo surface → NumPy BGRA |
| `qimage_to_cairo_surface(img)` | QImage → Cairo surface |
| `cairo_surface_to_qimage(surface)` | Cairo surface → QImage |

### Stride Handling
Cairo surfaces require specific stride alignment (typically 4-byte). The conversions handle:
- Stride padding when needed
- Contiguous memory requirements
- Proper data copying to avoid dangling references

## Layer Compositing

### CairoRenderer Class

```python
class CairoRenderer:
    def render(self, document) -> cairo.ImageSurface
    def render_to_qimage(self, document) -> QImage
    def invalidate_layer(self, layer_id)
```

### Per-Layer Caching
- Each layer's QImage is converted to Cairo surface once
- Surfaces cached by layer ID with version tracking
- Cache invalidated when `Document.content_changed` fires

### Blend Mode Mapping

Cairo supports these Qt blend modes natively:

| Qt Mode | Cairo Operator |
|---------|----------------|
| SourceOver | `OPERATOR_OVER` |
| Multiply | `OPERATOR_MULTIPLY` |
| Screen | `OPERATOR_SCREEN` |
| Overlay | `OPERATOR_OVERLAY` |
| Darken | `OPERATOR_DARKEN` |
| Lighten | `OPERATOR_LIGHTEN` |
| ColorDodge | `OPERATOR_COLOR_DODGE` |
| ColorBurn | `OPERATOR_COLOR_BURN` |
| HardLight | `OPERATOR_HARD_LIGHT` |
| SoftLight | `OPERATOR_SOFT_LIGHT` |
| Difference | `OPERATOR_DIFFERENCE` |
| Exclusion | `OPERATOR_EXCLUSION` |

Unsupported modes fall back to `OPERATOR_OVER`.

## Integration Points

### Document.render()
Delegates to `CairoRenderer.render_to_qimage()`:

```python
def render(self, rect=None) -> QImage:
    return self._renderer.render_to_qimage(self)
```

### Cache Invalidation
Connected to `content_changed` signal:

```python
self.content_changed.connect(self._invalidate_render_cache)
```

### Tools
Tools continue to draw via `QPainter` to layer QImages. The Cairo cache is invalidated on changes, causing re-conversion on next render.

## Dependencies

- `pycairo>=1.20` - Python Cairo bindings
- System: `cairo` library (usually pre-installed on Linux)

### Installation

```bash
# Fedora/RHEL
sudo dnf install cairo-devel

# Ubuntu/Debian
sudo apt install libcairo2-dev

# pip (usually works without system deps)
pip install pycairo
```

## Performance Considerations

1. **Layer caching** reduces repeated QImage→Cairo conversions
2. **No extra copy** needed for pixel format (same memory layout)
3. **Display overhead**: Cairo→QImage conversion for Qt display (~1ms per frame for typical sizes)

## Future Enhancements

- [ ] Partial region rendering (`render_region`)
- [ ] Direct Cairo drawing for tools (bypass QPainter)
- [ ] GPU-accelerated Cairo backends
