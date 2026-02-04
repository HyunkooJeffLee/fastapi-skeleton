"""Google OAuth endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from common.db.session import get_db_session
from common.lib.config import Settings, get_settings
from backoffice_api.auth.schemas import (
    OAuthAuthorizeResponse,
    OAuthExchangeRequest,
    OAuthRefreshRequest,
    OAuthTokenRecord,
)
from backoffice_api.repositories.oauth_token_repository import OAuthTokenRepository
from backoffice_api.services.google_oauth_service import GoogleOAuthService

router = APIRouter()


def get_google_oauth_service(
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> GoogleOAuthService:
    repository = OAuthTokenRepository(session)
    return GoogleOAuthService(repository, settings)


@router.get("/authorize", response_model=OAuthAuthorizeResponse)
async def authorize_url(
    state: str,
    scope: str = "openid email profile",
    service: GoogleOAuthService = Depends(get_google_oauth_service),
) -> OAuthAuthorizeResponse:
    url = service.authorize_url(state=state, scope=scope)
    return OAuthAuthorizeResponse(authorize_url=url)


@router.post("/exchange", response_model=OAuthTokenRecord)
async def exchange_tokens(
    payload: OAuthExchangeRequest,
    service: GoogleOAuthService = Depends(get_google_oauth_service),
) -> OAuthTokenRecord:
    record = await service.exchange_store_record(payload)
    return OAuthTokenRecord(
        id=record.id,
        provider=record.provider,
        subject=record.subject,
        expires_at=record.expires_at,
    )


@router.post("/refresh", response_model=OAuthTokenRecord)
async def refresh_tokens(
    payload: OAuthRefreshRequest,
    service: GoogleOAuthService = Depends(get_google_oauth_service),
) -> OAuthTokenRecord:
    record = await service.refresh_store_record(payload)
    return OAuthTokenRecord(
        id=record.id,
        provider=record.provider,
        subject=record.subject,
        expires_at=record.expires_at,
    )
