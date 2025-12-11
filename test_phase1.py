import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QSize, QRect
from PySide6.QtGui import QColor

# Setup app for Qt types
app = QApplication(sys.argv)

try:
    from src.core.document import Document
    from src.core.layer import Layer
    
    print("Initializing Document...")
    doc = Document(800, 600)
    assert doc.size.width() == 800
    
    # Test Layer Add
    print("Testing Add Layer...")
    l1 = doc.add_layer("Layer 1")
    assert len(doc.layers) == 1
    assert doc.layers[0] == l1
    
    # Test Undo Add
    print("Testing Undo Add Layer...")
    doc.history.undo()
    assert len(doc.layers) == 0
    
    doc.history.redo()
    assert len(doc.layers) == 1
    
    # Test Resize
    print("Testing Resize...")
    # Add pixel data to check scaling
    l1.image.setPixelColor(0, 0, QColor(255, 0, 0))
    doc.resize_image(400, 300)
    assert doc.size.width() == 400
    assert doc.layers[0].image.width() == 400
    # Check pixel if possible (scaling might interpolate, but let's just check size)
    
    # Test Undo Resize
    print("Testing Undo Resize...")
    doc.history.undo()
    assert doc.size.width() == 800
    assert doc.layers[0].image.width() == 800
    
    # Test Selection
    print("Testing Selection...")
    doc.set_selection(QRect(10, 10, 100, 100), "replace")
    assert doc.has_selection
    assert not doc.get_selection_region().isEmpty()
    # Note: QRegion.contains takes QPoint usually
    from PySide6.QtCore import QPoint
    print(f"Mask pixel at 50,50: {doc.selection_mask.pixelColor(50, 50).alpha()}")
    
    # Debug conversion
    from PySide6.QtGui import QBitmap, QRegion
    from PySide6.QtCore import Qt
    debug_mask = doc.selection_mask.createMaskFromColor(0, Qt.MaskMode.MaskOutColor)
    print(f"Debug Mask pixel at 50,50: {debug_mask.pixelIndex(50, 50)}")
    debug_bmp = QBitmap.fromImage(debug_mask)
    debug_rgn = QRegion(debug_bmp)
    print(f"Debug Region contains 50,50: {debug_rgn.contains(QPoint(50, 50))}")

    print(f"Real Region contains 50,50: {doc.get_selection_region().contains(QPoint(50, 50))}")
    
    if not doc.get_selection_region().contains(QPoint(50, 50)):
         # Maybe the region is inverted?
         print(f"Real Region contains 0,0 (should be false): {doc.get_selection_region().contains(QPoint(0, 0))}")

    assert doc.get_selection_region().contains(QPoint(50, 50))
    
    # Test Selection Undo
    print("Testing Undo Selection...")
    doc.history.undo()
    assert not doc.has_selection
    assert doc.get_selection_region().isEmpty()
    

    
    print("Phase 1 Verification Passed!")

except Exception as e:
    print(f"FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
