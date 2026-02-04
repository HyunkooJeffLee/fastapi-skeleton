"""Health check endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from common.db.session import get_db_session

router = APIRouter()


@router.get("/liveness")
async def liveness() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/readiness")
async def readiness(session: AsyncSession = Depends(get_db_session)) -> dict[str, str]:
    await session.execute(text("SELECT 1"))
    return {"status": "ok"}
