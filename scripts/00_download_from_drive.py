#!/usr/bin/env python3
"""Download PDF earnings reports from Google Drive.

Downloads all PDFs from Drive/<quarter>/<company>/ into data/raw/<quarter>/<company>/.
Skips files that already exist locally and are up to date.

Usage:
    python 00_download_from_drive.py --quarter Q4           # Download all Q4 PDFs
    python 00_download_from_drive.py --quarter Q4 --force   # Re-download all
    python 00_download_from_drive.py --quarter Q4 --company Amazon  # Single company
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io

# Load environment variables
load_dotenv(Path(__file__).parent.parent / ".env")

DATA_DIR = Path(__file__).parent.parent / "data"
RAW_DIR = DATA_DIR / "raw"
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


def list_folder(service, folder_id: str) -> list[dict]:
    """List contents of a Drive folder."""
    results = []
    page_token = None

    while True:
        response = service.files().list(
            q=f"'{folder_id}' in parents and trashed = false",
            spaces="drive",
            fields="nextPageToken, files(id, name, mimeType, modifiedTime, size)",
            pageToken=page_token,
        ).execute()

        results.extend(response.get("files", []))
        page_token = response.get("nextPageToken")
        if not page_token:
            break

    return results


def find_folder(service, parent_id: str, folder_name: str) -> str | None:
    """Find a folder by name within a parent folder."""
    query = (
        f"'{parent_id}' in parents and name = '{folder_name}' "
        f"and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    )
    results = service.files().list(q=query, fields="files(id, name)").execute()
    files = results.get("files", [])
    return files[0]["id"] if files else None


def download_file(service, file_id: str, destination: Path) -> None:
    """Download a file from Google Drive."""
    destination.parent.mkdir(parents=True, exist_ok=True)

    request = service.files().get_media(fileId=file_id)
    file_handle = io.BytesIO()
    downloader = MediaIoBaseDownload(file_handle, request)

    done = False
    while not done:
        _, done = downloader.next_chunk()

    with open(destination, "wb") as f:
        f.write(file_handle.getvalue())


def download_quarter(
    quarter: str = DEFAULT_QUARTER,
    company_filter: str | None = None,
    force: bool = False,
):
    """Download PDFs from Drive for a given quarter.

    Args:
        quarter: Quarter identifier (e.g., Q3, Q4)
        company_filter: If set, only download this company
        force: Re-download even if file exists locally
    """
    root_folder_id = os.environ.get("GDRIVE_ROOT_FOLDER_ID")
    if not root_folder_id:
        print("ERROR: GDRIVE_ROOT_FOLDER_ID not set in .env")
        return

    print(f"Root folder ID: {root_folder_id}")
    print(f"Quarter: {quarter}")
    if company_filter:
        print(f"Company filter: {company_filter}")

    # Connect to Drive
    print("\nConnecting to Google Drive...")
    service = get_drive_service()

    # Find quarter folder
    quarter_folder_id = find_folder(service, root_folder_id, quarter)
    if not quarter_folder_id:
        print(f"ERROR: Quarter folder '{quarter}' not found in Drive")
        return

    print(f"Quarter folder found: {quarter_folder_id}")

    # List company folders
    items = list_folder(service, quarter_folder_id)
    company_folders = [
        item for item in items
        if item["mimeType"] == "application/vnd.google-apps.folder"
    ]

    if company_filter:
        company_folders = [
            f for f in company_folders
            if f["name"].lower() == company_filter.lower()
        ]
        if not company_folders:
            print(f"ERROR: Company '{company_filter}' not found in {quarter}")
            return

    print(f"Found {len(company_folders)} companies")

    total_downloaded = 0
    total_skipped = 0
    total_errors = 0

    for company_folder in sorted(company_folders, key=lambda x: x["name"]):
        company_name = company_folder["name"]
        company_id = company_folder["id"]
        local_dir = RAW_DIR / quarter / company_name

        print(f"\n[{company_name}]")

        # List files in company folder
        files = list_folder(service, company_id)
        pdf_files = [f for f in files if f["name"].lower().endswith(".pdf")]

        if not pdf_files:
            print("  No PDF files found")
            continue

        for pdf_file in pdf_files:
            local_path = local_dir / pdf_file["name"]

            # Skip if already exists (unless force)
            if local_path.exists() and not force:
                print(f"  [SKIP] {pdf_file['name']} (already exists)")
                total_skipped += 1
                continue

            try:
                print(f"  [DL] {pdf_file['name']}...", end="", flush=True)
                download_file(service, pdf_file["id"], local_path)
                size_kb = local_path.stat().st_size / 1024
                print(f" ({size_kb:.0f} KB)")
                total_downloaded += 1
            except Exception as e:
                print(f" ERROR: {e}")
                total_errors += 1

    # Summary
    print(f"\n{'='*50}")
    print("SUMMARY")
    print(f"{'='*50}")
    print(f"Downloaded: {total_downloaded} files")
    print(f"Skipped: {total_skipped} files (already exist)")
    print(f"Errors: {total_errors}")
    print(f"Output: {RAW_DIR / quarter}/")


if __name__ == "__main__":
    quarter = DEFAULT_QUARTER
    company_filter = None
    force = False

    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--quarter" and i + 1 < len(args):
            quarter = args[i + 1]
            i += 2
        elif args[i] == "--company" and i + 1 < len(args):
            company_filter = args[i + 1]
            i += 2
        elif args[i] == "--force":
            force = True
            i += 1
        else:
            i += 1

    download_quarter(quarter=quarter, company_filter=company_filter, force=force)
