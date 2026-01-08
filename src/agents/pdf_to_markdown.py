"""PDF to Markdown converter using LlamaParse API (with pdfplumber fallback)."""

from __future__ import annotations

import html
import os
import re
import time
import httpx
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

LLAMA_CLOUD_API_KEY = os.getenv("LLAMA_CLOUD_API_KEY")
LLAMAPARSE_API_URL = "https://api.cloud.llamaindex.ai/api/parsing"

# Strict parsing instruction to avoid hallucinations
PARSING_INSTRUCTION = """
STRICT EXTRACTION RULES - FOLLOW EXACTLY:

1. ONLY extract text and tables that are EXPLICITLY visible in the PDF
2. DO NOT generate, infer, or hallucinate any content
3. DO NOT add placeholder values like "X%", "€X", "N/A" if data is not in the document
4. DO NOT create summary sections or conclusions that are not in the original
5. DO NOT add any commentary about the document
6. If a table cell is empty in the PDF, leave it empty in the output

For financial tables:
- Preserve exact numerical values as shown (with commas, decimals, currency symbols)
- Preserve exact column headers and row labels
- Preserve percentage signs and +/- indicators exactly as shown
- Keep table structure intact with proper alignment

Output format:
- Use markdown headers (##, ###) for section titles from the document
- Use markdown tables for tabular data
- Use bullet points for lists
- Preserve paragraph breaks as in original

DO NOT ADD ANY CONTENT THAT IS NOT IN THE ORIGINAL PDF.
"""

# Fallback to pdfplumber
try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except ImportError:
    HAS_PDFPLUMBER = False


def clean_markdown(content: str) -> str:
    """
    Clean up markdown content from LlamaParse.

    - Decode HTML entities
    - Remove hallucinated sections
    - Clean up formatting
    """
    # Decode HTML entities (&#x26; -> &, etc.)
    content = html.unescape(content)

    # Also handle numeric HTML entities that might be missed
    content = re.sub(r'&#(\d+);', lambda m: chr(int(m.group(1))), content)
    content = re.sub(r'&#x([0-9a-fA-F]+);', lambda m: chr(int(m.group(1), 16)), content)

    # Remove lines with obvious placeholder patterns
    lines = content.split('\n')
    cleaned_lines = []
    skip_section = False

    for line in lines:
        # Detect hallucinated placeholder patterns
        if re.search(r'\|\s*€?[XYZ]\s*\||\|\s*[XYZ]%\s*\|', line):
            skip_section = True
            continue

        # Detect "It appears that" hallucination patterns
        if 'It appears that' in line or 'If you have a specific' in line:
            skip_section = True
            continue

        # Reset skip on new major section
        if line.startswith('# ') or line.startswith('## ') or line.startswith('---'):
            skip_section = False

        if not skip_section:
            cleaned_lines.append(line)

    content = '\n'.join(cleaned_lines)

    # Remove multiple consecutive blank lines
    content = re.sub(r'\n{3,}', '\n\n', content)

    # Remove trailing whitespace on lines
    content = '\n'.join(line.rstrip() for line in content.split('\n'))

    return content.strip()


