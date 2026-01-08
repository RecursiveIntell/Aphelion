import sys
import unittest
import os
import shutil
from aphelion.core.plugins import PluginManager, AphelionPlugin
from aphelion.core.effects import EffectRegistry, Effect

# Dummy Plugin Content
PLUGIN_CODE = """
from aphelion.core.plugins import AphelionPlugin
from aphelion.core.effects import EffectRegistry, Effect
from PySide6.QtGui import QImage

class TestEffect(Effect):
    name = "Test Effect Plugin"
    category = "Plugins"
    def apply(self, image: QImage, config: dict) -> QImage:
        return image

class MyPlugin(AphelionPlugin):
    name = "Test Plugin"
    version = "1.0"
    author = "Tester"
    description = "A test"

    def initialize(self, context):
        registry = context["EffectRegistry"]
        registry.register(TestEffect)
"""

class TestPhase6(unittest.TestCase):
    def setUp(self):
        self.test_dir = os.path.join(os.getcwd(), "test_plugins")
        if not os.path.exists(self.test_dir):
            os.makedirs(self.test_dir)
            
        with open(os.path.join(self.test_dir, "my_plugin.py"), "w") as f:
            f.write(PLUGIN_CODE)
            
        self.manager = PluginManager()
        # Reset singleton state effectively for test?
        # Singleton is tricky in tests. 
        self.manager.plugins = []
        self.manager.loaded_modules = {}
        
    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
            
    def test_plugin_discovery(self):
        self.manager.discover_plugins([self.test_dir])
        plugins = self.manager.get_loaded_plugins()
        
        found = False
        for p in plugins:
            if p.name == "Test Plugin":
                found = True
                break
        self.assertTrue(found, "Test Plugin not found in loaded plugins")
        
        # Verify Effect Registration
        effects = EffectRegistry.get_all()
        self.assertIn("Plugins", effects)
        names = [e.name for e in effects["Plugins"]]
        self.assertIn("Test Effect Plugin", names)

    def test_broken_plugin(self):
        # Create a plugin with syntax error
        broken_code = "This is not python code..."

        path = os.path.join(self.test_dir, "broken_plugin.py")
        with open(path, "w") as f:
            f.write(broken_code)

        # Should catch exception and not crash
        self.manager.discover_plugins([self.test_dir])
        # We expect 1 valid plugin from previous setup (MyPlugin) and 0 broken ones added.
        # But discover_plugins is additive or resets? It scans directory.
        # Since we are using same manager instance and same dir, it might reload MyPlugin.
        pass # The test is just that it doesn't crash.

if __name__ == '__main__':
    unittest.main()
