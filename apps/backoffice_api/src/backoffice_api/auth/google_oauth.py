"""Google OAuth helpers."""

from __future__ import annotations

from http import HTTPStatus
from urllib.parse import urlencode

import httpx

from common.lib.config import Settings
from common.lib.exceptions import AppError, UnauthorizedError
from backoffice_api.auth.schemas import OAuthTokens

GOOGLE_OAUTH_AUTHORIZE_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_OAUTH_TOKEN_URL = "https://oauth2.googleapis.com/token"


def build_authorize_url(settings: Settings, state: str, scope: str) -> str:
    if not settings.AUTH_GOOGLE_CLIENT_ID or not settings.AUTH_GOOGLE_REDIRECT_URI:
        raise UnauthorizedError("Google OAuth client is not configured")

    params = {
        "client_id": settings.AUTH_GOOGLE_CLIENT_ID,
        "redirect_uri": settings.AUTH_GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": scope,
        "access_type": "offline",
        "prompt": "consent",
        "state": state,
    }
    return f"{GOOGLE_OAUTH_AUTHORIZE_URL}?{urlencode(params)}"


async def exchange_code_for_tokens(
    settings: Settings,
    code: str,
    redirect_uri: str | None = None,
) -> OAuthTokens:
    if not settings.AUTH_GOOGLE_CLIENT_ID or not settings.AUTH_GOOGLE_CLIENT_SECRET:
        raise UnauthorizedError("Google OAuth client is not configured")

    data: dict[str, str] = {
        "client_id": settings.AUTH_GOOGLE_CLIENT_ID,
        "client_secret": settings.AUTH_GOOGLE_CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": redirect_uri or settings.AUTH_GOOGLE_REDIRECT_URI or "",
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(GOOGLE_OAUTH_TOKEN_URL, data=data)
            response.raise_for_status()
            payload = response.json()
    except httpx.HTTPStatusError as exc:
        status = exc.response.status_code
        raise AppError(
            message=f"Google OAuth request failed (status={status})",
            status_code=HTTPStatus.BAD_GATEWAY,
            error_code="GOOGLE_OAUTH_HTTP_ERROR",
        ) from exc
    except httpx.RequestError as exc:
        raise AppError(
            message="Google OAuth request failed (network error)",
            status_code=HTTPStatus.SERVICE_UNAVAILABLE,
            error_code="GOOGLE_OAUTH_REQUEST_ERROR",
        ) from exc

    return OAuthTokens(**payload)


async def refresh_access_token(settings: Settings, refresh_token: str) -> OAuthTokens:
    if not settings.AUTH_GOOGLE_CLIENT_ID or not settings.AUTH_GOOGLE_CLIENT_SECRET:
        raise UnauthorizedError("Google OAuth client is not configured")

    data: dict[str, str] = {
        "client_id": settings.AUTH_GOOGLE_CLIENT_ID,
        "client_secret": settings.AUTH_GOOGLE_CLIENT_SECRET,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(GOOGLE_OAUTH_TOKEN_URL, data=data)
            response.raise_for_status()
            payload = response.json()
    except httpx.HTTPStatusError as exc:
        status = exc.response.status_code
        raise AppError(
            message=f"Google OAuth request failed (status={status})",
            status_code=HTTPStatus.BAD_GATEWAY,
            error_code="GOOGLE_OAUTH_HTTP_ERROR",
        ) from exc
    except httpx.RequestError as exc:
        raise AppError(
            message="Google OAuth request failed (network error)",
            status_code=HTTPStatus.SERVICE_UNAVAILABLE,
            error_code="GOOGLE_OAUTH_REQUEST_ERROR",
        ) from exc

    return OAuthTokens(**payload)
