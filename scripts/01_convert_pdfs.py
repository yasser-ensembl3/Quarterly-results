#!/usr/bin/env python3
"""Batch convert all PDFs to Markdown using LlamaParse.

Usage:
    python 01_convert_pdfs.py                    # Default Q3
    python 01_convert_pdfs.py --quarter Q4       # Different quarter
    python 01_convert_pdfs.py --force            # Re-convert all
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agents.pdf_to_markdown import pdf_to_markdown

# Base directories
DATA_DIR = Path(__file__).parent.parent / "data"
DEFAULT_QUARTER = "Q3"


def get_all_pdfs(raw_dir: Path):
    """Get all PDFs from the raw directory."""
    return list(raw_dir.rglob("*.pdf"))


def get_output_path(pdf_path: Path, raw_dir: Path, output_dir: Path) -> Path:
    """Get the output markdown path for a PDF."""
    # Get relative path from RAW_DIR
    rel_path = pdf_path.relative_to(raw_dir)
    # Change extension to .md
    output_path = output_dir / rel_path.with_suffix(".md")
    return output_path


def is_already_converted(pdf_path: Path, raw_dir: Path, output_dir: Path) -> bool:
    """Check if a PDF has already been converted."""
    output_path = get_output_path(pdf_path, raw_dir, output_dir)
    return output_path.exists()


def convert_pdf_to_markdown(pdf_path: Path, raw_dir: Path, output_dir: Path) -> bool:
    """Convert a single PDF to markdown."""
    output_path = get_output_path(pdf_path, raw_dir, output_dir)

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


def main(quarter: str = DEFAULT_QUARTER, force: bool = False):
    """Main function to convert all PDFs."""
    raw_dir = DATA_DIR / "raw" / quarter
    output_dir = DATA_DIR / "markdown" / quarter

    if not raw_dir.exists():
        print(f"ERROR: Raw directory not found: {raw_dir}")
        return

    all_pdfs = get_all_pdfs(raw_dir)
    print(f"Found {len(all_pdfs)} PDFs in {raw_dir}")

    # Filter out already converted (unless force)
    if force:
        pdfs_to_convert = all_pdfs
        already_converted = 0
    else:
        pdfs_to_convert = [p for p in all_pdfs if not is_already_converted(p, raw_dir, output_dir)]
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
        if convert_pdf_to_markdown(pdf_path, raw_dir, output_dir):
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
    # Parse arguments
    quarter = DEFAULT_QUARTER
    force = False

    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--quarter" and i + 1 < len(args):
            quarter = args[i + 1]
            i += 2
        elif args[i] == "--force":
            force = True
            i += 1
        else:
            i += 1

    main(quarter=quarter, force=force)
