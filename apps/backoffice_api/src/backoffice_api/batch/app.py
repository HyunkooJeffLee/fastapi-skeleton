"""Typer batch commands for backoffice API."""

from __future__ import annotations

import asyncio
import json

import typer

from common.db.session import get_sessionmaker
from backoffice_api.repositories.sample_repository import SampleRepository
from backoffice_api.services.batch_service import BatchResult, BatchService

app = typer.Typer(help="backoffice-api batch commands")


async def _execute_batch(limit: int, dry_run: bool) -> BatchResult:
    session_factory = get_sessionmaker()

    async with session_factory() as session:
        repository = SampleRepository(session)
        service = BatchService(repository)
        transaction = await session.begin()
        try:
            result = await service.process(limit)

            if dry_run:
                await transaction.rollback()
            else:
                await transaction.commit()
        except Exception:
            await transaction.rollback()
            raise

    return result


@app.command("template")
def template(
    limit: int = typer.Option(100, min=1, help="Maximum items to process"),
    dry_run: bool = typer.Option(False, help="Do not commit changes"),
    json_output: bool = typer.Option(False, "--json", help="Output JSON"),
) -> None:
    """Batch job template with input/output and transaction pattern."""
    result = asyncio.run(_execute_batch(limit=limit, dry_run=dry_run))
    if json_output:
        typer.echo(json.dumps(result.to_dict()))
    else:
        typer.echo(result.as_message())
