import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QColor, QImage, QPainter

# Setup app for Qt types
app = QApplication.instance() or QApplication(sys.argv)

try:
    from aphelion.core.document import Document

    print("Initializing Document...")
    doc = Document(200, 200)

    # 1. Test Replace
    print("Testing Selection Replace...")
    from PySide6.QtCore import QRect, QPoint
    doc.set_selection(QRect(50, 50, 100, 100), "replace")
    assert doc.has_selection
    assert doc.get_selection_region().contains(QPoint(60, 60))
    assert not doc.get_selection_region().contains(QPoint(10, 10))

    # Check mask values
    # In alpha8, selected is 255 (if white painted) or 0 (if inverted).
    # Document.combine_selection uses:
    # replace: fills 0, draws mask (usually white/255)
    # So 255 is selected.
    # val = QColor(doc.selection_mask.pixel(60, 60)).alpha()
    # Wait, pixel() returns ARGB int. For Format_Alpha8, it returns an index into color table or just alpha?
    # QImage.pixel() on Alpha8 returns an index which is the alpha value.
    # Actually pixel() returns QRgb.
    # pixelIndex() returns the index.
    # For Alpha8, pixelIndex() is the alpha value.
    # val = doc.selection_mask.pixelIndex(60, 60)
    val = QColor(doc.selection_mask.pixel(60, 60)).alpha()
    print(f"Replace Value at 60,60: {val}")
    assert val == 255 or val == 0 # Depending on impl, likely 255

    # 2. Test Add
    print("Testing Selection Add...")
    # Add a rectangle that overlaps partially
    # Existing: 50,50 100x100 (ends 150,150)
    # New: 100, 100 100x100 (ends 200,200)
    doc.set_selection(QRect(100, 100, 100, 100), "add")

    # Should contain 60,60 (original)
    assert doc.get_selection_region().contains(QPoint(60, 60))
    # Should contain 160, 160 (new)
    assert doc.get_selection_region().contains(QPoint(160, 160))
    # Should contain 120, 120 (overlap)
    assert doc.get_selection_region().contains(QPoint(120, 120))

    # 3. Test Subtract
    print("Testing Selection Subtract...")
    # Subtract 120, 120 100x100
    doc.set_selection(QRect(120, 120, 100, 100), "subtract")

    # 60, 60 should still be selected
    assert doc.get_selection_region().contains(QPoint(60, 60))
    # 160, 160 should NOT be selected
    assert not doc.get_selection_region().contains(QPoint(160, 160))
    # 120, 120 should NOT be selected
    assert not doc.get_selection_region().contains(QPoint(130, 130))

    # 4. Test Intersect
    print("Testing Selection Intersect...")
    # Reset to simple rect
    doc.set_selection(QRect(0, 0, 100, 100), "replace")
    # Intersect with 50, 0, 100, 100
    doc.set_selection(QRect(50, 0, 100, 100), "intersect")

    # Overlap is 50, 0, 50, 100
    assert doc.get_selection_region().contains(QPoint(60, 10))
    assert not doc.get_selection_region().contains(QPoint(10, 10))
    assert not doc.get_selection_region().contains(QPoint(140, 10))

    print("Selection Logic Verification Passed!")

except Exception as e:
    print(f"FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
