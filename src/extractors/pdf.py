from __future__ import annotations
"""Extracteur pour les fichiers PDF utilisant pdfplumber."""

from pathlib import Path
from typing import Optional

from .base import BaseExtractor, ExtractionResult

try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except ImportError:
    HAS_PDFPLUMBER = False


class PDFExtractor(BaseExtractor):
    """Extracteur pour les fichiers PDF utilisant pdfplumber."""

    @property
    def supported_extensions(self) -> list[str]:
        return [".pdf"]

    def can_handle(self, file_path: Path) -> bool:
        if not HAS_PDFPLUMBER:
            return False
        return file_path.suffix.lower() in self.supported_extensions

    def extract(self, file_path: Path) -> ExtractionResult:
        """
        Extrait le texte et les tableaux d'un fichier PDF.

        Utilise pdfplumber qui est particulièrement bon pour les tableaux.
        """
        if not HAS_PDFPLUMBER:
            return ExtractionResult(
                raw_text="",
                extraction_method="pdf_error",
                confidence_score=0.0,
                warnings=["pdfplumber n'est pas installé. Installez avec: pip install pdfplumber"],
            )

        warnings = []
        all_text = []
        all_tables = []

        try:
            with pdfplumber.open(file_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    # Extraire le texte
                    text = page.extract_text()
                    if text:
                        all_text.append(f"--- Page {page_num} ---\n{text}")

                    # Extraire les tableaux
                    tables = page.extract_tables()
                    for table_idx, table in enumerate(tables):
                        if table:
                            parsed_table = self._parse_table(table, page_num, table_idx)
                            if parsed_table:
                                all_tables.append(parsed_table)

        except Exception as e:
            return ExtractionResult(
                raw_text="",
                extraction_method="pdf_error",
                confidence_score=0.0,
                warnings=[f"Erreur lors de l'extraction PDF: {str(e)}"],
            )

        full_text = "\n\n".join(all_text)

        # Calculer le score de confiance
        confidence = self._calculate_pdf_confidence(full_text, all_tables, warnings)

        return ExtractionResult(
            raw_text=full_text,
            tables=all_tables,
            extraction_method="pdfplumber",
            confidence_score=confidence,
            warnings=warnings,
        )

    def _parse_table(
        self,
        table: list[list[Optional[str]]],
        page_num: int,
        table_idx: int,
    ) -> Optional[dict]:
        """
        Parse un tableau extrait par pdfplumber.

        Args:
            table: Tableau brut (liste de listes)
            page_num: Numéro de page
            table_idx: Index du tableau dans la page

        Returns:
            Dict avec headers, rows et métadonnées
        """
        if not table or len(table) < 2:
            return None

        # Nettoyer les cellules
        cleaned_table = []
        for row in table:
            cleaned_row = [
                (cell.strip() if cell else "") for cell in row
            ]
            cleaned_table.append(cleaned_row)

        # Première ligne = headers
        headers = cleaned_table[0]

        # Reste = données
        rows = []
        for row in cleaned_table[1:]:
            if any(cell for cell in row):  # Ignorer les lignes vides
                row_dict = {}
                for i, header in enumerate(headers):
                    if i < len(row):
                        key = header if header else f"col_{i}"
                        row_dict[key] = row[i]
                rows.append(row_dict)

        if not rows:
            return None

        return {
            "headers": headers,
            "rows": rows,
            "page": page_num,
            "table_index": table_idx,
        }

    def _calculate_pdf_confidence(
        self,
        text: str,
        tables: list[dict],
        warnings: list[str],
    ) -> float:
        """Calcule le score de confiance pour l'extraction PDF."""
        if not text:
            return 0.0

        score = 0.7  # Base score pour PDF avec texte

        # Bonus si des tableaux ont été trouvés
        if tables:
            score += 0.1

        # Bonus si le texte semble de bonne qualité
        text_length = len(text)
        if text_length > 500:
            score += 0.05
        if text_length > 2000:
            score += 0.05

        # Vérifier s'il y a des indicateurs de problèmes OCR
        garbled_ratio = self._estimate_garbled_text_ratio(text)
        if garbled_ratio > 0.1:
            score -= 0.2
            warnings.append(f"Possible problème OCR détecté ({garbled_ratio:.0%} texte illisible)")

        return max(0.0, min(score, 1.0))

    def _estimate_garbled_text_ratio(self, text: str) -> float:
        """
        Estime la proportion de texte potentiellement mal extrait.

        Retourne une valeur entre 0 et 1.
        """
        if not text:
            return 0.0

        # Compter les caractères "normaux" vs "suspects"
        normal_chars = 0
        suspect_chars = 0

        for char in text:
            if char.isalnum() or char.isspace() or char in ".,;:!?-()[]{}\"'$%&@#":
                normal_chars += 1
            else:
                suspect_chars += 1

        total = normal_chars + suspect_chars
        if total == 0:
            return 0.0

        return suspect_chars / total

    def extract_text_only(self, file_path: Path) -> str:
        """
        Extrait uniquement le texte (sans les tableaux).

        Utile pour une extraction rapide.
        """
        result = self.extract(file_path)
        return result.raw_text
