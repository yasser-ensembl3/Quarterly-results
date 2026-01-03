"""Complete pipeline: PDF -> Markdown -> OpenAI -> Claude Review -> Claude Normalize."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from .pdf_to_markdown import pdf_to_markdown
from .extractor import OpenAIExtractor
from .reviewer import ClaudeReviewer, ClaudeNormalizer


@dataclass
class PipelineResult:
    """Complete pipeline result."""
    source_file: str
    company: str = ""
    quarter: str = ""
    year: int = 0

    # Steps
    markdown: str = ""
    extracted_data: dict = field(default_factory=dict)
    validated_data: dict = field(default_factory=dict)
    normalized_data: dict = field(default_factory=dict)

    # Metadata
    is_valid: bool = False
    confidence_score: float = 0.0
    errors: list[str] = field(default_factory=list)
    processed_at: datetime = field(default_factory=datetime.now)


class FinancialsPipeline:
    """Pipeline: PDF -> MD -> OpenAI -> Claude Review -> Claude Normalize."""

    def __init__(self):
        self.extractor = OpenAIExtractor()
        self.reviewer = ClaudeReviewer()
        self.normalizer = ClaudeNormalizer()

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
        except Exception as e:
            errors.append(f"PDF conversion error: {e}")
            result.errors = errors
            return result

        # Step 2: Markdown -> OpenAI Extraction
        if verbose:
            print(f"  [2/4] OpenAI extraction...")
        try:
            result.extracted_data = self.extractor.extract_from_markdown(
                result.markdown,
                source_file=str(pdf_path)
            )
            if "error" in result.extracted_data:
                errors.append(result.extracted_data["error"])
        except Exception as e:
            errors.append(f"Extraction error: {e}")
            result.errors = errors
            return result

        # Get basic info
        result.company = result.extracted_data.get("company", "Unknown")
        result.quarter = result.extracted_data.get("quarter", "")
        result.year = result.extracted_data.get("year", 0)

        # Step 3: Claude Review
        if verbose:
            print(f"  [3/4] Claude review: {result.company}...")
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

        # Step 4: Claude Normalize
        if verbose:
            print(f"  [4/4] Claude normalize...")
        try:
            result.normalized_data = self.normalizer.normalize(result.validated_data)
            if "error" in result.normalized_data:
                errors.append(result.normalized_data["error"])
        except Exception as e:
            errors.append(f"Normalize error: {e}")

        result.errors = errors
        return result

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
