"""
NumPy-based image processing utilities for high-performance graphics operations.

Provides zero-copy (when possible) conversion between QImage and NumPy arrays,
and vectorized implementations of common image processing operations.

IMPORTANT: Qt uses BGRA order on little-endian systems and premultiplied alpha.
This module provides helpers to handle this correctly.
"""
import numpy as np
from PySide6.QtGui import QImage, QColor
from typing import Tuple


def qimage_to_numpy(img: QImage, unpremultiply: bool = False) -> np.ndarray:
    """
    Convert a QImage to a NumPy array.
    
    Args:
        img: QImage to convert
        unpremultiply: If True, convert from premultiplied to straight alpha.
                       Set to True for effects that do RGB math (otherwise you
                       get mysterious darkening artifacts).
    
    Returns:
        np.ndarray: Shape (height, width, 4) with BGRA order.
                    Channels are [Blue, Green, Red, Alpha] on little-endian systems.
    """
    # Ensure we have a compatible format
    if img.format() not in (QImage.Format.Format_ARGB32, 
                            QImage.Format.Format_ARGB32_Premultiplied,
                            QImage.Format.Format_RGB32):
        img = img.convertToFormat(QImage.Format.Format_ARGB32_Premultiplied)
    
    width = img.width()
    height = img.height()
    bytes_per_line = img.bytesPerLine()
    
    # Get pointer to image data
    # Handle both older (voidptr with setsize) and newer (memoryview) PySide6
    ptr = img.bits()
    if hasattr(ptr, 'setsize'):
        ptr.setsize(img.sizeInBytes())
        arr = np.frombuffer(ptr, dtype=np.uint8).reshape((height, bytes_per_line))
    else:
        # ptr is already a memoryview
        arr = np.asarray(ptr, dtype=np.uint8).reshape((height, bytes_per_line))
    
    # Slice to actual width (bytes_per_line may include padding)
    # First width*4 bytes are pixels, remainder is padding
    arr = arr[:, :width * 4].reshape((height, width, 4)).copy()
    
    if unpremultiply and img.format() == QImage.Format.Format_ARGB32_Premultiplied:
        arr = unpremultiply_alpha(arr)
    
    return arr


def numpy_to_qimage(arr: np.ndarray, premultiply: bool = False) -> QImage:
    """
    Convert a NumPy array back to QImage.
    
    Args:
        arr: Shape (height, width, 4) with BGRA order, dtype=uint8
        premultiply: If True, convert from straight to premultiplied alpha.
                     Set to True if you used unpremultiply=True during conversion.
        
    Returns:
        QImage in ARGB32_Premultiplied format
    """
    if arr.dtype != np.uint8:
        arr = np.clip(arr, 0, 255).astype(np.uint8)
    
    if len(arr.shape) == 2:
        # Grayscale - expand to BGRA
        arr = np.stack([arr, arr, arr, np.full_like(arr, 255)], axis=-1)
    
    if premultiply:
        arr = premultiply_alpha(arr)
    
    height, width = arr.shape[:2]
    
    # Ensure contiguous array
    arr = np.ascontiguousarray(arr)
    
    # Create QImage from data
    img = QImage(arr.data, width, height, arr.strides[0], 
                 QImage.Format.Format_ARGB32_Premultiplied)
    
    # Must copy since numpy array may be garbage collected
    return img.copy()


def unpremultiply_alpha(arr: np.ndarray) -> np.ndarray:
    """
    Convert from premultiplied to straight alpha.
    
    Premultiplied: RGB values are pre-scaled by alpha
    Straight: RGB values are unscaled
    
    Use this before doing effect math on RGB channels.
    """
    result = arr.astype(np.float32)
    alpha = result[:, :, 3:4]
    
    # Avoid division by zero
    mask = alpha > 0
    result[:, :, :3] = np.where(mask, result[:, :, :3] * 255.0 / np.maximum(alpha, 1), result[:, :, :3])
    
    return np.clip(result, 0, 255).astype(np.uint8)


