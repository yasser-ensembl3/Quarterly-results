from __future__ import annotations
"""Synchronization of files with Google Drive."""

import io
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

from googleapiclient.discovery import Resource
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload

from ..config import get_settings
from ..database.models import FileType
from .auth import get_drive_service


@dataclass
class DriveFile:
    """Représente un fichier Google Drive."""
    id: str
    name: str
    mime_type: str
    modified_time: Optional[datetime] = None
    size: Optional[int] = None
    parents: list[str] = field(default_factory=list)

    @property
    def file_type(self) -> FileType:
        """Détermine le type de fichier basé sur le mime type."""
        if "markdown" in self.mime_type or self.name.endswith(".md"):
            return FileType.MARKDOWN
        elif "pdf" in self.mime_type:
            return FileType.PDF
        elif "image" in self.mime_type:
            return FileType.IMAGE
        else:
            return FileType.OTHER


@dataclass
class DriveFolder:
    """Représente un dossier Google Drive."""
    id: str
    name: str
    files: list[DriveFile] = field(default_factory=list)
    subfolders: list["DriveFolder"] = field(default_factory=list)


@dataclass
class SyncResult:
    """Résultat d'une opération de synchronisation."""
    downloaded: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    total_files: int = 0


class DriveSync:
    """Gère la synchronisation des fichiers depuis Google Drive."""

    FOLDER_MIME_TYPE = "application/vnd.google-apps.folder"
    SUPPORTED_MIME_TYPES = [
        "text/markdown",
        "text/plain",
        "application/pdf",
        "image/png",
        "image/jpeg",
        "image/gif",
        "image/webp",
    ]

    def __init__(self, service: Optional[Resource] = None):
        self.service = service or get_drive_service()
        self.settings = get_settings()

    def list_folder_contents(self, folder_id: str) -> list[DriveFile | DriveFolder]:
        """Liste le contenu d'un dossier Google Drive."""
        results = []
        page_token = None

        while True:
            response = self.service.files().list(
                q=f"'{folder_id}' in parents and trashed = false",
                spaces="drive",
                fields="nextPageToken, files(id, name, mimeType, modifiedTime, size, parents)",
                pageToken=page_token,
            ).execute()

            for item in response.get("files", []):
                modified_time = None
                if item.get("modifiedTime"):
                    modified_time = datetime.fromisoformat(
                        item["modifiedTime"].replace("Z", "+00:00")
                    )

                if item["mimeType"] == self.FOLDER_MIME_TYPE:
                    results.append(DriveFolder(
                        id=item["id"],
                        name=item["name"],
                    ))
                else:
                    results.append(DriveFile(
                        id=item["id"],
                        name=item["name"],
                        mime_type=item["mimeType"],
                        modified_time=modified_time,
                        size=int(item.get("size", 0)),
                        parents=item.get("parents", []),
                    ))

            page_token = response.get("nextPageToken")
            if not page_token:
                break

        return results

    def download_file(self, file: DriveFile, destination_dir: Path) -> Path:
        """
        Télécharge un fichier depuis Google Drive.

        Args:
            file: Le fichier à télécharger
            destination_dir: Dossier de destination

        Returns:
            Le chemin du fichier téléchargé
        """
        destination_dir.mkdir(parents=True, exist_ok=True)
        destination = destination_dir / file.name

        request = self.service.files().get_media(fileId=file.id)
        file_handle = io.BytesIO()
        downloader = MediaIoBaseDownload(file_handle, request)

        done = False
        while not done:
            _, done = downloader.next_chunk()

        with open(destination, "wb") as f:
            f.write(file_handle.getvalue())

        return destination

    def sync_root_folder(self, root_folder_id: str) -> dict[str, dict[str, SyncResult]]:
        """
        Synchronise le dossier racine (structure: trimestre -> société -> fichiers).

        Args:
            root_folder_id: ID du dossier racine Google Drive

        Returns:
            Dict avec résultats par trimestre et société
        """
        results = {}
        raw_path = self.settings.raw_data_path

        # Lister les dossiers de trimestres
        quarter_items = self.list_folder_contents(root_folder_id)
        quarter_folders = [item for item in quarter_items if isinstance(item, DriveFolder)]

        for quarter_folder in quarter_folders:
            quarter_name = self._normalize_quarter_name(quarter_folder.name)
            results[quarter_name] = {}

            # Lister les dossiers de sociétés dans ce trimestre
            company_items = self.list_folder_contents(quarter_folder.id)
            company_folders = [item for item in company_items if isinstance(item, DriveFolder)]

            for company_folder in company_folders:
                company_name = company_folder.name
                sync_result = self.sync_company_folder(
                    company_folder.id,
                    raw_path / quarter_name / company_name,
                )
                results[quarter_name][company_name] = sync_result

        return results

    def sync_company_folder(self, folder_id: str, destination_dir: Path) -> SyncResult:
        """
        Synchronise un dossier de société.

        Args:
            folder_id: ID du dossier Google Drive
            destination_dir: Dossier local de destination

        Returns:
            Résultat de la synchronisation
        """
        result = SyncResult()
        items = self.list_folder_contents(folder_id)
        files = [item for item in items if isinstance(item, DriveFile)]

        result.total_files = len(files)

        for file in files:
            if not self._is_supported_file(file):
                result.skipped.append(f"{file.name} (type non supporté: {file.mime_type})")
                continue

            try:
                local_path = destination_dir / file.name

                # Vérifier si le fichier existe et est à jour
                if self._needs_download(file, local_path):
                    self.download_file(file, destination_dir)
                    result.downloaded.append(file.name)
                else:
                    result.skipped.append(f"{file.name} (déjà à jour)")
            except Exception as e:
                result.errors.append(f"{file.name}: {str(e)}")

        return result

    def _is_supported_file(self, file: DriveFile) -> bool:
        """Vérifie si le fichier est d'un type supporté."""
        if file.mime_type in self.SUPPORTED_MIME_TYPES:
            return True
        # Vérifier aussi par extension
        ext = Path(file.name).suffix.lower()
        return ext in [".md", ".pdf", ".png", ".jpg", ".jpeg", ".gif", ".webp"]

    def _needs_download(self, file: DriveFile, local_path: Path) -> bool:
        """Vérifie si le fichier doit être téléchargé."""
        if not local_path.exists():
            return True

        if file.modified_time:
            local_mtime = datetime.fromtimestamp(
                local_path.stat().st_mtime
            ).replace(tzinfo=file.modified_time.tzinfo)
            return file.modified_time > local_mtime

        return True

    def _normalize_quarter_name(self, name: str) -> str:
        """Normalize quarter name (e.g., 'Q3 2024' -> 'Q3_2024')."""
        match = re.search(r"Q(\d)\s*[-_]?\s*(\d{4})", name, re.IGNORECASE)
        if match:
            return f"Q{match.group(1)}_{match.group(2)}"
        return name.replace(" ", "_").replace("-", "_")

    def find_folder_by_name(self, parent_id: str, folder_name: str) -> Optional[str]:
        """
        Find a folder by name within a parent folder.

        Args:
            parent_id: Parent folder ID
            folder_name: Name of folder to find

        Returns:
            Folder ID if found, None otherwise
        """
        items = self.list_folder_contents(parent_id)
        for item in items:
            if isinstance(item, DriveFolder) and item.name.lower() == folder_name.lower():
                return item.id
        return None

    def upload_file(self, local_path: Path, parent_folder_id: str) -> str:
        """
        Upload a file to Google Drive.

        Args:
            local_path: Path to local file
            parent_folder_id: ID of parent folder in Drive

        Returns:
            ID of uploaded file
        """
        # Determine mime type
        suffix = local_path.suffix.lower()
        mime_types = {
            '.json': 'application/json',
            '.md': 'text/markdown',
            '.pdf': 'application/pdf',
            '.txt': 'text/plain',
        }
        mime_type = mime_types.get(suffix, 'application/octet-stream')

        # Check if file already exists
        existing_id = self._find_file_in_folder(parent_folder_id, local_path.name)

        file_metadata = {
            'name': local_path.name,
            'parents': [parent_folder_id]
        }

        media = MediaFileUpload(str(local_path), mimetype=mime_type)

        if existing_id:
            # Update existing file
            file = self.service.files().update(
                fileId=existing_id,
                media_body=media
            ).execute()
        else:
            # Create new file
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()

        return file.get('id')

    def _find_file_in_folder(self, folder_id: str, filename: str) -> Optional[str]:
        """Find a file by name in a folder."""
        items = self.list_folder_contents(folder_id)
        for item in items:
            if isinstance(item, DriveFile) and item.name == filename:
                return item.id
        return None

    def upload_results_to_company_folder(self, root_folder_id: str, quarter_name: str,
                                          company_name: str, files: list[Path]) -> dict:
        """
        Upload result files to a company's folder in Drive.

        Args:
            root_folder_id: Root folder ID (quarterly results root)
            quarter_name: Quarter name (e.g., 'Q3')
            company_name: Company name (e.g., 'Amazon', 'Coinbase')
            files: List of file paths to upload

        Returns:
            Dict with upload results
        """
        results = {'uploaded': [], 'errors': []}

        # Find quarter folder
        quarter_folder_id = self.find_folder_by_name(root_folder_id, quarter_name)
        if not quarter_folder_id:
            results['errors'].append(f"Quarter folder '{quarter_name}' not found")
            return results

        # Find company folder
        company_folder_id = self.find_folder_by_name(quarter_folder_id, company_name)
        if not company_folder_id:
            results['errors'].append(f"Company folder '{company_name}' not found in {quarter_name}")
            return results

        # Upload each file
        for file_path in files:
            try:
                file_id = self.upload_file(file_path, company_folder_id)
                results['uploaded'].append({
                    'file': file_path.name,
                    'drive_id': file_id
                })
            except Exception as e:
                results['errors'].append(f"{file_path.name}: {str(e)}")

        return results

    def parse_quarter_from_folder(self, folder_name: str) -> Optional[tuple[int, int]]:
        """
        Parse le trimestre et l'année depuis le nom de dossier.

        Returns:
            Tuple (year, quarter) ou None si non parseable
        """
        match = re.search(r"Q(\d)\s*[-_]?\s*(\d{4})", folder_name, re.IGNORECASE)
        if match:
            return int(match.group(2)), int(match.group(1))
        return None


def sync_from_drive(root_folder_id: Optional[str] = None) -> dict:
    """
    Fonction utilitaire pour synchroniser depuis Google Drive.

    Args:
        root_folder_id: ID du dossier racine (utilise .env par défaut)

    Returns:
        Résultats de synchronisation
    """
    settings = get_settings()
    folder_id = root_folder_id or settings.gdrive_root_folder_id

    if not folder_id:
        raise ValueError(
            "ID du dossier Google Drive non configuré. "
            "Définissez GDRIVE_ROOT_FOLDER_ID dans .env"
        )

    sync = DriveSync()
    return sync.sync_root_folder(folder_id)
