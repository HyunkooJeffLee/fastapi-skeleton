"""Alembic environment configuration."""

from __future__ import annotations

import importlib
import logging
import pkgutil
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool

from common.db.base import Base
from common.lib.config import get_settings

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name, defaults={"sys": sys})

logger = logging.getLogger("alembic.env")
settings = get_settings()


def _sync_url(url: str) -> str:
    if "+asyncpg" in url:
        return url.replace("+asyncpg", "")
    if "+aiosqlite" in url:
        return url.replace("+aiosqlite", "")
    return url


def _import_submodules(module_name: str) -> None:
    module = importlib.import_module(module_name)
    if not getattr(module, "__path__", None):
        return
    for module_info in pkgutil.walk_packages(module.__path__, prefix=f"{module.__name__}."):
        if module_info.ispkg:
            continue
        importlib.import_module(module_info.name)


def _load_model_modules() -> None:
    modules = settings.alembic_modules()
    if not modules:
        raise RuntimeError("ALEMBIC_MODEL_MODULES is empty")

    missing: list[str] = []
    for module_path in modules:
        try:
            _import_submodules(module_path)
            logger.info("Loaded model module: %s", module_path)
        except ModuleNotFoundError:
            missing.append(module_path)
        except Exception as exc:
            raise RuntimeError(f"Failed to import {module_path}: {exc}") from exc

    if missing:
        raise RuntimeError(f"Model modules not found: {', '.join(missing)}")

    if not Base.metadata.tables:
        is_autogenerate = bool(getattr(getattr(config, "cmd_opts", None), "autogenerate", False))
        message = "No tables found in metadata. Check ALEMBIC_MODEL_MODULES and model imports."
        if is_autogenerate:
            raise RuntimeError(message)
        logger.warning(message)


_load_model_modules()

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = _sync_url(settings.DB_URL)
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = create_engine(
        _sync_url(settings.DB_URL),
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
