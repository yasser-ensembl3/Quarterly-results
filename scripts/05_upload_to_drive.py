#!/usr/bin/env python3
"""Upload markdown and insight files to Google Drive.

Uploads:
- Intermediate markdown files (PDF conversions) from data/markdown/<quarter>/
- Insight files (JSON + MD) from data/insights/<quarter>/

Files are uploaded to Drive/<quarter>/<company>/ (same folder as source PDFs).

Usage:
    python 05_upload_to_drive.py --quarter Q4                  # Upload both
    python 05_upload_to_drive.py --quarter Q4 --markdown-only  # Only PDF conversions
    python 05_upload_to_drive.py --quarter Q4 --insights-only  # Only insights
    python 05_upload_to_drive.py --quarter Q4 --company Amazon # Single company
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Load environment variables
load_dotenv(Path(__file__).parent.parent / ".env")

DATA_DIR = Path(__file__).parent.parent / "data"
INSIGHTS_DIR = DATA_DIR / "insights"
MARKDOWN_DIR = DATA_DIR / "markdown"
DEFAULT_QUARTER = "Q4"


def get_drive_service():
    """Get authenticated Google Drive service."""
    client_id = os.environ.get("GOOGLE_CLIENT_ID")
    client_secret = os.environ.get("GOOGLE_CLIENT_SECRET")
    refresh_token = os.environ.get("GOOGLE_REFRESH_TOKEN")

    if not all([client_id, refresh_token]):
        raise ValueError("Google credentials not configured in .env")

    creds = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret or "",
    )

    return build("drive", "v3", credentials=creds)


def find_folder(service, parent_id: str, folder_name: str) -> str | None:
    """Find a folder by name within a parent folder."""
    query = f"'{parent_id}' in parents and name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    results = service.files().list(q=query, fields="files(id, name)").execute()
    files = results.get("files", [])
    return files[0]["id"] if files else None


def find_file(service, parent_id: str, filename: str) -> str | None:
    """Find a file by name in a folder."""
    query = f"'{parent_id}' in parents and name = '{filename}' and trashed = false"
    results = service.files().list(q=query, fields="files(id, name)").execute()
    files = results.get("files", [])
    return files[0]["id"] if files else None


def upload_file(service, local_path: Path, parent_folder_id: str) -> str:
    """Upload or update a file in Google Drive."""
    mime_types = {
        '.json': 'application/json',
        '.md': 'text/markdown',
    }
    mime_type = mime_types.get(local_path.suffix.lower(), 'application/octet-stream')

    # Check if file already exists
    existing_id = find_file(service, parent_folder_id, local_path.name)

    media = MediaFileUpload(str(local_path), mimetype=mime_type)

    if existing_id:
        # Update existing file
        file = service.files().update(
            fileId=existing_id,
            media_body=media
        ).execute()
        return file.get('id')
    else:
        # Create new file
        file_metadata = {
            'name': local_path.name,
            'parents': [parent_folder_id]
        }
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()
        return file.get('id')


def create_folder(service, parent_id: str, folder_name: str) -> str:
    """Create a folder in Google Drive."""
    file_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder',
        'parents': [parent_id]
    }
    folder = service.files().create(body=file_metadata, fields='id').execute()
    return folder.get('id')


def get_or_create_folder(service, parent_id: str, folder_name: str) -> str:
    """Get existing folder or create new one."""
    folder_id = find_folder(service, parent_id, folder_name)
    if not folder_id:
        folder_id = create_folder(service, parent_id, folder_name)
        print(f"  Created folder: {folder_name}")
    return folder_id


def upload_markdown_files(
    service, quarter_folder_id: str, quarter: str, company_filter: str | None = None
) -> tuple[int, int]:
    """Upload intermediate markdown files (PDF conversions)."""
    markdown_quarter_dir = MARKDOWN_DIR / quarter

    if not markdown_quarter_dir.exists():
        print(f"Markdown directory not found: {markdown_quarter_dir}")
        return 0, 0

    companies = [d for d in markdown_quarter_dir.iterdir() if d.is_dir()]

    if company_filter:
        companies = [
            d for d in companies if d.name.lower() == company_filter.lower()
        ]
        if not companies:
            print(f"Company '{company_filter}' not found in {markdown_quarter_dir}")
            return 0, 0

    print(f"\nUploading markdown files for {len(companies)} companies...")

    total_uploaded = 0
    total_errors = 0

    for company_dir in sorted(companies, key=lambda d: d.name):
        company_name = company_dir.name
        print(f"\n[{company_name}] (markdown)")

        # Get or create company folder in Drive
        company_folder_id = get_or_create_folder(service, quarter_folder_id, company_name)

        # Get or create 'markdown' subfolder
        markdown_subfolder_id = get_or_create_folder(service, company_folder_id, "markdown")

        # Get all markdown files
        files = list(company_dir.glob("*.md"))

        if not files:
            print("  No markdown files to upload")
            continue

        for file_path in sorted(files, key=lambda f: f.name):
            try:
                upload_file(service, file_path, markdown_subfolder_id)
                print(f"  [OK] {file_path.name}")
                total_uploaded += 1
            except Exception as e:
                print(f"  [ERR] {file_path.name}: {e}")
                total_errors += 1

    return total_uploaded, total_errors


def upload_insight_files(
    service, quarter_folder_id: str, quarter: str, company_filter: str | None = None
) -> tuple[int, int]:
    """Upload insight files (JSON + formatted MD).

    Looks for insights in data/insights/<quarter>/<company>/.
    Uploads directly to Drive/<quarter>/<company>/ (alongside source PDFs).
    """
    insights_quarter_dir = INSIGHTS_DIR / quarter

    if not insights_quarter_dir.exists():
        print(f"Insights directory not found: {insights_quarter_dir}")
        return 0, 0

    companies = [d for d in insights_quarter_dir.iterdir() if d.is_dir()]

    if company_filter:
        companies = [
            d for d in companies if d.name.lower() == company_filter.lower()
        ]
        if not companies:
            print(f"Company '{company_filter}' not found in {insights_quarter_dir}")
            return 0, 0

    print(f"\nUploading insights for {len(companies)} companies...")

    total_uploaded = 0
    total_errors = 0

    for company_dir in sorted(companies, key=lambda d: d.name):
        company_name = company_dir.name
        print(f"\n[{company_name}] (insights)")

        # Get or create company folder in Drive
        company_folder_id = get_or_create_folder(service, quarter_folder_id, company_name)

        # Get all files (JSON + MD) - upload directly to company folder
        files = list(company_dir.glob("*.json")) + list(company_dir.glob("*.md"))

        if not files:
            print("  No insight files to upload")
            continue

        for file_path in sorted(files, key=lambda f: f.name):
            try:
                upload_file(service, file_path, company_folder_id)
                print(f"  [OK] {file_path.name}")
                total_uploaded += 1
            except Exception as e:
                print(f"  [ERR] {file_path.name}: {e}")
                total_errors += 1

    return total_uploaded, total_errors


def upload_all(
    quarter: str = DEFAULT_QUARTER,
    markdown_only: bool = False,
    insights_only: bool = False,
    company_filter: str | None = None,
):
    """Upload files to Google Drive.

    Args:
        quarter: Quarter identifier (e.g., Q3, Q4)
        markdown_only: Only upload intermediate markdown files
        insights_only: Only upload insight files
        company_filter: If set, only upload this company
    """
    root_folder_id = os.environ.get("GDRIVE_ROOT_FOLDER_ID")
    if not root_folder_id:
        print("ERROR: GDRIVE_ROOT_FOLDER_ID not set in .env")
        return

    print(f"Root folder ID: {root_folder_id}")
    print(f"Quarter: {quarter}")
    if company_filter:
        print(f"Company: {company_filter}")

    upload_types = []
    if not insights_only:
        upload_types.append("markdown")
    if not markdown_only:
        upload_types.append("insights")
    print(f"Uploading: {', '.join(upload_types)}")

    # Initialize Drive service
    print("\nConnecting to Google Drive...")
    service = get_drive_service()

    # Get or create quarter folder
    quarter_folder_id = get_or_create_folder(service, root_folder_id, quarter)
    print(f"Quarter folder: {quarter_folder_id}")

    total_uploaded = 0
    total_errors = 0

    # Upload markdown files (PDF conversions)
    if not insights_only:
        uploaded, errors = upload_markdown_files(
            service, quarter_folder_id, quarter, company_filter
        )
        total_uploaded += uploaded
        total_errors += errors

    # Upload insight files
    if not markdown_only:
        uploaded, errors = upload_insight_files(
            service, quarter_folder_id, quarter, company_filter
        )
        total_uploaded += uploaded
        total_errors += errors

    print(f"\n{'='*50}")
    print("SUMMARY")
    print(f"{'='*50}")
    print(f"Uploaded: {total_uploaded} files")
    print(f"Errors: {total_errors}")


if __name__ == "__main__":
    # Parse arguments
    quarter = DEFAULT_QUARTER
    markdown_only = False
    insights_only = False
    company_filter = None

    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--quarter" and i + 1 < len(args):
            quarter = args[i + 1]
            i += 2
        elif args[i] == "--company" and i + 1 < len(args):
            company_filter = args[i + 1]
            i += 2
        elif args[i] == "--markdown-only":
            markdown_only = True
            i += 1
        elif args[i] == "--insights-only":
            insights_only = True
            i += 1
        else:
            i += 1

    upload_all(
        quarter=quarter,
        markdown_only=markdown_only,
        insights_only=insights_only,
        company_filter=company_filter,
    )
