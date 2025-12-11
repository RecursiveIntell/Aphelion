import sys
from PySide6.QtWidgets import QApplication
from src.core.plugins import PluginManager
from src.ui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    
    # Init Plugins
    # manager = PluginManager()
    # Discovery handled by MainWindow to ensuring callbacks (register_tool) are ready.
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
