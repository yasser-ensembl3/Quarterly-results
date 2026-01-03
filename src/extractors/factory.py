from __future__ import annotations
"""Factory pour sélectionner l'extracteur approprié."""

from pathlib import Path
from typing import Optional, Union

from .base import BaseExtractor, ExtractionResult
from .markdown import MarkdownExtractor
from .pdf import PDFExtractor
from .image import ImageExtractor


class UnsupportedFileTypeError(Exception):
    """Erreur pour les types de fichiers non supportés."""
    pass


class ExtractorFactory:
    """Factory pour obtenir l'extracteur approprié pour un fichier."""

    # Liste des extracteurs disponibles (ordre de priorité)
    _extractors: list[BaseExtractor] = [
        MarkdownExtractor(),
        PDFExtractor(),
        ImageExtractor(),
    ]

    @classmethod
    def get_extractor(cls, file_path: Path) -> BaseExtractor:
        """
        Retourne l'extracteur approprié pour le fichier.

        Args:
            file_path: Chemin vers le fichier

        Returns:
            L'extracteur approprié

        Raises:
            UnsupportedFileTypeError: Si aucun extracteur ne peut gérer le fichier
        """
        for extractor in cls._extractors:
            if extractor.can_handle(file_path):
                return extractor

        raise UnsupportedFileTypeError(
            f"Aucun extracteur disponible pour: {file_path.suffix}"
        )

    @classmethod
    def extract(cls, file_path: Path) -> ExtractionResult:
        """
        Extrait directement le contenu d'un fichier.

        Shortcut pour get_extractor(path).extract(path)

        Args:
            file_path: Chemin vers le fichier

        Returns:
            ExtractionResult avec le contenu extrait
        """
        file_path = Path(file_path)
        extractor = cls.get_extractor(file_path)
        return extractor.extract(file_path)

    @classmethod
    def can_extract(cls, file_path: Path) -> bool:
        """
        Vérifie si un fichier peut être extrait.

        Args:
            file_path: Chemin vers le fichier

        Returns:
            True si un extracteur est disponible
        """
        try:
            cls.get_extractor(file_path)
            return True
        except UnsupportedFileTypeError:
            return False

    @classmethod
    def get_supported_extensions(cls) -> list[str]:
        """Retourne toutes les extensions supportées."""
        extensions = []
        for extractor in cls._extractors:
            extensions.extend(extractor.supported_extensions)
        return list(set(extensions))

    @classmethod
    def register_extractor(cls, extractor: BaseExtractor) -> None:
        """
        Enregistre un nouvel extracteur.

        Args:
            extractor: Instance de BaseExtractor à ajouter
        """
        cls._extractors.insert(0, extractor)  # Priorité aux nouveaux


def extract_file(file_path: Union[str, Path]) -> ExtractionResult:
    """
    Fonction utilitaire pour extraire un fichier.

    Args:
        file_path: Chemin vers le fichier (string ou Path)

    Returns:
        ExtractionResult
    """
    return ExtractorFactory.extract(Path(file_path))