def premultiply_alpha(arr: np.ndarray) -> np.ndarray:
    """
    Convert from straight to premultiplied alpha.
    
    Use this after doing effect math to prepare for Qt compositing.
    """
    result = arr.astype(np.float32)
    alpha = result[:, :, 3:4] / 255.0
    result[:, :, :3] = result[:, :, :3] * alpha
    return np.clip(result, 0, 255).astype(np.uint8)


def qimage_alpha8_to_numpy(img: QImage) -> np.ndarray:
    """Convert an Alpha8 format image (selection mask) to numpy array."""
    if img.format() != QImage.Format.Format_Alpha8:
        img = img.convertToFormat(QImage.Format.Format_Alpha8)
    
    width = img.width()
    height = img.height()
    bytes_per_line = img.bytesPerLine()
    
    # Handle both older (voidptr with setsize) and newer (memoryview) PySide6
    ptr = img.bits()
    if hasattr(ptr, 'setsize'):
        ptr.setsize(img.sizeInBytes())
        arr = np.frombuffer(ptr, dtype=np.uint8).reshape((height, bytes_per_line))
    else:
        arr = np.asarray(ptr, dtype=np.uint8).reshape((height, bytes_per_line))
    
    arr = arr[:, :width].copy()
    
    return arr


def numpy_to_qimage_alpha8(arr: np.ndarray) -> QImage:
    """Convert a 2D numpy array to Alpha8 QImage."""
    if arr.dtype != np.uint8:
        arr = np.clip(arr, 0, 255).astype(np.uint8)
    
    height, width = arr.shape
    arr = np.ascontiguousarray(arr)
    
    img = QImage(arr.data, width, height, arr.strides[0], QImage.Format.Format_Alpha8)
    return img.copy()


def gaussian_blur_np(arr: np.ndarray, sigma: float) -> np.ndarray:
    """
    Apply Gaussian blur using separable convolution.
    
    This is O(n*r) instead of O(n*r²) for a full 2D convolution.
    
    Args:
        arr: Image array shape (H, W, C) or (H, W)
        sigma: Standard deviation of Gaussian kernel
        
    Returns:
        Blurred image array
    """
    if sigma <= 0:
        return arr.copy()
    
    # Build 1D Gaussian kernel
    radius = int(np.ceil(sigma * 3))
    size = radius * 2 + 1
    x = np.arange(size) - radius
    kernel = np.exp(-x**2 / (2 * sigma**2))
    kernel = kernel / kernel.sum()
    
    # Handle multi-channel images
    if len(arr.shape) == 3:
        result = np.zeros_like(arr, dtype=np.float32)
        for c in range(arr.shape[2]):
            # Horizontal pass
            temp = np.apply_along_axis(
                lambda row: np.convolve(row, kernel, mode='same'),
                axis=1,
                arr=arr[:, :, c].astype(np.float32)
            )
            # Vertical pass
            result[:, :, c] = np.apply_along_axis(
                lambda col: np.convolve(col, kernel, mode='same'),
                axis=0,
                arr=temp
            )
        return np.clip(result, 0, 255).astype(np.uint8)
    else:
        # 2D array (grayscale/mask)
        temp = np.apply_along_axis(
            lambda row: np.convolve(row, kernel, mode='same'),
            axis=1,
            arr=arr.astype(np.float32)
        )
        result = np.apply_along_axis(
            lambda col: np.convolve(col, kernel, mode='same'),
            axis=0,
            arr=temp
        )
        return np.clip(result, 0, 255).astype(np.uint8)


def apply_lut(arr: np.ndarray, lut: np.ndarray, channels: tuple = (0, 1, 2)) -> np.ndarray:
    """
    Apply a lookup table to specified channels.
    
    Args:
        arr: Image array (H, W, 4) BGRA
        lut: Lookup table array of shape (256,)
        channels: Which channels to apply LUT to (0=B, 1=G, 2=R)
        
    Returns:
        Modified image array
    """
    result = arr.copy()
    for c in channels:
        result[:, :, c] = lut[arr[:, :, c]]
    return result


