"""Sample repository used by batch jobs."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from common.db.models.sample import SampleItem


class SampleRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_items(self, limit: int) -> list[SampleItem]:
        result = await self._session.execute(select(SampleItem).limit(limit))
        return list(result.scalars().all())
