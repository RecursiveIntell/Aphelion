#!/usr/bin/env python3
"""
Render Sample Script

Creates a test document with multiple layers and renders it to PNG
using the Cairo-based renderer. This validates the rendering pipeline.

Usage:
    cd /path/to/Aphelion
    PYTHONPATH=src python scripts/render_sample.py
"""
import sys
import os

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtCore import Qt, QPoint

from aphelion.core.document import Document


def create_sample_document():
    """Create a test document with multiple layers."""
    # Create 200x200 document
    doc = Document(200, 200)
    
    # Layer 1: Red background (bottom)
    layer1 = doc.add_layer("Red Background")
    layer1.image.fill(QColor(255, 100, 100, 255))
    layer1.opacity = 1.0
    
    # Layer 2: Blue semi-transparent square (middle)
    layer2 = doc.add_layer("Blue Square")
    layer2.image.fill(QColor(0, 0, 0, 0))  # Transparent
    painter = QPainter(layer2.image)
    painter.setBrush(QColor(100, 100, 255, 255))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawRect(30, 30, 100, 100)
    painter.end()
    layer2.opacity = 0.7  # 70% opacity
    
    # Layer 3: Green circle (top)
    layer3 = doc.add_layer("Green Circle")
    layer3.image.fill(QColor(0, 0, 0, 0))  # Transparent
    painter = QPainter(layer3.image)
    painter.setBrush(QColor(100, 255, 100, 255))
    painter.setPen(QPen(QColor(0, 0, 0), 2))
    painter.drawEllipse(70, 70, 80, 80)
    painter.end()
    layer3.opacity = 0.9
    
    return doc


def main():
    # Qt app required for QImage operations
    app = QApplication([])
    
    print("Creating sample document...")
    doc = create_sample_document()
    
    print(f"Document size: {doc.size.width()}x{doc.size.height()}")
    print(f"Layers: {len(doc.layers)}")
    for i, layer in enumerate(doc.layers):
        print(f"  [{i}] {layer.name} - opacity: {layer.opacity}")
    
    print("\nRendering with Cairo backend...")
    rendered = doc.render()
    
    print(f"Rendered image: {rendered.width()}x{rendered.height()}")
    print(f"Format: {rendered.format()}")
    
    # Save to PNG
    output_path = os.path.join(os.path.dirname(__file__), 'test_render_output.png')
    if rendered.save(output_path, 'PNG'):
        print(f"\n✓ Saved to: {output_path}")
    else:
        print(f"\n✗ Failed to save to: {output_path}")
        return 1
    
    # Verify some pixels
    print("\nPixel verification:")
    
    # Check corner (should be reddish from bottom layer)
    corner = rendered.pixelColor(5, 5)
    print(f"  Corner (5,5): R={corner.red()}, G={corner.green()}, B={corner.blue()}, A={corner.alpha()}")
    
    # Check center (should show green circle blended)
    center = rendered.pixelColor(100, 100)
    print(f"  Center (100,100): R={center.red()}, G={center.green()}, B={center.blue()}, A={center.alpha()}")
    
    print("\n✓ Cairo rendering test complete!")
    return 0


if __name__ == '__main__':
    sys.exit(main())
