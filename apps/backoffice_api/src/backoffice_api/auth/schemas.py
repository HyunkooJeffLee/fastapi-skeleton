"""OAuth-related schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class OAuthTokens(BaseModel):
    access_token: str
    refresh_token: str | None = None
    expires_in: int | None = None
    token_type: str | None = None
    scope: str | None = None


class OAuthExchangeRequest(BaseModel):
    code: str
    subject: str
    redirect_uri: str | None = None


class OAuthRefreshRequest(BaseModel):
    subject: str


class OAuthAuthorizeResponse(BaseModel):
    authorize_url: str


class OAuthTokenRecord(BaseModel):
    id: int
    provider: str
    subject: str
    expires_at: datetime | None = None
