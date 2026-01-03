from __future__ import annotations
"""Extracteur pour les fichiers images (basique, sans OCR complexe)."""

from pathlib import Path

from .base import BaseExtractor, ExtractionResult


class ImageExtractor(BaseExtractor):
    """
    Extracteur basique pour les images.

    Note: Cette version ne fait pas d'OCR. Elle enregistre le fichier
    pour traitement manuel ou futur traitement OCR.
    """

    @property
    def supported_extensions(self) -> list[str]:
        return [".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".tiff"]

    def can_handle(self, file_path: Path) -> bool:
        return file_path.suffix.lower() in self.supported_extensions

    def extract(self, file_path: Path) -> ExtractionResult:
        """
        Pour les images, retourne un placeholder indiquant qu'une review manuelle est nécessaire.

        L'OCR peut être ajouté plus tard si nécessaire.
        """
        file_size = file_path.stat().st_size if file_path.exists() else 0

        # Retourner un résultat indiquant que le fichier nécessite une review
        return ExtractionResult(
            raw_text=f"[IMAGE: {file_path.name}]\n"
                     f"Type: {file_path.suffix}\n"
                     f"Size: {file_size / 1024:.1f} KB\n"
                     f"Note: Extraction manuelle requise ou OCR à implémenter.",
            tables=[],
            extraction_method="image_placeholder",
            confidence_score=0.1,  # Faible confiance car pas vraiment extrait
            warnings=[
                "Les images nécessitent une extraction manuelle des données.",
                "OCR peut être ajouté si nécessaire (pytesseract, img2table).",
            ],
        )

    def get_image_info(self, file_path: Path) -> dict:
        """
        Retourne des informations basiques sur l'image.

        Note: Pour dimensions, installez Pillow: pip install Pillow
        """
        info = {
            "path": str(file_path),
            "name": file_path.name,
            "extension": file_path.suffix,
            "size_bytes": file_path.stat().st_size if file_path.exists() else 0,
        }

        # Essayer d'obtenir les dimensions si Pillow est disponible
        try:
            from PIL import Image
            with Image.open(file_path) as img:
                info["width"] = img.width
                info["height"] = img.height
                info["format"] = img.format
                info["mode"] = img.mode
        except ImportError:
            info["note"] = "Installez Pillow pour les dimensions: pip install Pillow"
        except Exception:
            pass

        return info
