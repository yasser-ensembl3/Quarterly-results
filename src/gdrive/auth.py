from __future__ import annotations
"""Authentification Google Drive OAuth2."""

from pathlib import Path
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build, Resource

from ..config import get_settings


class DriveAuthenticator:
    """Gère l'authentification OAuth2 pour Google Drive."""

    def __init__(
        self,
        credentials_path: Optional[Path] = None,
        token_path: Optional[Path] = None,
        scopes: Optional[list[str]] = None,
    ):
        settings = get_settings()
        self.credentials_path = credentials_path or settings.gdrive_credentials_path
        self.token_path = token_path or settings.gdrive_token_path
        self.scopes = scopes or settings.gdrive_scopes
        self._credentials: Optional[Credentials] = None

    def authenticate(self) -> Credentials:
        """
        Authentifie l'utilisateur et retourne les credentials.

        - Charge le token existant si disponible
        - Rafraîchit le token si expiré
        - Lance le flow OAuth2 si nécessaire
        """
        # Essayer de charger un token existant
        if self.token_path.exists():
            self._credentials = Credentials.from_authorized_user_file(
                str(self.token_path), self.scopes
            )

        # Si pas de credentials valides, authentifier
        if not self._credentials or not self._credentials.valid:
            if self._credentials and self._credentials.expired and self._credentials.refresh_token:
                # Rafraîchir le token
                self._credentials.refresh(Request())
            else:
                # Lancer le flow OAuth2
                if not self.credentials_path.exists():
                    raise FileNotFoundError(
                        f"Fichier credentials.json non trouvé: {self.credentials_path}\n"
                        "Téléchargez-le depuis Google Cloud Console."
                    )
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(self.credentials_path), self.scopes
                )
                # Port fixe 8080 pour compatibilité avec Web Application credentials
                self._credentials = flow.run_local_server(
                    port=8080,
                    prompt="consent",
                    success_message="Authentification réussie! Vous pouvez fermer cette fenêtre.",
                )

            # Sauvegarder le token pour les prochaines fois
            self._save_token()

        return self._credentials

    def _save_token(self) -> None:
        """Sauvegarde le token pour réutilisation."""
        if self._credentials:
            self.token_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.token_path, "w") as token_file:
                token_file.write(self._credentials.to_json())

    def get_service(self) -> Resource:
        """Retourne un service Google Drive API authentifié."""
        credentials = self.authenticate()
        return build("drive", "v3", credentials=credentials)

    @property
    def is_authenticated(self) -> bool:
        """Vérifie si l'utilisateur est authentifié."""
        return self._credentials is not None and self._credentials.valid


def get_drive_service() -> Resource:
    """Shortcut pour obtenir un service Drive authentifié."""
    auth = DriveAuthenticator()
    return auth.get_service()
