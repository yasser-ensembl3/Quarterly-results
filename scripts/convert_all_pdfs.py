#!/usr/bin/env python3
"""Batch convert all PDFs to Markdown using LlamaParse."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agents.pdf_to_markdown import pdf_to_markdown

# Directories
RAW_DIR = Path(__file__).parent.parent / "data" / "raw" / "Q3"
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "markdown" / "Q3"


def get_all_pdfs():
    """Get all PDFs from the raw directory."""
    return list(RAW_DIR.rglob("*.pdf"))


def get_output_path(pdf_path: Path) -> Path:
    """Get the output markdown path for a PDF."""
    # Get relative path from RAW_DIR
    rel_path = pdf_path.relative_to(RAW_DIR)
    # Change extension to .md
    output_path = OUTPUT_DIR / rel_path.with_suffix(".md")
    return output_path


def is_already_converted(pdf_path: Path) -> bool:
    """Check if a PDF has already been converted."""
    output_path = get_output_path(pdf_path)
    return output_path.exists()


def convert_pdf_to_markdown(pdf_path: Path) -> bool:
    """Convert a single PDF to markdown."""
    output_path = get_output_path(pdf_path)

    # Create output directory if needed
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        print(f"\n{'='*60}")
        print(f"Converting: {pdf_path.name}")
        print(f"Output: {output_path}")

        markdown_content = pdf_to_markdown(pdf_path, use_llamaparse=True)

        # Write to file
        output_path.write_text(markdown_content, encoding="utf-8")

        print(f"SUCCESS: {len(markdown_content):,} characters written")
        return True

    except Exception as e:
        print(f"ERROR: {e}")
        return False


def main():
    """Main function to convert all PDFs."""
    all_pdfs = get_all_pdfs()
    print(f"Found {len(all_pdfs)} PDFs in {RAW_DIR}")

    # Filter out already converted
    pdfs_to_convert = [p for p in all_pdfs if not is_already_converted(p)]
    already_converted = len(all_pdfs) - len(pdfs_to_convert)

    print(f"Already converted: {already_converted}")
    print(f"To convert: {len(pdfs_to_convert)}")

    if not pdfs_to_convert:
        print("\nAll PDFs already converted!")
        return

    # Show what will be converted
    print("\nPDFs to convert:")
    for pdf in pdfs_to_convert:
        print(f"  - {pdf.parent.name}/{pdf.name}")

    # Convert each PDF
    successes = 0
    failures = []

    for i, pdf_path in enumerate(pdfs_to_convert, 1):
        print(f"\n[{i}/{len(pdfs_to_convert)}]")
        if convert_pdf_to_markdown(pdf_path):
            successes += 1
        else:
            failures.append(pdf_path)

    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"Total processed: {len(pdfs_to_convert)}")
    print(f"Successes: {successes}")
    print(f"Failures: {len(failures)}")

    if failures:
        print("\nFailed files:")
        for f in failures:
            print(f"  - {f.parent.name}/{f.name}")


if __name__ == "__main__":
    main()
