#!/usr/bin/env python3
"""Pipeline orchestrator for quarterly financial analysis.

Workflow:
0. Download PDFs from Google Drive to data/raw/<quarter>/
1. Convert PDFs to Markdown (pdfplumber/LlamaParse)
2. [Manual] Use Claude Code to extract, validate, and format insights
   - Read markdowns from data/markdown/<quarter>/
   - Use prompts from prompts/ to guide extraction
   - Write results to data/insights/<quarter>/
3. Upload results to Google Drive

Usage:
    python run_pipeline.py --quarter Q4 --all             # Run steps 0, 1, 3
    python run_pipeline.py --quarter Q4 --steps 0         # Download from Drive
    python run_pipeline.py --quarter Q4 --steps 0,1       # Download + convert
    python run_pipeline.py --quarter Q4 --steps 3          # Upload only
    python run_pipeline.py --quarter Q4 --company Amazon   # Single company
    python run_pipeline.py --help                          # Show help
"""

import subprocess
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent

STEPS = {
    0: {
        "name": "Download PDFs from Drive",
        "script": "00_download_from_drive.py",
        "description": "Downloads PDF earnings reports from Google Drive",
    },
    1: {
        "name": "Convert PDFs to Markdown",
        "script": "01_convert_pdfs.py",
        "description": "Converts PDF earnings reports to Markdown files",
    },
    3: {
        "name": "Upload to Drive",
        "script": "05_upload_to_drive.py",
        "description": "Uploads insights and reports to Google Drive",
    },
}


def print_help():
    """Print usage information."""
    print(__doc__)
    print("\nAutomated steps:")
    for num, info in sorted(STEPS.items()):
        print(f"  {num}. {info['name']} - {info['description']}")
    print()
    print("Manual step (via Claude Code):")
    print("  2. Extract, validate, and format insights using prompts/")
    print("     Read data/markdown/<quarter>/, write to data/insights/<quarter>/")
    print()


def run_step(step_num: int, quarter: str, extra_args: list = None) -> bool:
    """Run a single pipeline step."""
    if step_num not in STEPS:
        print(f"Invalid step: {step_num}")
        return False

    step = STEPS[step_num]
    script_path = SCRIPTS_DIR / step["script"]

    if not script_path.exists():
        print(f"Script not found: {script_path}")
        return False

    print(f"\n{'='*60}")
    print(f"STEP {step_num}: {step['name']}")
    print(f"Script: {step['script']}")
    print(f"{'='*60}\n")

    cmd = [sys.executable, str(script_path), "--quarter", quarter]

    if extra_args:
        cmd.extend(extra_args)

    try:
        result = subprocess.run(cmd, check=False)
        if result.returncode != 0:
            print(f"\n[WARNING] Step {step_num} exited with code {result.returncode}")
            return False
        return True
    except Exception as e:
        print(f"\n[ERROR] Step {step_num} failed: {e}")
        return False


def run_pipeline(quarter: str, steps: list[int], company: str = None):
    """Run the pipeline with specified steps."""
    print(f"{'#'*60}")
    print(f"# QUARTERLY ANALYSIS PIPELINE")
    print(f"# Quarter: {quarter}")
    if company:
        print(f"# Company: {company}")
    print(f"# Steps: {', '.join(str(s) for s in steps)}")
    print(f"{'#'*60}")

    extra_args = []
    if company:
        extra_args.extend(["--company", company])

    results = {}

    for step_num in steps:
        if step_num == 2:
            print(f"\n{'='*60}")
            print("STEP 2: Extract & Validate Insights (MANUAL)")
            print(f"Use Claude Code with prompts/ to analyze data/markdown/{quarter}/")
            print(f"Write results to data/insights/{quarter}/<company>/")
            print(f"{'='*60}\n")
            continue

        success = run_step(step_num, quarter, extra_args)
        results[step_num] = success

        if not success:
            print(f"\n[WARNING] Step {step_num} had issues. Continuing...")

    # Summary
    print(f"\n{'='*60}")
    print("PIPELINE SUMMARY")
    print(f"{'='*60}")

    for step_num in steps:
        if step_num == 2:
            print(f"  Step 2: Extract & Validate (manual via Claude Code)")
        else:
            status = "OK" if results.get(step_num) else "ISSUES"
            step_name = STEPS[step_num]["name"]
            print(f"  Step {step_num}: {step_name} - [{status}]")

    success_count = sum(1 for v in results.values() if v)
    automated = len([s for s in steps if s != 2])
    print(f"\nAutomated: {success_count}/{automated} steps completed")


def parse_args(args: list) -> dict:
    """Parse command line arguments."""
    result = {
        "quarter": "Q4",
        "steps": [0, 1, 2, 3],
        "company": None,
        "help": False,
    }

    i = 0
    while i < len(args):
        if args[i] in ("--help", "-h"):
            result["help"] = True
            i += 1
        elif args[i] == "--quarter" and i + 1 < len(args):
            result["quarter"] = args[i + 1]
            i += 2
        elif args[i] == "--company" and i + 1 < len(args):
            result["company"] = args[i + 1]
            i += 2
        elif args[i] == "--steps" and i + 1 < len(args):
            steps_str = args[i + 1]
            result["steps"] = [int(s.strip()) for s in steps_str.split(",")]
            i += 2
        elif args[i] == "--all":
            result["steps"] = [0, 1, 2, 3]
            i += 1
        else:
            i += 1

    return result


if __name__ == "__main__":
    parsed = parse_args(sys.argv[1:])

    if parsed["help"]:
        print_help()
        sys.exit(0)

    run_pipeline(
        quarter=parsed["quarter"],
        steps=parsed["steps"],
        company=parsed["company"],
    )