def morphological_dilate(mask: np.ndarray, radius: int) -> np.ndarray:
    """
    Dilate a binary/grayscale mask (for selection expansion).
    
    Uses a circular structuring element.
    """
    if radius <= 0:
        return mask.copy()
    
    height, width = mask.shape
    result = np.zeros_like(mask)
    
    # Create circular kernel
    y, x = np.ogrid[-radius:radius+1, -radius:radius+1]
    kernel_mask = x**2 + y**2 <= radius**2
    
    # Use maximum filter approach
    padded = np.pad(mask, radius, mode='constant', constant_values=0)
    
    for dy in range(-radius, radius + 1):
        for dx in range(-radius, radius + 1):
            if dx**2 + dy**2 <= radius**2:
                shifted = padded[radius+dy:radius+dy+height, radius+dx:radius+dx+width]
                result = np.maximum(result, shifted)
    
    return result


def morphological_erode(mask: np.ndarray, radius: int) -> np.ndarray:
    """
    Erode a binary/grayscale mask (for selection contraction).
    
    Uses a circular structuring element.
    """
    if radius <= 0:
        return mask.copy()
    
    height, width = mask.shape
    result = np.full_like(mask, 255)
    
    # Use minimum filter approach
    padded = np.pad(mask, radius, mode='constant', constant_values=0)
    
    for dy in range(-radius, radius + 1):
        for dx in range(-radius, radius + 1):
            if dx**2 + dy**2 <= radius**2:
                shifted = padded[radius+dy:radius+dy+height, radius+dx:radius+dx+width]
                result = np.minimum(result, shifted)
    
    return result


def box_blur_np(arr: np.ndarray, radius: int) -> np.ndarray:
    """
    Apply box blur using cumulative sum for O(1) per pixel.
    
    Args:
        arr: Image array (H, W, C) or (H, W)
        radius: Blur radius
        
    Returns:
        Blurred image array
    """
    if radius <= 0:
        return arr.copy()
    
    # Use cumsum-based approach for efficiency
    if len(arr.shape) == 3:
        result = np.zeros_like(arr, dtype=np.float32)
        for c in range(arr.shape[2]):
            result[:, :, c] = _box_blur_2d(arr[:, :, c].astype(np.float32), radius)
        return np.clip(result, 0, 255).astype(np.uint8)
    else:
        result = _box_blur_2d(arr.astype(np.float32), radius)
        return np.clip(result, 0, 255).astype(np.uint8)


def _box_blur_2d(arr: np.ndarray, radius: int) -> np.ndarray:
    """Box blur a 2D array using cumulative sums."""
    height, width = arr.shape
    
    # Horizontal pass
    padded_h = np.pad(arr, ((0, 0), (radius, radius)), mode='edge')
    cumsum_h = np.cumsum(padded_h, axis=1)
    temp = (cumsum_h[:, 2*radius:] - cumsum_h[:, :-2*radius]) / (2*radius + 1)
    
    # Vertical pass  
    padded_v = np.pad(temp, ((radius, radius), (0, 0)), mode='edge')
    cumsum_v = np.cumsum(padded_v, axis=0)
    result = (cumsum_v[2*radius:, :] - cumsum_v[:-2*radius, :]) / (2*radius + 1)
    
    return result


def sepia_transform(arr: np.ndarray) -> np.ndarray:
    """Apply sepia tone transformation."""
    # BGRA format, extract channels
    b, g, r = arr[:, :, 0].astype(np.float32), arr[:, :, 1].astype(np.float32), arr[:, :, 2].astype(np.float32)
    
    new_r = r * 0.393 + g * 0.769 + b * 0.189
    new_g = r * 0.349 + g * 0.686 + b * 0.168
    new_b = r * 0.272 + g * 0.534 + b * 0.131
    
    result = arr.copy()
    result[:, :, 0] = np.clip(new_b, 0, 255)
    result[:, :, 1] = np.clip(new_g, 0, 255)
    result[:, :, 2] = np.clip(new_r, 0, 255)
    
    return result.astype(np.uint8)