def pdf_to_markdown_llamaparse(pdf_path: Path) -> str:
    """
    Convert PDF to Markdown using LlamaParse API directly.

    Uses httpx to call the API without the llama-parse library.
    """
    if not LLAMA_CLOUD_API_KEY:
        raise ValueError("LLAMA_CLOUD_API_KEY not set")

    headers = {
        "Authorization": f"Bearer {LLAMA_CLOUD_API_KEY}",
        "Accept": "application/json",
    }

    # Step 1: Upload the PDF with strict parsing settings
    print(f"  [LlamaParse] Uploading {pdf_path.name}...")
    with open(pdf_path, "rb") as f:
        files = {"file": (pdf_path.name, f, "application/pdf")}
        data = {
            "parsing_instruction": PARSING_INSTRUCTION,
            "result_type": "markdown",
            "skip_diagonal_text": "true",
            "do_not_unroll_columns": "false",
            "invalidate_cache": "false",
        }

        with httpx.Client(timeout=120.0) as client:
            response = client.post(
                f"{LLAMAPARSE_API_URL}/upload",
                headers=headers,
                files=files,
                data=data,
            )
            response.raise_for_status()
            upload_result = response.json()

    job_id = upload_result.get("id")
    if not job_id:
        raise ValueError(f"No job ID returned: {upload_result}")

    print(f"  [LlamaParse] Job ID: {job_id}")

    # Step 2: Poll for completion
    print(f"  [LlamaParse] Processing", end="", flush=True)
    with httpx.Client(timeout=30.0) as client:
        max_attempts = 60  # 5 minutes max
        for attempt in range(max_attempts):
            response = client.get(
                f"{LLAMAPARSE_API_URL}/job/{job_id}",
                headers=headers,
            )
            response.raise_for_status()
            status_result = response.json()

            status = status_result.get("status")
            if status == "SUCCESS":
                print(" Done!")
                break
            elif status in ("ERROR", "FAILED"):
                print(" Failed!")
                raise ValueError(f"LlamaParse job failed: {status_result}")

            print(".", end="", flush=True)
            time.sleep(3)  # Wait 3 seconds before next poll
        else:
            print(" Timeout!")
            raise TimeoutError("LlamaParse job timed out after 5 minutes")

    # Step 3: Get the markdown result
    print(f"  [LlamaParse] Downloading result...")
    with httpx.Client(timeout=60.0) as client:
        response = client.get(
            f"{LLAMAPARSE_API_URL}/job/{job_id}/result/markdown",
            headers=headers,
        )
        response.raise_for_status()
        result = response.json()

    markdown_content = result.get("markdown", "")
    if not markdown_content:
        raise ValueError(f"No markdown content returned: {result}")

    # Clean up the content
    markdown_content = clean_markdown(markdown_content)

    # Add title
    final_content = f"# {pdf_path.stem}\n\n{markdown_content}"
    print(f"  [LlamaParse] Done ({len(final_content):,} chars)")

    return final_content


def pdf_to_markdown_pdfplumber(pdf_path: Path) -> str:
    """
    Convert PDF to Markdown using pdfplumber (fallback).
    """
    markdown_parts = []
    markdown_parts.append(f"# {pdf_path.stem}\n")

    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, 1):
            markdown_parts.append(f"\n## Page {page_num}\n")

            text = page.extract_text()
            if text:
                markdown_parts.append(text)
                markdown_parts.append("\n")

            tables = page.extract_tables()
            for table_idx, table in enumerate(tables):
                if table and len(table) > 0:
                    markdown_parts.append(f"\n### Table {table_idx + 1}\n")
                    markdown_parts.append(table_to_markdown(table))
                    markdown_parts.append("\n")

    return "\n".join(markdown_parts)


def table_to_markdown(table: list[list]) -> str:
    """Convert a pdfplumber table to Markdown table format."""
    if not table or len(table) == 0:
        return ""

    cleaned_table = []
    for row in table:
        cleaned_row = []
        for cell in row:
            if cell is None:
                cleaned_row.append("")
            else:
                cleaned_row.append(str(cell).replace("\n", " ").strip())
        cleaned_table.append(cleaned_row)

    if not cleaned_table:
        return ""

    max_cols = max(len(row) for row in cleaned_table)

    for row in cleaned_table:
        while len(row) < max_cols:
            row.append("")

    lines = []
    header = cleaned_table[0]
    lines.append("| " + " | ".join(header) + " |")
    lines.append("| " + " | ".join(["---"] * max_cols) + " |")

    for row in cleaned_table[1:]:
        lines.append("| " + " | ".join(row) + " |")

    return "\n".join(lines)


def pdf_to_markdown(pdf_path: Path, use_llamaparse: bool = True) -> str:
    """
    Convert a PDF to structured Markdown.

    Args:
        pdf_path: Path to the PDF file
        use_llamaparse: Whether to use LlamaParse API (default: True)

    Returns:
        Markdown content from the PDF
    """
    pdf_path = Path(pdf_path)

    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    # Try LlamaParse first if available and requested
    if use_llamaparse and LLAMA_CLOUD_API_KEY:
        try:
            return pdf_to_markdown_llamaparse(pdf_path)
        except Exception as e:
            print(f"  [LlamaParse] Error: {e}")
            if HAS_PDFPLUMBER:
                print(f"  [LlamaParse] Falling back to pdfplumber...")
            else:
                raise

    # Fallback to pdfplumber
    if HAS_PDFPLUMBER:
        return pdf_to_markdown_pdfplumber(pdf_path)

    raise RuntimeError(
        "No PDF parser available. Set LLAMA_CLOUD_API_KEY or install pdfplumber."
    )


def convert_pdf(pdf_path: str | Path, use_llamaparse: bool = True) -> str:
    """Utility function to convert a PDF."""
    return pdf_to_markdown(Path(pdf_path), use_llamaparse=use_llamaparse)
