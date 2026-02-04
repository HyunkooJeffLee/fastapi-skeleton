"""Token encryption and persistence helpers."""

from __future__ import annotations

import base64
from datetime import datetime, timedelta, timezone

from cryptography.fernet import Fernet
from common.lib.config import Settings
from common.lib.exceptions import NotFoundError, UnauthorizedError
from backoffice_api.auth.schemas import OAuthTokens
from backoffice_api.db.models.oauth_token import OAuthToken
from backoffice_api.repositories.oauth_token_repository import OAuthTokenRepository


def _build_fernet_key(raw_key: str) -> bytes:
    key_bytes = raw_key.encode("utf-8")
    try:
        decoded = base64.urlsafe_b64decode(key_bytes)
        if len(decoded) == 32:
            return key_bytes
    except Exception:
        pass
    if len(key_bytes) == 32:
        return base64.urlsafe_b64encode(key_bytes)
    raise ValueError("AUTH_TOKEN_ENC_KEY must be 32 bytes or base64-encoded 32 bytes")


class OAuthTokenStore:
    def __init__(self, repository: OAuthTokenRepository, settings: Settings) -> None:
        if not settings.AUTH_TOKEN_ENC_KEY:
            raise UnauthorizedError("AUTH_TOKEN_ENC_KEY is not configured")
        self._repository = repository
        try:
            self._cipher = Fernet(_build_fernet_key(settings.AUTH_TOKEN_ENC_KEY))
        except ValueError as exc:
            raise UnauthorizedError(str(exc)) from exc

    def encrypt(self, value: str) -> str:
        return self._cipher.encrypt(value.encode("utf-8")).decode("utf-8")

    def decrypt(self, value: str) -> str:
        return self._cipher.decrypt(value.encode("utf-8")).decode("utf-8")

    async def get_refresh_token(self, provider: str, subject: str) -> str:
        record = await self._repository.get_by_provider_subject(provider, subject)
        if not record or not record.refresh_token_enc:
            raise NotFoundError("Refresh token not found")
        return self.decrypt(record.refresh_token_enc)

    async def upsert_tokens(
        self,
        provider: str,
        subject: str,
        tokens: OAuthTokens,
    ) -> OAuthToken:
        existing = await self._repository.get_by_provider_subject(provider, subject)
        if tokens.refresh_token is None and existing:
            refresh_token_enc = existing.refresh_token_enc
        else:
            refresh_token_enc = self.encrypt(tokens.refresh_token) if tokens.refresh_token else None

        access_token_enc = self.encrypt(tokens.access_token)
        expires_at = (
            datetime.now(timezone.utc) + timedelta(seconds=tokens.expires_in)
            if tokens.expires_in
            else None
        )
        return await self._repository.upsert(
            provider=provider,
            subject=subject,
            access_token_enc=access_token_enc,
            refresh_token_enc=refresh_token_enc,
            expires_at=expires_at,
        )
