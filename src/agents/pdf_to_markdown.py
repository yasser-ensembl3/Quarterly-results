"""PDF to Markdown converter using pdfplumber."""

from __future__ import annotations

from pathlib import Path

import pdfplumber


def pdf_to_markdown(pdf_path: Path) -> str:
    """
    Convert a PDF to structured Markdown.

    Args:
        pdf_path: Path to the PDF file

    Returns:
        Markdown content from the PDF
    """
    pdf_path = Path(pdf_path)

    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    markdown_parts = []
    markdown_parts.append(f"# {pdf_path.stem}\n")

    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, 1):
            markdown_parts.append(f"\n## Page {page_num}\n")

            # Extract text
            text = page.extract_text()
            if text:
                markdown_parts.append(text)
                markdown_parts.append("\n")

            # Extract tables
            tables = page.extract_tables()
            for table_idx, table in enumerate(tables):
                if table and len(table) > 0:
                    markdown_parts.append(f"\n### Table {table_idx + 1}\n")
                    markdown_parts.append(table_to_markdown(table))
                    markdown_parts.append("\n")

    return "\n".join(markdown_parts)


def table_to_markdown(table: list[list]) -> str:
    """
    Convert a pdfplumber table to Markdown table format.

    Args:
        table: List of lists (rows and cells)

    Returns:
        Table in Markdown format
    """
    if not table or len(table) == 0:
        return ""

    # Clean cells
    cleaned_table = []
    for row in table:
        cleaned_row = []
        for cell in row:
            if cell is None:
                cleaned_row.append("")
            else:
                # Clean text (remove newlines)
                cleaned_row.append(str(cell).replace("\n", " ").strip())
        cleaned_table.append(cleaned_row)

    if not cleaned_table:
        return ""

    # Find max number of columns
    max_cols = max(len(row) for row in cleaned_table)

    # Normalize all rows to same number of columns
    for row in cleaned_table:
        while len(row) < max_cols:
            row.append("")

    # Build markdown
    lines = []

    # Header (first row)
    header = cleaned_table[0]
    lines.append("| " + " | ".join(header) + " |")

    # Separator
    lines.append("| " + " | ".join(["---"] * max_cols) + " |")

    # Data rows
    for row in cleaned_table[1:]:
        lines.append("| " + " | ".join(row) + " |")

    return "\n".join(lines)


def convert_pdf(pdf_path: str | Path) -> str:
    """Utility function to convert a PDF."""
    return pdf_to_markdown(Path(pdf_path))
