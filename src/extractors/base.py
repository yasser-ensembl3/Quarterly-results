from __future__ import annotations
"""Interface de base pour les extracteurs de données."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ExtractionResult:
    """Résultat d'une extraction de fichier."""
    raw_text: str
    tables: list[dict] = field(default_factory=list)
    extraction_method: str = "unknown"
    confidence_score: float = 0.0
    warnings: list[str] = field(default_factory=list)

    def __bool__(self) -> bool:
        """Retourne True si l'extraction contient du contenu."""
        return bool(self.raw_text.strip())


class BaseExtractor(ABC):
    """Classe de base pour tous les extracteurs."""

    @abstractmethod
    def extract(self, file_path: Path) -> ExtractionResult:
        """
        Extrait le texte et les données d'un fichier.

        Args:
            file_path: Chemin vers le fichier à extraire

        Returns:
            ExtractionResult contenant le texte et les métadonnées
        """
        pass

    @abstractmethod
    def can_handle(self, file_path: Path) -> bool:
        """
        Vérifie si cet extracteur peut traiter le fichier.

        Args:
            file_path: Chemin vers le fichier

        Returns:
            True si l'extracteur peut traiter ce type de fichier
        """
        pass

    @property
    @abstractmethod
    def supported_extensions(self) -> list[str]:
        """Extensions de fichiers supportées par cet extracteur."""
        pass

    def _calculate_confidence(self, text: str) -> float:
        """
        Calcule un score de confiance basé sur le contenu extrait.

        Args:
            text: Texte extrait

        Returns:
            Score entre 0.0 et 1.0
        """
        if not text:
            return 0.0

        # Heuristiques basiques
        text_length = len(text)
        has_numbers = any(c.isdigit() for c in text)
        has_financial_keywords = any(
            kw in text.lower()
            for kw in ["revenue", "profit", "income", "margin", "eps", "growth"]
        )

        score = 0.5  # Base score

        # Ajuster selon la longueur
        if text_length > 100:
            score += 0.2
        if text_length > 500:
            score += 0.1

        # Bonus si contient des nombres (données financières)
        if has_numbers:
            score += 0.1

        # Bonus si contient des termes financiers
        if has_financial_keywords:
            score += 0.1

        return min(score, 1.0)
