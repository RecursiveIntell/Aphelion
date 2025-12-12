from PySide6.QtCore import QSettings

class SettingsManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SettingsManager, cls).__new__(cls)
            cls._instance._settings = QSettings("Aphelion", "AphelionApp")
        return cls._instance

    def set_value(self, key, value):
        self._settings.setValue(key, value)

    def get_value(self, key, default=None):
        return self._settings.value(key, default)
        
    def sync(self):
        self._settings.sync()

    def add_recent_file(self, filepath):
        recents = self.get_value("recent_files", [])
        if not isinstance(recents, list): recents = []
        
        # Remove if exists (to move to top)
        if filepath in recents:
            recents.remove(filepath)
            
        recents.insert(0, filepath)
        # Limit to 10
        recents = recents[:10]
        self.set_value("recent_files", recents)
        
    def get_recent_files(self):
        recents = self.get_value("recent_files", [])
        return recents if isinstance(recents, list) else []
