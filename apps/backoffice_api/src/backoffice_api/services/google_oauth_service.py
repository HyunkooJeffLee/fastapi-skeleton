"""Google OAuth service layer."""

from __future__ import annotations

from common.lib.config import Settings
from backoffice_api.auth.google_oauth import (
    build_authorize_url,
    exchange_code_for_tokens,
    refresh_access_token,
)
from backoffice_api.auth.schemas import OAuthExchangeRequest, OAuthRefreshRequest, OAuthTokens
from backoffice_api.auth.token_store import OAuthTokenStore
from backoffice_api.db.models.oauth_token import OAuthToken
from backoffice_api.repositories.oauth_token_repository import OAuthTokenRepository


class GoogleOAuthService:
    def __init__(self, repository: OAuthTokenRepository, settings: Settings) -> None:
        self._repository = repository
        self._settings = settings
        self._store = OAuthTokenStore(repository, settings)

    def authorize_url(self, state: str, scope: str) -> str:
        return build_authorize_url(self._settings, state=state, scope=scope)

    async def exchange_tokens(self, request: OAuthExchangeRequest) -> OAuthTokens:
        return await exchange_code_for_tokens(
            settings=self._settings,
            code=request.code,
            redirect_uri=request.redirect_uri,
        )

    async def refresh_tokens(self, request: OAuthRefreshRequest, provider: str = "google") -> OAuthTokens:
        refresh_token = await self._store.get_refresh_token(provider, request.subject)
        tokens = await refresh_access_token(self._settings, refresh_token)
        if tokens.refresh_token is None:
            tokens.refresh_token = refresh_token
        return tokens

    async def exchange_store_record(
        self,
        request: OAuthExchangeRequest,
        provider: str = "google",
    ) -> OAuthToken:
        tokens = await self.exchange_tokens(request)
        return await self._store.upsert_tokens(
            provider=provider,
            subject=request.subject,
            tokens=tokens,
        )

    async def refresh_store_record(
        self,
        request: OAuthRefreshRequest,
        provider: str = "google",
    ) -> OAuthToken:
        tokens = await self.refresh_tokens(request, provider=provider)
        return await self._store.upsert_tokens(
            provider=provider,
            subject=request.subject,
            tokens=tokens,
        )
