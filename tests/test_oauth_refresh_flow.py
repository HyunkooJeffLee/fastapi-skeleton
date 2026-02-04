from __future__ import annotations

import base64

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from backoffice_api.auth.schemas import OAuthRefreshRequest, OAuthTokens
from backoffice_api.auth.token_store import OAuthTokenStore
from backoffice_api.repositories.oauth_token_repository import OAuthTokenRepository
from backoffice_api.services.google_oauth_service import GoogleOAuthService
from common.db.base import Base
from common.lib.config import Settings


def _fernet_key() -> str:
    return base64.urlsafe_b64encode(b"0" * 32).decode("utf-8")


async def test_refresh_flow_keeps_refresh_token(tmp_path, monkeypatch) -> None:
    db_path = tmp_path / "refresh_test.db"
    db_url = f"sqlite+aiosqlite:///{db_path}"
    settings = Settings(DB_URL=db_url, AUTH_TOKEN_ENC_KEY=_fernet_key())

    engine = create_async_engine(db_url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with session_factory() as session:
        repository = OAuthTokenRepository(session)
        store = OAuthTokenStore(repository, settings)

        await store.upsert_tokens(
            provider="google",
            subject="user-1",
            tokens=OAuthTokens(access_token="access-1", refresh_token="refresh-1"),
        )

        async def fake_refresh_access_token(_: Settings, refresh_token: str) -> OAuthTokens:
            assert refresh_token == "refresh-1"
            return OAuthTokens(access_token="access-2", refresh_token=None, expires_in=3600)

        monkeypatch.setattr(
            "backoffice_api.services.google_oauth_service.refresh_access_token",
            fake_refresh_access_token,
        )

        service = GoogleOAuthService(repository, settings)
        record = await service.refresh_store_record(OAuthRefreshRequest(subject="user-1"))

        refreshed = await repository.get_by_provider_subject("google", "user-1")
        assert refreshed is not None
        assert refreshed.id == record.id
        assert store.decrypt(refreshed.access_token_enc) == "access-2"
        assert await store.get_refresh_token("google", "user-1") == "refresh-1"

    await engine.dispose()


async def test_refresh_flow_updates_existing_row(tmp_path, monkeypatch) -> None:
    db_path = tmp_path / "refresh_update_test.db"
    db_url = f"sqlite+aiosqlite:///{db_path}"
    settings = Settings(DB_URL=db_url, AUTH_TOKEN_ENC_KEY=_fernet_key())

    engine = create_async_engine(db_url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with session_factory() as session:
        repository = OAuthTokenRepository(session)
        store = OAuthTokenStore(repository, settings)

        await store.upsert_tokens(
            provider="google",
            subject="user-2",
            tokens=OAuthTokens(access_token="access-1", refresh_token="refresh-1"),
        )

        async def fake_refresh_access_token(_: Settings, refresh_token: str) -> OAuthTokens:
            assert refresh_token == "refresh-1"
            return OAuthTokens(access_token="access-3", refresh_token=None, expires_in=1800)

        monkeypatch.setattr(
            "backoffice_api.services.google_oauth_service.refresh_access_token",
            fake_refresh_access_token,
        )

        service = GoogleOAuthService(repository, settings)
        record = await service.refresh_store_record(OAuthRefreshRequest(subject="user-2"))

        refreshed = await repository.get_by_provider_subject("google", "user-2")
        assert refreshed is not None
        assert refreshed.id == record.id
        assert store.decrypt(refreshed.access_token_enc) == "access-3"
        assert await store.get_refresh_token("google", "user-2") == "refresh-1"

    await engine.dispose()
