from __future__ import annotations
"""Authentification Google Drive OAuth2 et Service Account."""

import base64
import json
import os
from pathlib import Path
from typing import Optional, Union

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build, Resource

from ..config import get_settings


class DriveAuthenticator:
    """Gère l'authentification OAuth2 ou Service Account pour Google Drive."""

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
        self._credentials: Optional[Union[Credentials, service_account.Credentials]] = None

    def authenticate(self) -> Union[Credentials, service_account.Credentials]:
        """
        Authentifie l'utilisateur et retourne les credentials.

        Ordre de priorité:
        1. GOOGLE_SERVICE_ACCOUNT_JSON (env var - JSON complet)
        2. GOOGLE_SERVICE_ACCOUNT_BASE64 (env var - JSON encodé en base64)
        3. Token existant (token.json)
        4. OAuth2 flow (credentials.json)
        """
        # Option 1: Service Account JSON direct depuis env var
        sa_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
        if sa_json:
            sa_info = json.loads(sa_json)
            self._credentials = service_account.Credentials.from_service_account_info(
                sa_info, scopes=self.scopes
            )
            return self._credentials

        # Option 2: Service Account JSON encodé en base64
        sa_base64 = os.getenv("GOOGLE_SERVICE_ACCOUNT_BASE64")
        if sa_base64:
            sa_json = base64.b64decode(sa_base64).decode("utf-8")
            sa_info = json.loads(sa_json)
            self._credentials = service_account.Credentials.from_service_account_info(
                sa_info, scopes=self.scopes
            )
            return self._credentials

        # Option 3: Essayer de charger un token existant
        if self.token_path.exists():
            self._credentials = Credentials.from_authorized_user_file(
                str(self.token_path), self.scopes
            )

        # Si pas de credentials valides, authentifier via OAuth2
        if not self._credentials or not self._credentials.valid:
            if self._credentials and self._credentials.expired and self._credentials.refresh_token:
                # Rafraîchir le token
                self._credentials.refresh(Request())
            else:
                # Lancer le flow OAuth2
                if not self.credentials_path.exists():
                    raise FileNotFoundError(
                        f"Aucune méthode d'authentification trouvée.\n"
                        f"Options:\n"
                        f"  1. Définir GOOGLE_SERVICE_ACCOUNT_JSON ou GOOGLE_SERVICE_ACCOUNT_BASE64\n"
                        f"  2. Placer credentials.json dans: {self.credentials_path}"
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
