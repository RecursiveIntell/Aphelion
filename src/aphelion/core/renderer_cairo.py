"""
Cairo-based rendering backend for Aphelion.

This module provides a Cairo-based renderer that composites layers
with correct opacity, blend modes, and alpha handling.

PIXEL FORMAT NOTES:
- Cairo ImageSurface FORMAT_ARGB32 uses native byte order, premultiplied alpha
- On little-endian (x86/ARM): memory layout is BGRA (same as Qt!)
- Qt Format_ARGB32_Premultiplied also uses BGRA on little-endian
- Both use premultiplied alpha, so no alpha conversion needed
- Channel order is the same on little-endian, so minimal conversion required
"""
import cairo
import numpy as np
from functools import lru_cache
from PySide6.QtGui import QImage, QPainter
from PySide6.QtCore import QSize
from typing import Dict, Optional, Tuple
from .logging import get_logger

logger = get_logger(__name__)


# =============================================================================
# Cairo ↔ NumPy ↔ QImage Conversion Utilities
# =============================================================================

def numpy_to_cairo_surface(arr: np.ndarray) -> cairo.ImageSurface:
    """
    Convert a NumPy array to a Cairo ImageSurface.
    
    Args:
        arr: Shape (height, width, 4) with BGRA order, dtype=uint8,
             MUST be premultiplied alpha.
             
    Returns:
        cairo.ImageSurface in FORMAT_ARGB32
        
    Note:
        Cairo FORMAT_ARGB32 on little-endian is stored as BGRA in memory,
        which matches Qt's Format_ARGB32_Premultiplied. No channel swap needed.
    """
    if arr.ndim != 3 or arr.shape[2] != 4:
        raise ValueError(f"Expected (H, W, 4) array, got {arr.shape}")
    
    height, width = arr.shape[:2]
    
    # Cairo requires specific stride alignment (usually 4-byte)
    stride = cairo.ImageSurface.format_stride_for_width(cairo.FORMAT_ARGB32, width)
    
    # If array stride matches Cairo stride, we can use it directly
    if arr.strides[0] == stride and arr.flags['C_CONTIGUOUS']:
        # Create surface from existing data (no copy if possible)
        data = arr.tobytes()
    else:
        # Need to create properly strided copy
        if stride == width * 4:
            # Simple case: no padding needed
            data = np.ascontiguousarray(arr).tobytes()
        else:
            # Need to add padding
            padded = np.zeros((height, stride // 4, 4), dtype=np.uint8)
            padded[:, :width, :] = arr
            data = padded.tobytes()
    
    surface = cairo.ImageSurface.create_for_data(
        bytearray(data), cairo.FORMAT_ARGB32, width, height, stride
    )
    
    # Mark surface as dirty to ensure Cairo knows about the data
    surface.mark_dirty()
    return surface


def cairo_surface_to_numpy(surface: cairo.ImageSurface) -> np.ndarray:
    """
    Convert a Cairo ImageSurface to a NumPy array.
    
    Args:
        surface: Cairo surface in FORMAT_ARGB32
        
    Returns:
        np.ndarray: Shape (height, width, 4) with BGRA order, dtype=uint8,
                    premultiplied alpha.
    """
    surface.flush()
    
    width = surface.get_width()
    height = surface.get_height()
    stride = surface.get_stride()
    
    # Get raw data buffer
    data = surface.get_data()
    
    # Create numpy array from buffer
    arr = np.frombuffer(data, dtype=np.uint8).reshape((height, stride // 4, 4))
    
    # Remove stride padding if present
    if stride != width * 4:
        arr = arr[:, :width, :].copy()
    else:
        arr = arr.copy()  # Make a copy since buffer may be invalidated
    
    return arr


def qimage_alpha8_to_cairo_surface(img: QImage) -> cairo.ImageSurface:
    """
    Convert an Alpha8 QImage (mask) to a Cairo ImageSurface.

    The alpha values become the alpha channel of an ARGB32 surface,
    which can then be used for masking operations.

    Args:
        img: QImage in Format_Alpha8

    Returns:
        cairo.ImageSurface in FORMAT_ARGB32 where alpha channel = mask values
    """
    if img.format() != QImage.Format.Format_Alpha8:
        img = img.convertToFormat(QImage.Format.Format_Alpha8)

    width = img.width()
    height = img.height()

    # Get alpha values from mask
    ptr = img.constBits()
    stride = img.bytesPerLine()
    alpha_arr = np.frombuffer(ptr, dtype=np.uint8).reshape((height, stride))
    alpha_arr = alpha_arr[:, :width].copy()

    # Create BGRA array with white color and mask alpha
    bgra = np.zeros((height, width, 4), dtype=np.uint8)
    bgra[:, :, 0] = 255  # B
    bgra[:, :, 1] = 255  # G
    bgra[:, :, 2] = 255  # R
    bgra[:, :, 3] = alpha_arr  # A = mask values

    # Premultiply alpha (white * alpha = alpha)
    bgra[:, :, 0] = alpha_arr
    bgra[:, :, 1] = alpha_arr
    bgra[:, :, 2] = alpha_arr

    return numpy_to_cairo_surface(bgra)


def qimage_to_cairo_surface(img: QImage) -> cairo.ImageSurface:
    """
    Convert a QImage to a Cairo ImageSurface.

    Args:
        img: QImage, will be converted to ARGB32_Premultiplied if needed

    Returns:
        cairo.ImageSurface in FORMAT_ARGB32
    """
    # Ensure correct format
    if img.format() != QImage.Format.Format_ARGB32_Premultiplied:
        img = img.convertToFormat(QImage.Format.Format_ARGB32_Premultiplied)
    
    width = img.width()
    height = img.height()
    
    # Get raw bytes from QImage
    ptr = img.constBits()
    qt_stride = img.bytesPerLine()
    
    # Convert to numpy array
    arr = np.frombuffer(ptr, dtype=np.uint8).reshape((height, qt_stride // 4, 4))
    
    # Extract just the image width (remove Qt's stride padding)
    if qt_stride != width * 4:
        arr = arr[:, :width, :].copy()
    else:
        arr = arr.copy()
    
    return numpy_to_cairo_surface(arr)


def cairo_surface_to_qimage(surface: cairo.ImageSurface) -> QImage:
    """
    Convert a Cairo ImageSurface to a QImage.
    
    Args:
        surface: Cairo surface in FORMAT_ARGB32
        
    Returns:
        QImage in Format_ARGB32_Premultiplied
    """
    arr = cairo_surface_to_numpy(surface)
    height, width = arr.shape[:2]
    
    # Create QImage from numpy data
    # Need to ensure data is contiguous
    arr = np.ascontiguousarray(arr)
    
    # Create QImage - we pass the data pointer directly
    # IMPORTANT: We must keep a reference to arr or the data will be garbage collected
    img = QImage(
        arr.data, 
        width, 
        height, 
        width * 4,  # bytes per line
        QImage.Format.Format_ARGB32_Premultiplied
    )
    
    # Make a deep copy so we don't depend on the numpy array's lifetime
    return img.copy()


# =============================================================================
# Blend Mode Mapping
# =============================================================================

# Map Qt CompositionMode to Cairo Operator
# Cairo supports fewer modes natively
_BLEND_MODE_MAP = {
    # Qt enum value -> Cairo operator
    0: cairo.OPERATOR_SOURCE,      # CompositionMode_SourceOver (use OVER for alpha blend)
    1: cairo.OPERATOR_OVER,        # CompositionMode_DestinationOver
    2: cairo.OPERATOR_CLEAR,       # CompositionMode_Clear
    3: cairo.OPERATOR_SOURCE,      # CompositionMode_Source
    # Note: 0 is actually SourceOver, we handle it specially below
}

def _get_qt_mode_value(mode) -> int:
    """Extract integer value from Qt CompositionMode enum."""
    if hasattr(mode, 'value'):
        return mode.value
    return int(mode)


@lru_cache(maxsize=32)
def _qt_blend_to_cairo(qt_mode) -> Tuple[cairo.Operator, bool]:
    """
    Convert Qt CompositionMode to Cairo Operator.

    Returns:
        Tuple of (operator, needs_fallback)
        If needs_fallback is True, use CPU compositing instead.
    """
    from PySide6.QtGui import QPainter

    # Use match/case for clearer control flow
    match qt_mode:
        case QPainter.CompositionMode.CompositionMode_SourceOver:
            return (cairo.OPERATOR_OVER, False)
        case QPainter.CompositionMode.CompositionMode_DestinationOver:
            return (cairo.OPERATOR_DEST_OVER, False)
        case QPainter.CompositionMode.CompositionMode_Clear:
            return (cairo.OPERATOR_CLEAR, False)
        case QPainter.CompositionMode.CompositionMode_Source:
            return (cairo.OPERATOR_SOURCE, False)
        case QPainter.CompositionMode.CompositionMode_Destination:
            return (cairo.OPERATOR_DEST, False)
        case QPainter.CompositionMode.CompositionMode_SourceIn:
            return (cairo.OPERATOR_IN, False)
        case QPainter.CompositionMode.CompositionMode_DestinationIn:
            return (cairo.OPERATOR_DEST_IN, False)
        case QPainter.CompositionMode.CompositionMode_SourceOut:
            return (cairo.OPERATOR_OUT, False)
        case QPainter.CompositionMode.CompositionMode_DestinationOut:
            return (cairo.OPERATOR_DEST_OUT, False)
        case QPainter.CompositionMode.CompositionMode_SourceAtop:
            return (cairo.OPERATOR_ATOP, False)
        case QPainter.CompositionMode.CompositionMode_DestinationAtop:
            return (cairo.OPERATOR_DEST_ATOP, False)
        case QPainter.CompositionMode.CompositionMode_Xor:
            return (cairo.OPERATOR_XOR, False)
        case QPainter.CompositionMode.CompositionMode_Plus:
            return (cairo.OPERATOR_ADD, False)
        case QPainter.CompositionMode.CompositionMode_Multiply:
            return (cairo.OPERATOR_MULTIPLY, False)
        case QPainter.CompositionMode.CompositionMode_Screen:
            return (cairo.OPERATOR_SCREEN, False)
        case QPainter.CompositionMode.CompositionMode_Overlay:
            return (cairo.OPERATOR_OVERLAY, False)
        case QPainter.CompositionMode.CompositionMode_Darken:
            return (cairo.OPERATOR_DARKEN, False)
        case QPainter.CompositionMode.CompositionMode_Lighten:
            return (cairo.OPERATOR_LIGHTEN, False)
        case QPainter.CompositionMode.CompositionMode_ColorDodge:
            return (cairo.OPERATOR_COLOR_DODGE, False)
        case QPainter.CompositionMode.CompositionMode_ColorBurn:
            return (cairo.OPERATOR_COLOR_BURN, False)
        case QPainter.CompositionMode.CompositionMode_HardLight:
            return (cairo.OPERATOR_HARD_LIGHT, False)
        case QPainter.CompositionMode.CompositionMode_SoftLight:
            return (cairo.OPERATOR_SOFT_LIGHT, False)
        case QPainter.CompositionMode.CompositionMode_Difference:
            return (cairo.OPERATOR_DIFFERENCE, False)
        case QPainter.CompositionMode.CompositionMode_Exclusion:
            return (cairo.OPERATOR_EXCLUSION, False)
        case _:
            # Default fallback: use OVER (Normal blend)
            return (cairo.OPERATOR_OVER, False)


# =============================================================================
# Cairo Renderer Class
# =============================================================================

class CairoRenderer:
    """
    Cairo-based document renderer.
    
    Provides layer compositing with correct opacity and blend modes,
    with per-layer surface caching for performance.
    """
    
    def __init__(self):
        # Cache: layer_id -> (cairo.ImageSurface, version)
        self._layer_cache: Dict[str, Tuple[cairo.ImageSurface, int]] = {}
        # Track layer versions for cache invalidation
        self._layer_versions: Dict[str, int] = {}
    
    def invalidate_layer(self, layer_id: str):
        """Mark a layer's cache as invalid."""
        if layer_id in self._layer_versions:
            self._layer_versions[layer_id] += 1
        else:
            self._layer_versions[layer_id] = 1
    
    def invalidate_all(self):
        """Invalidate all layer caches."""
        self._layer_cache.clear()
        self._layer_versions.clear()
    
    def _get_layer_surface(self, layer) -> cairo.ImageSurface:
        """
        Get Cairo surface for a layer, using cache if valid.
        
        Args:
            layer: Layer object with .id, .image attributes
            
        Returns:
            cairo.ImageSurface representing the layer
        """
        layer_id = layer.id
        current_version = self._layer_versions.get(layer_id, 0)
        
        # Check cache
        if layer_id in self._layer_cache:
            cached_surface, cached_version = self._layer_cache[layer_id]
            if cached_version == current_version:
                return cached_surface
        
        # Convert layer's QImage to Cairo surface
        surface = qimage_to_cairo_surface(layer.image)
        self._layer_cache[layer_id] = (surface, current_version)
        
        return surface
    
    def render(self, document, view_state=None) -> cairo.ImageSurface:
        """
        Render the document to a Cairo ImageSurface.
        
        Args:
            document: Document object with .size, .layers attributes
            view_state: Optional view transform (not implemented yet)
            
        Returns:
            cairo.ImageSurface with composited layers
        """
        width = document.size.width()
        height = document.size.height()
        
        # Create output surface
        output = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
        ctx = cairo.Context(output)
        
        # Clear to transparent
        ctx.set_operator(cairo.OPERATOR_CLEAR)
        ctx.paint()
        ctx.set_operator(cairo.OPERATOR_OVER)
        
        # Composite layers in order (bottom to top)
        for layer in document.layers:
            if not layer.visible:
                continue
            
            if layer.is_adjustment:
                # Adjustment layers modify the output directly
                self._apply_adjustment_layer(output, layer)
                # Reset context since surface data changed
                ctx = cairo.Context(output)
                continue
            
            # Get layer surface
            layer_surface = self._get_layer_surface(layer)
            
            # Apply layer mask if present
            if layer.mask:
                layer_surface = self._apply_mask(layer_surface, layer.mask)
            
            # Set opacity
            ctx.save()
            
            # Get blend mode
            operator, needs_fallback = _qt_blend_to_cairo(layer.blend_mode)
            ctx.set_operator(operator)
            
            # Paint layer with opacity
            ctx.set_source_surface(layer_surface, 0, 0)
            ctx.paint_with_alpha(layer.opacity)
            
            ctx.restore()
        
        return output
    
    def _apply_mask(self, layer_surface: cairo.ImageSurface, mask: QImage) -> cairo.ImageSurface:
        """
        Apply a mask to a layer surface.

        Args:
            layer_surface: The layer's Cairo surface
            mask: QImage mask (Format_Alpha8)

        Returns:
            New Cairo surface with mask applied
        """
        width = layer_surface.get_width()
        height = layer_surface.get_height()

        # Create output surface
        output = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
        ctx = cairo.Context(output)

        # Draw layer
        ctx.set_source_surface(layer_surface, 0, 0)
        ctx.paint()

        # Apply mask using DestinationIn
        # Use Alpha8-specific conversion for masks
        if mask.format() == QImage.Format.Format_Alpha8:
            mask_surface = qimage_alpha8_to_cairo_surface(mask)
        else:
            mask_surface = qimage_to_cairo_surface(mask)
        ctx.set_operator(cairo.OPERATOR_DEST_IN)
        ctx.set_source_surface(mask_surface, 0, 0)
        ctx.paint()

        return output
    
    def _apply_adjustment_layer(self, surface: cairo.ImageSurface, layer):
        """
        Apply an adjustment layer's effect to the output surface.
        
        This modifies the surface data in-place via NumPy.
        """
        try:
            # Convert to numpy, apply effect, write back
            arr = cairo_surface_to_numpy(surface)
            
            # Create temporary QImage for effect
            from PySide6.QtGui import QImage
            temp_img = QImage(
                arr.data, arr.shape[1], arr.shape[0], 
                arr.shape[1] * 4, QImage.Format.Format_ARGB32_Premultiplied
            )
            
            # Apply effect
            result_img = layer.render_effect(temp_img)
            
            # Convert back and write to surface
            result_arr = np.frombuffer(
                result_img.constBits(), dtype=np.uint8
            ).reshape(arr.shape)
            
            # Write back to surface's data buffer
            surface_data = np.frombuffer(surface.get_data(), dtype=np.uint8).reshape(arr.shape)
            np.copyto(surface_data, result_arr)
            surface.mark_dirty()
            
        except Exception as e:
            logger.error(f"Error applying adjustment layer {layer.name}: {e}", exc_info=True)
    
    def render_to_qimage(self, document, view_state=None) -> QImage:
        """
        Render the document to a QImage.
        
        This is the primary method for display integration.
        
        Args:
            document: Document object
            view_state: Optional view transform
            
        Returns:
            QImage in Format_ARGB32_Premultiplied
        """
        surface = self.render(document, view_state)
        return cairo_surface_to_qimage(surface)
