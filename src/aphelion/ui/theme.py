from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPalette, QColor
from PySide6.QtCore import Qt

DARK_THEME_QSS = """
QMainWindow {
    background-color: #2b2b2b;
}
QWidget {
    background-color: #2b2b2b;
    color: #e0e0e0;
    font-family: 'Inter', 'Segoe UI', sans-serif;
    font-size: 10pt;
}
QTabWidget::pane {
    border: 1px solid #3a3a3a;
    background: #2b2b2b;
}
QTabBar::tab {
    background: #333333;
    color: #aaaaaa;
    padding: 8px 12px;
    border: 1px solid #3a3a3a;
    border-bottom: none;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
}
QTabBar::tab:selected {
    background: #444444;
    color: #ffffff;
}
QDockWidget {
    titlebar-close-icon: url(close.png);
    titlebar-normal-icon: url(undock.png);
    border: 1px solid #3a3a3a;
}
QDockWidget::title {
    text-align: left;
    background: #333333;
    padding-left: 5px;
}
QMenu {
    background-color: #333333;
    border: 1px solid #444444;
}
QMenu::item {
    padding: 5px 20px;
}
QMenu::item:selected {
    background-color: #555555;
}
QPushButton {
    background-color: #444444;
    border: 1px solid #555555;
    border-radius: 4px;
    padding: 5px;
    color: #ffffff;
}
QPushButton:hover {
    background-color: #555555;
}
QPushButton:pressed {
    background-color: #666666;
}
QLineEdit, QSpinBox {
    background-color: #1e1e1e;
    border: 1px solid #3a3a3a;
    border-radius: 3px;
    padding: 3px;
    color: #ffffff;
}
QScrollBar:vertical {
    border: none;
    background: #2b2b2b;
    width: 12px;
    margin: 0px 0px 0px 0px;
}
QScrollBar::handle:vertical {
    background: #555555;
    min-height: 20px;
    border-radius: 6px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
QScrollBar:horizontal {
    border: none;
    background: #2b2b2b;
    height: 12px;
    margin: 0px 0px 0px 0px;
}
QScrollBar::handle:horizontal {
    background: #555555;
    min-width: 20px;
    border-radius: 6px;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}
"""

LIGHT_THEME_QSS = """
QMainWindow {
    background-color: #f0f0f0;
}
QWidget {
    background-color: #f0f0f0;
    color: #333333;
    font-family: 'Inter', 'Segoe UI', sans-serif;
    font-size: 10pt;
}
QTabWidget::pane {
    border: 1px solid #cccccc;
    background: #f0f0f0;
}
QTabBar::tab {
    background: #e0e0e0;
    color: #555555;
    padding: 8px 12px;
    border: 1px solid #cccccc;
    border-bottom: none;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
}
QTabBar::tab:selected {
    background: #ffffff;
    color: #000000;
}
QDockWidget {
    border: 1px solid #cccccc;
}
QDockWidget::title {
    background: #e0e0e0;
    color: #333333;
    padding-left: 5px;
}
QMenu {
    background-color: #ffffff;
    border: 1px solid #cccccc;
    color: #333333;
}
QMenu::item:selected {
    background-color: #e0e0e0;
}
QPushButton {
    background-color: #ffffff;
    border: 1px solid #cccccc;
    border-radius: 4px;
    padding: 5px;
    color: #333333;
}
QPushButton:hover {
    background-color: #e6e6e6;
}
QPushButton:pressed {
    background-color: #d0d0d0;
}
QLineEdit, QSpinBox {
    background-color: #ffffff;
    border: 1px solid #cccccc;
    color: #333333;
}
"""

class ThemeManager:
    @staticmethod
    def apply_theme(app: QApplication, theme_name: str):
        # Clear existing stylesheet first
        app.setStyleSheet("")
        
        if theme_name == "Light":
            ThemeManager.apply_light_theme(app)
        else:
            ThemeManager.apply_dark_theme(app)
        
        # Force complete style refresh on all widgets
        style = app.style()
        for widget in app.allWidgets():
            style.unpolish(widget)
            style.polish(widget)
            widget.update()
        
        # Process pending events to ensure immediate update
        app.processEvents()

    @staticmethod
    def apply_dark_theme(app: QApplication):
        app.setStyle("Fusion")
        
        # Palette for Fusion fallback - using ColorRole enum
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.Text, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 0, 0))
        palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(0, 0, 0))
        app.setPalette(palette)
        
        # Apply Stylesheet
        app.setStyleSheet(DARK_THEME_QSS)

    @staticmethod
    def apply_light_theme(app: QApplication):
        app.setStyle("Fusion")
        
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(240, 240, 240))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(0, 0, 0))
        palette.setColor(QPalette.ColorRole.Base, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(240, 240, 240))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor(0, 0, 0))
        palette.setColor(QPalette.ColorRole.Text, QColor(0, 0, 0))
        palette.setColor(QPalette.ColorRole.Button, QColor(240, 240, 240))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(0, 0, 0))
        palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 0, 0))
        palette.setColor(QPalette.ColorRole.Link, QColor(0, 100, 200))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(0, 120, 215))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
        app.setPalette(palette)
        
        app.setStyleSheet(LIGHT_THEME_QSS)

