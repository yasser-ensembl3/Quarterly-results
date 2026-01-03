from __future__ import annotations
"""Extracteur pour les fichiers Markdown."""

import re
from pathlib import Path

from .base import BaseExtractor, ExtractionResult


class MarkdownExtractor(BaseExtractor):
    """Extracteur pour les fichiers Markdown (.md)."""

    @property
    def supported_extensions(self) -> list[str]:
        return [".md", ".markdown"]

    def can_handle(self, file_path: Path) -> bool:
        return file_path.suffix.lower() in self.supported_extensions

    def extract(self, file_path: Path) -> ExtractionResult:
        """
        Extrait le contenu d'un fichier Markdown.

        Les fichiers Markdown sont considérés comme haute confiance
        car le texte est déjà structuré.
        """
        warnings = []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except UnicodeDecodeError:
            # Essayer avec un autre encoding
            try:
                with open(file_path, "r", encoding="latin-1") as f:
                    content = f.read()
                warnings.append("Fichier lu avec encoding latin-1")
            except Exception as e:
                return ExtractionResult(
                    raw_text="",
                    extraction_method="markdown",
                    confidence_score=0.0,
                    warnings=[f"Erreur de lecture: {str(e)}"],
                )

        # Extraire les tableaux
        tables = self._extract_tables(content)

        # Calculer le score de confiance (élevé pour markdown)
        confidence = 0.95 if content.strip() else 0.0

        return ExtractionResult(
            raw_text=content,
            tables=tables,
            extraction_method="markdown_native",
            confidence_score=confidence,
            warnings=warnings,
        )

    def _extract_tables(self, content: str) -> list[dict]:
        """
        Extrait les tableaux Markdown du contenu.

        Un tableau Markdown a le format:
        | Header 1 | Header 2 |
        |----------|----------|
        | Value 1  | Value 2  |
        """
        tables = []
        table_pattern = r"(\|[^\n]+\|\n)(\|[-:\s|]+\|\n)((?:\|[^\n]+\|\n?)+)"

        for match in re.finditer(table_pattern, content):
            header_line = match.group(1).strip()
            rows_text = match.group(3).strip()

            # Parser les headers
            headers = [h.strip() for h in header_line.split("|") if h.strip()]

            # Parser les lignes
            rows = []
            for line in rows_text.split("\n"):
                if line.strip():
                    cells = [c.strip() for c in line.split("|") if c.strip()]
                    if cells:
                        row = dict(zip(headers, cells))
                        rows.append(row)

            if headers and rows:
                tables.append({
                    "headers": headers,
                    "rows": rows,
                    "raw": match.group(0),
                })

        return tables

    def extract_sections(self, content: str) -> dict[str, str]:
        """
        Extrait les sections basées sur les titres Markdown.

        Returns:
            Dict avec titre -> contenu
        """
        sections = {}
        current_section = "intro"
        current_content = []

        for line in content.split("\n"):
            # Détecter les titres (# ## ### etc.)
            header_match = re.match(r"^(#{1,6})\s+(.+)$", line)
            if header_match:
                # Sauvegarder la section précédente
                if current_content:
                    sections[current_section] = "\n".join(current_content).strip()
                # Commencer une nouvelle section
                current_section = header_match.group(2).strip()
                current_content = []
            else:
                current_content.append(line)

        # Sauvegarder la dernière section
        if current_content:
            sections[current_section] = "\n".join(current_content).strip()

        return sections
