"""Complete pipeline: PDF -> Markdown -> Claude Agents -> Claude Review -> Claude Normalize."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

from .pdf_to_markdown import pdf_to_markdown
from .financial_extractor import FinancialExtractor
from .strategic_extractor import StrategicExtractor
from .reviewer import ClaudeReviewer, ClaudeNormalizer
from ..gdrive.sync import DriveSync


@dataclass
class PipelineResult:
    """Complete pipeline result."""
    source_file: str
    company: str = ""
    quarter: str = ""
    year: int = 0

    # Steps
    markdown: str = ""
    financial_data: dict = field(default_factory=dict)  # From FinancialExtractor
    strategic_data: dict = field(default_factory=dict)  # From StrategicExtractor
    extracted_data: dict = field(default_factory=dict)  # Merged data
    validated_data: dict = field(default_factory=dict)
    normalized_data: dict = field(default_factory=dict)

    # Metadata
    is_valid: bool = False
    confidence_score: float = 0.0
    errors: list[str] = field(default_factory=list)
    processed_at: datetime = field(default_factory=datetime.now)


class FinancialsPipeline:
    """Pipeline: PDF -> MD -> Claude Agents (Financial + Strategic) -> Review -> Normalize."""

    def __init__(self, upload_markdown_to_drive: bool = True):
        self.financial_extractor = FinancialExtractor()
        self.strategic_extractor = StrategicExtractor()
        self.reviewer = ClaudeReviewer()
        self.normalizer = ClaudeNormalizer()
        self.upload_markdown_to_drive = upload_markdown_to_drive
        self._drive_sync: Optional[DriveSync] = None

    @property
    def drive_sync(self) -> DriveSync:
        """Lazy init du DriveSync."""
        if self._drive_sync is None:
            self._drive_sync = DriveSync()
        return self._drive_sync

    def process_pdf(self, pdf_path: Path, verbose: bool = True) -> PipelineResult:
        """
        Process a PDF through the complete pipeline.

        Args:
            pdf_path: Path to the PDF
            verbose: Show progress

        Returns:
            PipelineResult with all data
        """
        pdf_path = Path(pdf_path)
        result = PipelineResult(source_file=str(pdf_path))
        errors = []

        # Step 1: PDF -> Markdown
        if verbose:
            print(f"  [1/4] PDF -> Markdown: {pdf_path.name}...")
        try:
            result.markdown = pdf_to_markdown(pdf_path)

            # Sauvegarder le markdown intermédiaire
            self._save_markdown(pdf_path, result.markdown, verbose)
        except Exception as e:
            errors.append(f"PDF conversion error: {e}")
            result.errors = errors
            return result

        # Step 2a: Financial Extraction (Claude)
        if verbose:
            print(f"  [2/5] Claude Financial extraction...")
        try:
            result.financial_data = self.financial_extractor.extract(
                result.markdown,
                source_file=str(pdf_path)
            )
            if "error" in result.financial_data:
                errors.append(f"Financial: {result.financial_data['error']}")
        except Exception as e:
            errors.append(f"Financial extraction error: {e}")

        # Step 2b: Strategic Extraction (Claude)
        if verbose:
            print(f"  [3/5] Claude Strategic extraction...")
        try:
            result.strategic_data = self.strategic_extractor.extract(
                result.markdown,
                source_file=str(pdf_path)
            )
            if "error" in result.strategic_data:
                errors.append(f"Strategic: {result.strategic_data['error']}")
        except Exception as e:
            errors.append(f"Strategic extraction error: {e}")

        # Merge financial + strategic data
        result.extracted_data = self._merge_extractions(
            result.financial_data,
            result.strategic_data
        )

        # Get basic info from financial data (more reliable for company info)
        company_info = result.financial_data.get("company_info", {}) or result.strategic_data.get("company_info", {})
        result.company = company_info.get("name", "Unknown")
        result.quarter = company_info.get("quarter", "")
        result.year = company_info.get("year", 0)

        # Step 4: Claude Review
        if verbose:
            print(f"  [4/5] Claude review: {result.company}...")
        try:
            review_result = self.reviewer.review(result.extracted_data)
            if "error" in review_result:
                errors.append(review_result["error"])
            else:
                result.validated_data = review_result.get("validated_data", result.extracted_data)
                validation = review_result.get("validation", {})
                result.is_valid = validation.get("is_valid", True)
                result.confidence_score = validation.get("confidence_score", 0.8)
        except Exception as e:
            errors.append(f"Review error: {e}")
            result.validated_data = result.extracted_data

        # Step 5: Claude Normalize
        if verbose:
            print(f"  [5/5] Claude normalize...")
        try:
            result.normalized_data = self.normalizer.normalize(result.validated_data)
            if "error" in result.normalized_data:
                errors.append(result.normalized_data["error"])
        except Exception as e:
            errors.append(f"Normalize error: {e}")

        result.errors = errors
        return result

    def _merge_extractions(self, financial: dict, strategic: dict) -> dict:
        """
        Merge financial and strategic extractions into a unified structure.

        Args:
            financial: Output from FinancialExtractor
            strategic: Output from StrategicExtractor

        Returns:
            Merged dict compatible with reviewer expectations
        """
        merged = {}

        # Company info (prefer financial, fallback to strategic)
        merged["company_info"] = financial.get("company_info") or strategic.get("company_info", {})

        # Financial data - map to expected structure
        merged["financial_highlights"] = {
            "revenue": financial.get("income_statement", {}).get("revenue"),
            "net_income": financial.get("income_statement", {}).get("net_income"),
            "gross_profit": financial.get("income_statement", {}).get("gross_profit"),
            "operating_income": financial.get("income_statement", {}).get("operating_income"),
            "ebitda": financial.get("income_statement", {}).get("ebitda"),
            "eps": financial.get("income_statement", {}).get("eps"),
            "free_cash_flow": financial.get("cash_flow", {}).get("free_cash_flow"),
            "cash_and_equivalents": financial.get("balance_sheet", {}).get("cash_and_equivalents"),
            "total_debt": financial.get("balance_sheet", {}).get("total_debt"),
        }

        # Balance sheet and cash flow
        merged["balance_sheet"] = financial.get("balance_sheet", {})
        merged["cash_flow"] = financial.get("cash_flow", {})

        # Revenue breakdown
        merged["revenue_breakdown"] = financial.get("revenue_breakdown", {})

        # Operational metrics
        merged["operational_metrics"] = financial.get("operational_metrics", {})

        # Sector specific
        merged["sector_specific_metrics"] = financial.get("sector_specific", {})

        # Guidance (financial numbers + strategic commentary)
        merged["guidance_and_outlook"] = {
            "next_quarter": financial.get("guidance", {}).get("next_quarter", {}),
            "full_year": financial.get("guidance", {}).get("full_year", {}),
            "management_commentary": strategic.get("management_commentary", {}).get("outlook_sentiment", ""),
        }

        # Capital allocation
        merged["capital_allocation"] = financial.get("capital_allocation", {})

        # Strategic data
        merged["strategic_updates"] = {
            "acquisitions": strategic.get("partnerships_and_ma", {}).get("acquisitions", []),
            "partnerships": strategic.get("partnerships_and_ma", {}).get("partnerships", []),
            "product_launches": strategic.get("product_and_innovation", {}).get("new_launches", []),
            "strategic_initiatives": strategic.get("strategic_initiatives", []),
        }

        merged["risks_and_challenges"] = strategic.get("risks_and_challenges", [])

        merged["competitive_position"] = {
            "market_position": strategic.get("competitive_landscape", {}).get("market_position"),
            "competitive_advantages": strategic.get("competitive_landscape", {}).get("competitive_advantages", []),
            "market_trends": strategic.get("competitive_landscape", {}).get("industry_trends", []),
        }

        merged["notable_quotes"] = strategic.get("notable_quotes", [])
        merged["key_takeaways"] = strategic.get("key_takeaways", [])

        # Executive summary from strategic
        merged["executive_summary"] = strategic.get("executive_summary", {})

        # Investor highlights
        merged["investor_highlights"] = strategic.get("investor_highlights", {})

        # ESG
        merged["esg"] = strategic.get("esg_and_sustainability", {})

        # Metadata
        merged["extraction_metadata"] = {
            "financial_confidence": financial.get("extraction_metadata", {}).get("confidence_score"),
            "strategic_confidence": strategic.get("extraction_metadata", {}).get("confidence_score"),
            "financial_completeness": financial.get("extraction_metadata", {}).get("data_completeness"),
            "strategic_richness": strategic.get("extraction_metadata", {}).get("richness"),
        }

        return merged

    def _save_markdown(self, pdf_path: Path, markdown_content: str, verbose: bool = True) -> Optional[Path]:
        """
        Sauvegarde le markdown intermédiaire localement et l'upload vers Drive.

        Args:
            pdf_path: Chemin du PDF source (ex: data/raw/Q3_2024/Amazon/earnings.pdf)
            markdown_content: Contenu markdown généré
            verbose: Afficher les messages

        Returns:
            Chemin du fichier markdown local
        """
        # Créer le dossier markdown local (miroir de raw/)
        # Structure: data/markdown/Q3_2024/Amazon/earnings.md
        try:
            raw_parent = pdf_path.parent  # ex: data/raw/Q3_2024/Amazon
            company_name = raw_parent.name
            quarter_folder = raw_parent.parent.name

            # Chemin local: data/markdown/Q3_2024/Amazon/
            markdown_base = pdf_path.parents[3] / "markdown" / quarter_folder / company_name
            markdown_base.mkdir(parents=True, exist_ok=True)

            md_filename = pdf_path.stem + ".md"
            md_path = markdown_base / md_filename

            # Sauvegarder localement
            md_path.write_text(markdown_content, encoding="utf-8")
            if verbose:
                print(f"       → Markdown sauvegardé: {md_path}")

            # Upload vers Drive si activé
            if self.upload_markdown_to_drive:
                self._upload_markdown_to_drive(md_path, quarter_folder, company_name, verbose)

            return md_path
        except Exception as e:
            if verbose:
                print(f"       [!] Erreur sauvegarde markdown: {e}")
            return None

    def _upload_markdown_to_drive(
        self, md_path: Path, quarter_name: str, company_name: str, verbose: bool = True
    ) -> None:
        """Upload le markdown vers Google Drive."""
        try:
            root_folder_id = os.environ.get("GDRIVE_ROOT_FOLDER_ID")
            if not root_folder_id:
                if verbose:
                    print("       [!] GDRIVE_ROOT_FOLDER_ID non configuré, skip upload")
                return

            result = self.drive_sync.upload_results_to_company_folder(
                root_folder_id=root_folder_id,
                quarter_name=quarter_name,
                company_name=company_name,
                files=[md_path]
            )

            if result.get("uploaded"):
                if verbose:
                    print(f"       → Uploadé vers Drive: {company_name}/{md_path.name}")
            if result.get("errors"):
                if verbose:
                    for err in result["errors"]:
                        print(f"       [!] Erreur Drive: {err}")
        except Exception as e:
            if verbose:
                print(f"       [!] Erreur upload Drive: {e}")

    def process_company_folder(self, folder_path: Path) -> list[PipelineResult]:
        """Process all PDFs in a folder."""
        folder_path = Path(folder_path)
        results = []
        pdfs = list(folder_path.glob("*.pdf"))

        print(f"\n[Folder] {folder_path.name}: {len(pdfs)} PDFs")

        for pdf in pdfs:
            result = self.process_pdf(pdf)
            results.append(result)
            if result.errors:
                print(f"  [!] Errors: {result.errors}")
            else:
                print(f"  [OK] {result.company} - Confidence: {result.confidence_score:.0%}")

        return results


def process_single_pdf(pdf_path: str, verbose: bool = True) -> PipelineResult:
    """Process a single PDF through the complete pipeline."""
    pipeline = FinancialsPipeline()
    return pipeline.process_pdf(Path(pdf_path), verbose=verbose)


def process_and_display(pdf_path: str) -> dict:
    """Process a PDF and display normalized results."""
    result = process_single_pdf(pdf_path)

    print("\n" + "=" * 60)
    print(f"[Result] {result.company} - {result.quarter} {result.year}")
    print("=" * 60)

    if result.errors:
        print(f"\n[!] Errors: {result.errors}")

    if result.normalized_data and "error" not in result.normalized_data:
        print(f"\nConfidence: {result.confidence_score:.0%}")
        print(f"Type: {result.normalized_data.get('company_type', 'N/A')}")

        core = result.normalized_data.get("core_metrics", {})
        if core:
            print("\n[Financials]")
            for key, value in core.items():
                if value is not None:
                    if "pct" in key:
                        print(f"  {key}: {value:.1f}%")
                    elif isinstance(value, (int, float)):
                        print(f"  {key}: ${value:,.1f}M")
                    else:
                        print(f"  {key}: {value}")

        sector = result.normalized_data.get("sector_metrics", {})
        if sector:
            print("\n[Sector Metrics]")
            for key, value in sector.items():
                if value is not None:
                    print(f"  {key}: {value}")

    return result.normalized_data
