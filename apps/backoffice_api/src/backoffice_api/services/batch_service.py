"""Batch service template."""

from __future__ import annotations

from dataclasses import dataclass

from backoffice_api.repositories.sample_repository import SampleRepository


@dataclass
class BatchResult:
    processed: int = 0
    skipped: int = 0
    failed: int = 0

    def to_dict(self) -> dict[str, int]:
        return {
            "processed": self.processed,
            "skipped": self.skipped,
            "failed": self.failed,
        }

    def as_message(self) -> str:
        return (
            f"processed={self.processed} skipped={self.skipped} failed={self.failed}"
        )


class BatchService:
    def __init__(self, repository: SampleRepository) -> None:
        self._repository = repository

    async def process(self, limit: int) -> BatchResult:
        items = await self._repository.list_items(limit)
        result = BatchResult()

        for item in items:
            if not item.name:
                result.skipped += 1
                continue
            result.processed += 1

        return result
