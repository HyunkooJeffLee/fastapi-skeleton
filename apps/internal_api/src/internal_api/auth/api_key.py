"""API Key authentication for internal API."""

from __future__ import annotations

import secrets

from fastapi import Depends, Request

from common.lib.config import Settings, get_settings
from common.lib.exceptions import UnauthorizedError


def _extract_api_key(settings: Settings, request: Request) -> str:
    header_name = settings.AUTH_API_KEY_HEADER
    api_key = request.headers.get(header_name)
    if not api_key:
        raise UnauthorizedError(f"Missing API key header: {header_name}")
    if not settings.AUTH_API_KEY:
        raise UnauthorizedError("API key not configured")
    if not secrets.compare_digest(api_key, settings.AUTH_API_KEY):
        raise UnauthorizedError("Invalid API key")
    return api_key


async def require_api_key(
    request: Request,
    settings: Settings = Depends(get_settings),
) -> str:
    return _extract_api_key(settings, request)
