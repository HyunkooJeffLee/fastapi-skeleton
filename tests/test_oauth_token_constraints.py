from sqlalchemy import UniqueConstraint
from sqlalchemy.dialects import postgresql

from backoffice_api.db.models.oauth_token import OAuthToken
from backoffice_api.repositories.oauth_token_repository import OAuthTokenRepository


def test_oauth_token_unique_constraint() -> None:
    constraints = [
        c for c in OAuthToken.__table__.constraints if isinstance(c, UniqueConstraint)
    ]
    assert any(
        {col.name for col in constraint.columns} == {"provider", "subject"}
        for constraint in constraints
    )


def test_pg_upsert_statement_contains_on_conflict() -> None:
    stmt = OAuthTokenRepository.build_pg_upsert_stmt(
        provider="google",
        subject="user-1",
        access_token_enc="access",
        refresh_token_enc="refresh",
        expires_at=None,
    )
    compiled = str(
        stmt.compile(
            dialect=postgresql.dialect(),
            compile_kwargs={"literal_binds": True},
        )
    )
    assert "ON CONFLICT (provider, subject) DO UPDATE" in compiled
