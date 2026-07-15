"""
Type-safe plugin API for Aphelion.

Provides protocols and metadata for plugin development with runtime validation.
"""
from dataclasses import dataclass
from enum import Enum, auto
from typing import Protocol, Any, Optional, Callable
from PySide6.QtGui import QImage


class PluginCapability(Enum):
    """Types of capabilities a plugin can provide."""
    TOOL = auto()
    EFFECT = auto()
    FILE_FORMAT = auto()
    UI_EXTENSION = auto()


@dataclass(slots=True, frozen=True)
class PluginMetadata:
    """
    Immutable metadata for a plugin.

    Attributes:
        name: Display name of the plugin
        version: Version string (semantic versioning recommended)
        author: Author name or organization
        description: Brief description of functionality
        capabilities: List of capabilities this plugin provides
        homepage: Optional URL to plugin homepage/repo
        license: Optional license identifier (e.g., "MIT", "GPL-3.0")
    """
    name: str
    version: str
    author: str
    description: str
    capabilities: tuple[PluginCapability, ...]
    homepage: Optional[str] = None
    license: Optional[str] = None

    def __post_init__(self) -> None:
        """Validate metadata."""
        if not self.name or not self.version:
            raise ValueError("Plugin must have name and version")
        if not self.capabilities:
            raise ValueError("Plugin must declare at least one capability")


class ToolPlugin(Protocol):
    """
    Protocol for tool plugins.

    Tool plugins provide new painting/editing tools.
    """
    metadata: PluginMetadata

    def create_tool(self, document: Any, session: Any) -> Any:
        """
        Create an instance of the tool.

        Args:
            document: Active document
            session: Global session state

        Returns:
            Tool instance with mouse_press/move/release methods
        """
        ...


class EffectPlugin(Protocol):
    """
    Protocol for effect plugins.

    Effect plugins provide image processing effects.
    """
    metadata: PluginMetadata

    def create_effect(self) -> Any:
        """
        Create an instance of the effect.

        Returns:
            Effect instance with apply(image, config) method
        """
        ...


class FileFormatPlugin(Protocol):
    """
    Protocol for file format plugins.

    File format plugins add support for additional image formats.
    """
    metadata: PluginMetadata

    def can_read(self, file_path: str) -> bool:
        """Check if this plugin can read the given file."""
        ...

    def can_write(self, file_path: str) -> bool:
        """Check if this plugin can write the given file."""
        ...

    def read(self, file_path: str) -> QImage:
        """Read image from file."""
        ...

    def write(self, image: QImage, file_path: str, options: dict[str, Any]) -> bool:
        """Write image to file."""
        ...


class UIExtensionPlugin(Protocol):
    """
    Protocol for UI extension plugins.

    UI extension plugins can add menu items, panels, or other UI elements.
    """
    metadata: PluginMetadata

    def register_ui(self, main_window: Any) -> None:
        """
        Register UI extensions.

        Args:
            main_window: MainWindow instance to extend
        """
        ...


class EnhancedPlugin:
    """
    Enhanced base class for Aphelion plugins.

    Provides type-safe metadata and capability declaration.
    Plugins should inherit from this and implement relevant protocols.
    """

    def __init__(self, metadata: PluginMetadata):
        """
        Initialize plugin with metadata.

        Args:
            metadata: Plugin metadata (immutable)
        """
        self._metadata = metadata
        self._initialized = False

    @property
    def metadata(self) -> PluginMetadata:
        """Get plugin metadata."""
        return self._metadata

    def initialize(self, context: dict[str, Any]) -> None:
        """
        Initialize the plugin with application context.

        Args:
            context: Dictionary with EffectRegistry, register_tool, etc.
        """
        if self._initialized:
            return

        self._context = context
        self._initialized = True
        self.on_initialize(context)

    def on_initialize(self, context: dict[str, Any]) -> None:
        """
        Override this to perform plugin initialization.

        Args:
            context: Application context
        """
        pass

    def shutdown(self) -> None:
        """Called when plugin is being unloaded."""
        pass


def validate_plugin(plugin: Any) -> tuple[bool, Optional[str]]:
    """
    Validate that a plugin meets requirements.

    Args:
        plugin: Plugin instance to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not hasattr(plugin, 'metadata'):
        return (False, "Plugin missing metadata attribute")

    metadata = plugin.metadata
    if not isinstance(metadata, PluginMetadata):
        return (False, "Plugin metadata must be PluginMetadata instance")

    # Validate capabilities match implemented protocols
    for capability in metadata.capabilities:
        match capability:
            case PluginCapability.TOOL:
                if not hasattr(plugin, 'create_tool'):
                    return (False, f"Plugin declares TOOL capability but missing create_tool method")
            case PluginCapability.EFFECT:
                if not hasattr(plugin, 'create_effect'):
                    return (False, f"Plugin declares EFFECT capability but missing create_effect method")
            case PluginCapability.FILE_FORMAT:
                required = ['can_read', 'can_write', 'read', 'write']
                for method in required:
                    if not hasattr(plugin, method):
                        return (False, f"Plugin declares FILE_FORMAT capability but missing {method} method")
            case PluginCapability.UI_EXTENSION:
                if not hasattr(plugin, 'register_ui'):
                    return (False, f"Plugin declares UI_EXTENSION capability but missing register_ui method")

    return (True, None)
