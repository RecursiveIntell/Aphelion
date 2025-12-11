from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QScrollArea, QVBoxLayout, QFrame
from PySide6.QtGui import QPixmap, QPainter, QColor, QBrush, QImage
from PySide6.QtCore import Qt, Signal, QSize
import os

class ImageThumbnail(QFrame):
    clicked = Signal()
    close_requested = Signal()
    
    def __init__(self, document, is_active=False):
        super().__init__()
        self.document = document
        self.is_active = is_active
        self.setFixedSize(120, 90)
        self.setFrameShape(QFrame.StyledPanel)
        
        # Styles
        self.update_style()
        
    def update_style(self):
        if self.is_active:
            self.setStyleSheet("""
                ImageThumbnail { 
                    background-color: #3d8ec9; 
                    border: 1px solid #5daeea; 
                    border-radius: 2px;
                }
            """)
        else:
            self.setStyleSheet("""
                ImageThumbnail { 
                    background-color: #505050; 
                    border: 1px solid #303030; 
                    border-radius: 2px;
                }
                ImageThumbnail:hover {
                    background-color: #606060;
                }
            """)

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        
        # Draw Thumbnail
        # We need a cached thumb from document. For now, generate on demand (slow) or just draw name?
        # Let's check if document has `image`.
        rect = self.rect()
        thumb_rect = rect.adjusted(4, 4, -4, -20)
        
        if hasattr(self.document, 'image'):
            # Convert canvas (QImage) to pixmap scaled
            # This is heavy for paintEvent. Ideally cache it.
            # For prototype, we do it here but optimization needed.
            # Actually, `document.image` is the composition? No, `document.layers`.
            # We need `document.get_composition()`?
            # Let's assume document.layers[0] image for MVP or fill gray.
            
            painter.fillRect(thumb_rect, QColor(255, 255, 255)) # Checkerboard TODO
            
            # Simple Text fallback if no cached composite
            painter.setPen(Qt.white)
            painter.drawText(thumb_rect, Qt.AlignCenter, "IMG")
            
        # Draw Title
        text_rect = rect.adjusted(2, rect.height() - 18, -2, -2)
        painter.setPen(Qt.white)
        font = painter.font()
        font.setPointSize(8)
        painter.setFont(font)
        file_path = getattr(self.document, 'file_path', None)
        name = os.path.basename(file_path) if file_path else "Untitled"
        painter.drawText(text_rect, Qt.AlignCenter, name)
        painter.end()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()

class ImageStripWidget(QScrollArea):
    document_selected = Signal(int) # index
    
    def __init__(self):
        super().__init__()
        self.setFixedHeight(110)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff) # Scroll with wheel?
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        self.container = QWidget()
        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(5, 5, 5, 5)
        self.layout.setSpacing(5)
        self.layout.addStretch() # Left align
        self.container.setLayout(self.layout)
        
        self.setWidget(self.container)
        
        self.thumbnails = [] # List of (doc, widget)
        
    def sync(self, documents, active_index):
        # Brute force rebuild for MVP.
        # Clear layout
        # Note: removing from layout doesn't delete widget immediately.
        
        while self.layout.count():
            item = self.layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.spacerItem():
                pass
                
        self.thumbnails = []
        
        for i, doc in enumerate(documents):
            thumb = ImageThumbnail(doc, is_active=(i == active_index))
            thumb.clicked.connect(lambda idx=i: self.document_selected.emit(idx))
            self.layout.insertWidget(self.layout.count(), thumb)
            self.thumbnails.append(thumb)
            
        self.layout.addStretch()
