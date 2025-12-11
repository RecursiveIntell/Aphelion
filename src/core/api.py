from .document import Document
from .commands import CanvasCommand, LayerStructureCommand
from .effects import EffectRegistry
from PySide6.QtGui import QColor, QImage

class AphelionAPI:
    def __init__(self, session):
        self.session = session
        
    @property
    def active_document(self) -> Document | None:
        # We need to bridge to MainWindow?
        # Or Session has active document? Currently MainWindow tracks it via Tabs.
        # Session has active_layer, active_tool etc.
        # But Document is not necessarily stored in Session as "active_document".
        # MainWindow updates Session when tab changes?
        # Actually session tracks colors/tools.
        # We need a way to get the document.
        # Let's assume the API user has access to "current" context or we pass doc explicitly?
        # For Console, we can inject `api` with `get_active_document` wired to `MainWindow.active_document`.
        
        # Let's abstract this: The console will bind a lambda for getting active doc.
        if hasattr(self, "_get_doc_fn"):
             return self._get_doc_fn()
        return None
        
    def set_doc_getter(self, fn):
        self._get_doc_fn = fn
        
    def add_layer(self, name="New Layer"):
        doc = self.active_document
        if not doc: return
        doc.add_layer(name)
        doc.set_active_layer(len(doc.layers) - 1)
        
    def delete_layer(self, index=-1):
        doc = self.active_document
        if not doc: return
        if index == -1: index = doc._active_layer_index
        doc.delete_layer(index)
        
    def resize_image(self, width, height):
        doc = self.active_document
        if not doc: return
        doc.resize_image(width, height)
        
    def apply_effect(self, effect_name, **config):
        doc = self.active_document
        if not doc: return
        layer = doc.get_active_layer()
        if not layer: return
        
        # Find effect
        registry = EffectRegistry.get_all()
        effect_cls = None
        for cat, effects in registry.items():
            for eff in effects:
                if eff.name == effect_name:
                    effect_cls = eff
                    break
            if effect_cls: break
            
        if not effect_cls:
            print(f"Effect '{effect_name}' not found.")
            return
            
        # Apply
        effect = effect_cls()
        # Create Command like MainWindow does but simplified (Synchronous for script)
        # Or Async? Scripts usually run sync.
        
        cmd = CanvasCommand(layer)
        # Capture before
        
        new_img = effect.apply(layer.image, config)
        if new_img:
            layer.image = new_img
            cmd.capture_after()
            doc.history.push(cmd)
            doc.content_changed.emit()
            print(f"Applied {effect_name}.")
            
    def fill(self, r, g, b, a=255):
         doc = self.active_document
         if not doc: return
         layer = doc.get_active_layer()
         if not layer: return
         
         cmd = CanvasCommand(layer)
         layer.image.fill(QColor(r, g, b, a))
         cmd.capture_after()
         doc.history.push(cmd)
         doc.content_changed.emit()
