#!/usr/bin/env python3
"""Upload insight files (JSON + MD) to Google Drive - standalone version."""

import os
from pathlib import Path

from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Load environment variables
load_dotenv(Path(__file__).parent.parent / ".env")

INSIGHTS_DIR = Path(__file__).parent.parent / "data" / "insights"
QUARTER = "Q3"


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


def upload_all_insights():
    """Upload all insight files to Google Drive."""
    root_folder_id = os.environ.get("GDRIVE_ROOT_FOLDER_ID")
    if not root_folder_id:
        print("ERROR: GDRIVE_ROOT_FOLDER_ID not set in .env")
        return

    print(f"Root folder ID: {root_folder_id}")
    print(f"Quarter: {QUARTER}")

    # Initialize Drive service
    print("\nConnecting to Google Drive...")
    service = get_drive_service()

    # Find quarter folder
    quarter_folder_id = find_folder(service, root_folder_id, QUARTER)
    if not quarter_folder_id:
        print(f"ERROR: Quarter folder '{QUARTER}' not found in Drive")
        return

    print(f"Quarter folder found: {quarter_folder_id}")

    # Get all company folders
    companies = [d for d in INSIGHTS_DIR.iterdir() if d.is_dir()]
    print(f"\nFound {len(companies)} companies to upload")

    total_uploaded = 0
    total_errors = 0

    for company_dir in companies:
        company_name = company_dir.name
        print(f"\n[{company_name}]")

        # Find company folder in Drive
        company_folder_id = find_folder(service, quarter_folder_id, company_name)
        if not company_folder_id:
            print(f"  ✗ Company folder not found in Drive")
            total_errors += 1
            continue

        # Get all files (JSON + MD)
        files = list(company_dir.glob("*.json")) + list(company_dir.glob("*.md"))

        if not files:
            print("  No files to upload")
            continue

        for file_path in files:
            try:
                file_id = upload_file(service, file_path, company_folder_id)
                print(f"  ✓ {file_path.name}")
                total_uploaded += 1
            except Exception as e:
                print(f"  ✗ {file_path.name}: {e}")
                total_errors += 1

    print(f"\n{'='*50}")
    print(f"SUMMARY")
    print(f"{'='*50}")
    print(f"Uploaded: {total_uploaded} files")
    print(f"Errors: {total_errors}")


if __name__ == "__main__":
    upload_all_insights()
