"""OAuth token data access."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import Insert, insert as pg_insert
from sqlalchemy.sql import func
from sqlalchemy.ext.asyncio import AsyncSession

from backoffice_api.db.models.oauth_token import OAuthToken


class OAuthTokenRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_provider_subject(self, provider: str, subject: str) -> OAuthToken | None:
        result = await self._session.execute(
            select(OAuthToken).where(
                OAuthToken.provider == provider,
                OAuthToken.subject == subject,
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    def build_pg_upsert_stmt(
        provider: str,
        subject: str,
        access_token_enc: str,
        refresh_token_enc: str | None,
        expires_at: datetime | None,
    ) -> Insert:
        return (
            pg_insert(OAuthToken)
            .values(
                provider=provider,
                subject=subject,
                access_token_enc=access_token_enc,
                refresh_token_enc=refresh_token_enc,
                expires_at=expires_at,
            )
            .on_conflict_do_update(
                index_elements=[OAuthToken.provider, OAuthToken.subject],
                set_={
                    "access_token_enc": access_token_enc,
                    "refresh_token_enc": refresh_token_enc,
                    "expires_at": expires_at,
                    "updated_at": func.now(),
                },
            )
            .returning(OAuthToken.id)
        )

    def _is_postgres(self) -> bool:
        bind = self._session.get_bind()
        if bind is None:
            return False
        return bind.dialect.name == "postgresql"

    async def upsert(
        self,
        provider: str,
        subject: str,
        access_token_enc: str,
        refresh_token_enc: str | None,
        expires_at: datetime | None,
    ) -> OAuthToken:
        if self._is_postgres():
            stmt = self.build_pg_upsert_stmt(
                provider=provider,
                subject=subject,
                access_token_enc=access_token_enc,
                refresh_token_enc=refresh_token_enc,
                expires_at=expires_at,
            )
            result = await self._session.execute(stmt)
            await self._session.commit()
            record_id = result.scalar_one()
            record = await self._session.get(OAuthToken, record_id)
            if record is None:
                raise RuntimeError("Failed to load OAuthToken after upsert")
            return record

        record = await self.get_by_provider_subject(provider, subject)
        if record is None:
            record = OAuthToken(
                provider=provider,
                subject=subject,
                access_token_enc=access_token_enc,
                refresh_token_enc=refresh_token_enc,
                expires_at=expires_at,
            )
            self._session.add(record)
        else:
            record.access_token_enc = access_token_enc
            record.refresh_token_enc = refresh_token_enc
            record.expires_at = expires_at

        await self._session.commit()
        await self._session.refresh(record)
        return record
