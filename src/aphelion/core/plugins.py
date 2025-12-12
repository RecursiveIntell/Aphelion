import importlib.util
import os
import sys
import inspect
from typing import List, Type
from abc import ABC, abstractmethod

from enum import Enum, auto
from ..core.settings import SettingsManager

class PluginType(Enum):
    EFFECT = auto()
    TOOL = auto()
    GENERAL = auto()

# Interface
class AphelionPlugin(ABC):
    name: str = "Unknown Plugin"
    version: str = "0.1"
    author: str = "Unknown"
    description: str = "No description."
    type: PluginType = PluginType.GENERAL

    @abstractmethod
    def initialize(self, context):
        """
        Initialize the plugin.
        Context exposes:
        - register_tool(name, tool_cls, icon, shortcut)
        - register_effect(effect_cls)
        - add_menu_action(menu_path, action)
        """
        pass

class PluginManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PluginManager, cls).__new__(cls)
            cls._instance.plugins = []
            cls._instance.loaded_modules = {}
            cls._instance.context = {} # Stored context callbacks
            cls._instance.settings = SettingsManager()
        return cls._instance

    def set_context_callbacks(self, callbacks: dict):
        self.context.update(callbacks)

    def discover_plugins(self, directories: List[str]):
        """
        Scan directories for python files or packages that implement AphelionPlugin.
        """
        disabled_plugins = self.settings.get_value("plugins/disabled", [])
        
        for directory in directories:
            if not os.path.exists(directory):
                continue
                
            for filename in os.listdir(directory):
                if filename.endswith(".py") and not filename.startswith("__"):
                    # Single file plugin
                    self._load_plugin_from_file(os.path.join(directory, filename), disabled_list=disabled_plugins)
                elif os.path.isdir(os.path.join(directory, filename)):
                    # Package plugin (must have __init__.py)
                    init_path = os.path.join(directory, filename, "__init__.py")
                    if os.path.exists(init_path):
                         self._load_plugin_from_file(init_path, package_name=filename, disabled_list=disabled_plugins)

    def _load_plugin_from_file(self, filepath: str, package_name: str = None, disabled_list: list = None):
        try:
            name = package_name if package_name else os.path.basename(filepath).replace(".py", "")
            
            # Helper to check class without full load? Hard in Python.
            # We load module, check class. If disabled, just don't init?
            # Or load, check name, if disabled don't init.
            
            spec = importlib.util.spec_from_file_location(name, filepath)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                sys.modules[name] = module
                spec.loader.exec_module(module)
                
                # Scan for Plugin Class
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (inspect.isclass(attr) and 
                        issubclass(attr, AphelionPlugin) and 
                        attr is not AphelionPlugin):
                        
                        plugin_instance = attr()
                        
                        if disabled_list and plugin_instance.name in disabled_list:
                            print(f"Skipping disabled plugin: {plugin_instance.name}")
                            continue
                            
                        self._initialize_plugin(plugin_instance)
                        self.plugins.append(plugin_instance)
                        print(f"Loaded plugin: {plugin_instance.name}")
                        
        except Exception as e:
            print(f"Failed to load plugin {filepath}: {e}")

    def _initialize_plugin(self, plugin: AphelionPlugin):
        # Context creation
        from .effects import EffectRegistry
        
        context = {
            "EffectRegistry": EffectRegistry,
            "register_tool": self.context.get("register_tool", lambda *a: print("Tool reg not avail")),
            # Add more as needed
        }
        try:
            plugin.initialize(context)
        except Exception as e:
             print(f"Error initializing plugin {plugin.name}: {e}")

    def get_loaded_plugins(self) -> List[AphelionPlugin]:
        return self.plugins
    
    def set_plugin_enabled(self, plugin_name: str, enabled: bool):
        disabled = self.settings.get_value("plugins/disabled", [])
        if not enabled:
            if plugin_name not in disabled:
                disabled.append(plugin_name)
        else:
            if plugin_name in disabled:
                disabled.remove(plugin_name)
        self.settings.set_value("plugins/disabled", disabled)
