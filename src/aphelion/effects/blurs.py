"""
Blur and Sharpen effects for Aphelion.

Optimized with NumPy for high-performance image processing.
"""
from PySide6.QtGui import QImage, QColor
from PySide6.QtWidgets import QDialog
from PySide6.QtCore import Qt
from ..core.effects import Effect
from ..ui.dialogs import ConfigDialog
from ..ui.dialogs.controls import create_slider_control
from ..utils.image_processing import (
    qimage_to_numpy, numpy_to_qimage, gaussian_blur_np,
    box_blur_np, apply_lut, sepia_transform
)
import numpy as np
import math


class GaussianBlurEffect(Effect):
    name = "Gaussian Blur"
    category = "Blurs"

    def create_dialog(self, parent) -> QDialog:
        controls = [
            create_slider_control("radius", "Radius:", 3, 1, 50),
        ]
        return ConfigDialog(self.name, controls, parent)
    
    def apply(self, image: QImage, config: dict) -> QImage:
        radius = config.get("radius", 3)
        
        if radius <= 0:
            return image.copy()
        
        # Convert to numpy, blur, convert back
        arr = qimage_to_numpy(image)
        sigma = radius / 3.0
        result_arr = gaussian_blur_np(arr, sigma)
        return numpy_to_qimage(result_arr)


class SharpenEffect(Effect):
    """Unsharp mask sharpening."""
    name = "Sharpen"
    category = "Blurs"

    def create_dialog(self, parent) -> QDialog:
        controls = [
            create_slider_control("amount", "Amount:", 50, 1, 100),
        ]
        return ConfigDialog(self.name, controls, parent)
    
    def apply(self, image: QImage, config: dict) -> QImage:
        amount = config.get("amount", 50) / 100.0
        
        arr = qimage_to_numpy(image)
        blurred = gaussian_blur_np(arr, sigma=1.0)
        
        # Unsharp mask: Original + (Original - Blurred) * amount
        result = arr.astype(np.float32) + (arr.astype(np.float32) - blurred.astype(np.float32)) * amount
        result = np.clip(result, 0, 255).astype(np.uint8)
        
        return numpy_to_qimage(result)


class MotionBlurEffect(Effect):
    name = "Motion Blur"
    category = "Blurs"

    def create_dialog(self, parent) -> QDialog:
        controls = [
            create_slider_control("distance", "Distance:", 10, 1, 50),
            create_slider_control("angle", "Angle:", 0, 0, 360),
        ]
        return ConfigDialog(self.name, controls, parent)
    
    def apply(self, image: QImage, config: dict) -> QImage:
        distance = config.get("distance", 10)
        angle = config.get("angle", 0)
        
        arr = qimage_to_numpy(image)
        height, width = arr.shape[:2]
        
        # Create motion blur kernel
        rad = math.radians(angle)
        dx = math.cos(rad)
        dy = math.sin(rad)
        
        # Accumulate shifted images
        result = np.zeros_like(arr, dtype=np.float32)
        count = 0
        
        for i in range(distance):
            shift_x = int(dx * i)
            shift_y = int(dy * i)
            
            # Use numpy roll for efficient shifting
            shifted = np.roll(arr, shift_x, axis=1)
            shifted = np.roll(shifted, shift_y, axis=0)
            
            # Handle edge cases by masking
            if shift_x > 0:
                shifted[:, :shift_x] = arr[:, :shift_x]
            elif shift_x < 0:
                shifted[:, shift_x:] = arr[:, shift_x:]
            if shift_y > 0:
                shifted[:shift_y, :] = arr[:shift_y, :]
            elif shift_y < 0:
                shifted[shift_y:, :] = arr[shift_y:, :]
            
            result += shifted.astype(np.float32)
            count += 1
        
        if count > 0:
            result = result / count
        
        return numpy_to_qimage(np.clip(result, 0, 255).astype(np.uint8))


class SepiaEffect(Effect):
    """Sepia tone effect."""
    name = "Sepia"
    category = "Adjustments"
    
    def apply(self, image: QImage, config: dict) -> QImage:
        arr = qimage_to_numpy(image)
        result = sepia_transform(arr)
        return numpy_to_qimage(result)


class MedianEffect(Effect):
    """Median filter for noise reduction."""
    name = "Median"
    category = "Blurs"

    def create_dialog(self, parent) -> QDialog:
        controls = [
            create_slider_control("radius", "Radius:", 1, 1, 5),
        ]
        return ConfigDialog(self.name, controls, parent)
    
    def apply(self, image: QImage, config: dict) -> QImage:
        radius = config.get("radius", 1)
        
        arr = qimage_to_numpy(image)
        height, width = arr.shape[:2]
        result = arr.copy()
        
        # Median filter using numpy - more efficient than per-pixel
        # Collect neighborhood and compute median
        window_size = 2 * radius + 1
        
        for c in range(min(3, arr.shape[2])):  # Process RGB, skip alpha
            padded = np.pad(arr[:, :, c], radius, mode='edge')
            
            # Create view of neighborhoods
            neighborhoods = np.lib.stride_tricks.sliding_window_view(
                padded, (window_size, window_size)
            )
            
            # Compute median for each position
            result[:, :, c] = np.median(
                neighborhoods.reshape(height, width, -1), 
                axis=2
            ).astype(np.uint8)
        
        return numpy_to_qimage(result)


class UnfocusEffect(Effect):
    """Simple defocus blur - faster than Gaussian, produces soft out-of-focus look."""
    name = "Unfocus"
    category = "Blurs"

    def create_dialog(self, parent) -> QDialog:
        controls = [
            create_slider_control("radius", "Radius:", 4, 1, 100),
        ]
        return ConfigDialog(self.name, controls, parent)
    
    def apply(self, image: QImage, config: dict) -> QImage:
        radius = config.get("radius", 4)
        
        if radius <= 0:
            return image.copy()
        
        arr = qimage_to_numpy(image)
        
        # Use box blur for simple defocus effect
        result = box_blur_np(arr, radius)
        
        return numpy_to_qimage(result)
