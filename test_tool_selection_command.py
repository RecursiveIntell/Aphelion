import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QSize, QRect, QPoint, Qt
from PySide6.QtGui import QColor, QImage, QPainter, qAlpha

# Setup app for Qt types
app = QApplication.instance() or QApplication(sys.argv)

try:
    from aphelion.core.document import Document
    from aphelion.tools.selection import EllipseSelectTool, LassoSelectTool

    print("Initializing Document...")
    doc = Document(200, 200)

    # Test EllipseSelectTool._create_selection_command
    print("Testing EllipseSelectTool._create_selection_command...")
    tool = EllipseSelectTool(doc, None)

    # Create a partial mask (e.g., a circle)
    partial_mask = QImage(200, 200, QImage.Format.Format_Alpha8)
    partial_mask.fill(0)
    painter = QPainter(partial_mask)
    painter.setBrush(Qt.white)
    painter.setPen(Qt.NoPen)
    painter.drawEllipse(50, 50, 100, 100)
    painter.end()

    # 1. Test Replace
    print("Testing Replace...")
    cmd = tool._create_selection_command(partial_mask, "replace")
    cmd.execute() # Apply to doc

    # Check if doc selection is correct (center should be selected)
    val = qAlpha(doc.selection_mask.pixel(100, 100))
    print(f"Center value: {val}")
    assert val == 255
    assert qAlpha(doc.selection_mask.pixel(10, 10)) == 0

    # 2. Test Add
    print("Testing Add...")
    # Add another circle
    partial_mask2 = QImage(200, 200, QImage.Format.Format_Alpha8)
    partial_mask2.fill(0)
    painter = QPainter(partial_mask2)
    painter.setBrush(Qt.white)
    painter.setPen(Qt.NoPen)
    painter.drawEllipse(100, 100, 100, 100)
    painter.end()

    cmd = tool._create_selection_command(partial_mask2, "add")
    cmd.execute()

    # Original center
    assert qAlpha(doc.selection_mask.pixel(100, 100)) == 255
    # New center
    assert qAlpha(doc.selection_mask.pixel(150, 150)) == 255
    # Outside
    assert qAlpha(doc.selection_mask.pixel(10, 10)) == 0

    # 3. Test Subtract
    print("Testing Subtract...")
    # Subtract center area
    partial_mask3 = QImage(200, 200, QImage.Format.Format_Alpha8)
    partial_mask3.fill(0)
    painter = QPainter(partial_mask3)
    painter.setBrush(Qt.white)
    painter.setPen(Qt.NoPen)
    painter.drawRect(90, 90, 20, 20)
    painter.end()

    cmd = tool._create_selection_command(partial_mask3, "subtract")
    cmd.execute()

    # Center (100, 100) should now be unselected
    assert qAlpha(doc.selection_mask.pixel(100, 100)) == 0
    # 150, 150 should still be selected
    assert qAlpha(doc.selection_mask.pixel(150, 150)) == 255

    print("Tool Selection Command Verification Passed!")

except Exception as e:
    print(f"FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
