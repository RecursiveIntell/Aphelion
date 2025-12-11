import json
import os
import zipfile
import tempfile
import shutil
from PySide6.QtGui import QImage, QColor, QPainter
from .document import Document
from .layer import Layer

class ProjectIO:
    @staticmethod
    def save_project(document: Document, filepath: str):
        # Create temp dir
        with tempfile.TemporaryDirectory() as temp_dir:
            layers_data = []
            
            # Save Layers
            for layer in document.layers:
                layer_filename = f"layer_{layer.id}.png"
                layer_path = os.path.join(temp_dir, layer_filename)
                layer.image.save(layer_path, "PNG")
                
                layers_data.append({
                    "id": layer.id,
                    "name": layer.name,
                    "visible": layer.visible,
                    "opacity": layer.opacity,
                    "blend_mode": layer.blend_mode.value,
                    "filename": layer_filename
                })
            
            # Manifest
            manifest = {
                "width": document.size.width(),
                "height": document.size.height(),
                "layers": layers_data
            }
            
            with open(os.path.join(temp_dir, "manifest.json"), "w") as f:
                json.dump(manifest, f, indent=4)
                
            # Zip it
            with zipfile.ZipFile(filepath, 'w', zipfile.ZIP_DEFLATED) as zipf:
                 for root, dirs, files in os.walk(temp_dir):
                    for file in files:
                        zipf.write(os.path.join(root, file), file)

    @staticmethod
    def load_project(filepath: str) -> Document:
        with tempfile.TemporaryDirectory() as temp_dir:
            with zipfile.ZipFile(filepath, 'r') as zipf:
                zipf.extractall(temp_dir)
                
            manifest_path = os.path.join(temp_dir, "manifest.json")
            if not os.path.exists(manifest_path):
                raise ValueError("Invalid project file: missing manifest.json")
                
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)
                
            width = manifest.get("width", 800)
            height = manifest.get("height", 600)
            
            document = Document(width, height)
            # Clear default layers? Document init creates empty?
            # Document init creates 0 layers in our current code? 
            # Check Document code: it initializes empty list. MainWindow adds "Background".
            
            # Recreate layers
            from PySide6.QtGui import QPainter
            
            for layer_data in manifest.get("layers", []):
                name = layer_data.get("name", "Layer")
                layer = document.add_layer(name)
                layer.id = layer_data.get("id", layer.id)
                layer.visible = layer_data.get("visible", True)
                layer.opacity = layer_data.get("opacity", 1.0)
                # Blend Mode
                mode_val = layer_data.get("blend_mode", QPainter.CompositionMode.CompositionMode_SourceOver)
                layer.blend_mode = QPainter.CompositionMode(mode_val)
                
                # Image
                filename = layer_data.get("filename")
                if filename:
                    img_path = os.path.join(temp_dir, filename)
                    if os.path.exists(img_path):
                        loaded_img = QImage(img_path)
                        if not loaded_img.isNull():
                            # Draw loaded image into layer image (to match format)
                            p = QPainter(layer.image)
                            p.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source)
                            p.drawImage(0, 0, loaded_img)
                            p.end()
                            
            return document

    @staticmethod
    def export_flat(document: Document, filepath: str):
         """Export flattened image. Supports PNG, JPEG, BMP, WebP, TIFF."""
         # Compose final image
         output = QImage(document.size, QImage.Format.Format_ARGB32_Premultiplied)
         output.fill(QColor(0,0,0,0))
         
         p = QPainter(output)
         
         for layer in document.layers:
            if layer.visible:
                p.setOpacity(layer.opacity)
                p.setCompositionMode(layer.blend_mode)
                p.drawImage(0, 0, layer.image)
         p.end()
         
         # Determine format from extension
         ext = os.path.splitext(filepath)[1].lower()
         
         format_map = {
             '.png': 'PNG',
             '.jpg': 'JPEG',
             '.jpeg': 'JPEG',
             '.bmp': 'BMP',
             '.gif': 'GIF',
             '.webp': 'WEBP',
             '.tiff': 'TIFF',
             '.tif': 'TIFF',
             '.tga': 'TGA',
             '.ico': 'ICO',
             '.ppm': 'PPM',
         }
         
         fmt = format_map.get(ext, 'PNG')
         
         # For JPEG, fill transparency with white
         if fmt in ('JPEG', 'BMP'):
             final = QImage(document.size, QImage.Format.Format_RGB32)
             final.fill(QColor(255, 255, 255))
             painter = QPainter(final)
             painter.drawImage(0, 0, output)
             painter.end()
             final.save(filepath, fmt)
         else:
             output.save(filepath, fmt)
    
    @staticmethod
    def get_supported_export_formats() -> str:
        """Return file filter string for export dialog."""
        return (
            "PNG Image (*.png);;"
            "JPEG Image (*.jpg *.jpeg);;"
            "WebP Image (*.webp);;"
            "TIFF Image (*.tiff *.tif);;"
            "BMP Image (*.bmp);;"
            "GIF Image (*.gif);;"
            "TGA Image (*.tga);;"
            "ICO Image (*.ico);;"
            "PPM Image (*.ppm);;"
            "All Files (*)"
        )
    
    @staticmethod
    def get_supported_import_formats() -> str:
        """Return file filter string for import dialog."""
        return (
            "All Images (*.png *.jpg *.jpeg *.webp *.tiff *.tif *.bmp *.gif *.tga *.ico *.ppm *.svg);;"
            "PNG Image (*.png);;"
            "JPEG Image (*.jpg *.jpeg);;"
            "WebP Image (*.webp);;"
            "TIFF Image (*.tiff *.tif);;"
            "BMP Image (*.bmp);;"
            "GIF Image (*.gif);;"
            "TGA Image (*.tga);;"
            "ICO Image (*.ico);;"
            "PPM Image (*.ppm);;"
            "SVG Image (*.svg);;"
            "All Files (*)"
        )
