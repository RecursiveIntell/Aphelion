"""Application controller for Aphelion.

Separates initialization logic from the UI, preventing MainWindow from being
the "all-knowing deity" of the codebase.
"""
import sys
from PySide6.QtWidgets import QApplication

from .core.settings import SettingsManager
from .core.plugins import PluginManager
from .ui.theme import ThemeManager
from .ui.main_window import MainWindow


class AppController:
    """Central application controller.
    
    Responsibilities:
    - Initialize QApplication with proper settings
    - Create and configure SettingsManager
    - Create PluginManager
    - Create MainWindow and wire everything together
    - Handle application lifecycle
    """
    
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.settings = SettingsManager()
        self.plugin_manager = PluginManager()
        self.window = None
        
    def initialize(self):
        """Set up the application."""
        # Apply theme from settings
        theme = self.settings.get_value("theme", "Dark")
        ThemeManager.apply_theme(self.app, theme)
        
        # Create main window
        self.window = MainWindow(settings=self.settings, plugin_manager=self.plugin_manager)
        
    def run(self) -> int:
        """Run the application event loop."""
        self.window.show()
        return self.app.exec()


def main():
    """Main entry point for Aphelion."""
    controller = AppController()
    controller.initialize()
    sys.exit(controller.run())


if __name__ == "__main__":
    main()
