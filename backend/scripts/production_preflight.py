"""Production deployment preflight checks.

This script intentionally validates only prerequisites that must be true before
the web process is released. Heavy ML/FAISS work stays out of the pre-deploy
phase so Railway healthchecks remain fast and deterministic.
"""

from __future__ import annotations

import os
import sys

from sqlalchemy import create_engine, text


def fail(message: str) -> None:
    print(f"[PREFLIGHT][FAIL] {message}", flush=True)
    raise SystemExit(1)


def main() -> None:
    app_env = os.getenv("APP_ENV", "development").strip().lower()
    if app_env != "production":
        fail(f"APP_ENV must be 'production' on Railway; got {app_env!r}")

    database_url = os.getenv("DATABASE_URL", "").strip()
    if not database_url:
        fail("DATABASE_URL is missing.")
    if not ("postgresql" in database_url or "postgres" in database_url):
        fail("DATABASE_URL must point to PostgreSQL/Supabase in production.")

    jwt_secret = os.getenv("JWT_SECRET", "").strip()
    if len(jwt_secret) < 32:
        fail("JWT_SECRET must be at least 32 characters long.")

    groq_key = os.getenv("GROQ_API_KEY", "").strip()
    if not groq_key:
        fail("GROQ_API_KEY is missing.")

    print("[PREFLIGHT] Connecting to production database...", flush=True)
    engine = create_engine(
        database_url,
        connect_args={"sslmode": "require", "connect_timeout": 10},
        pool_pre_ping=True,
    )

    try:
        with engine.begin() as conn:
            conn.execute(text("SELECT 1"))
            # Preserve the application's existing bootstrap behavior for a
            # missing table without performing destructive migrations.
            import models
            from database import Base

            Base.metadata.create_all(bind=conn)
    except Exception as exc:
        fail(f"Production database preflight failed: {type(exc).__name__}: {exc}")
    finally:
        engine.dispose()

    print("[PREFLIGHT] Database connectivity/schema bootstrap: PASS", flush=True)
    print("[PREFLIGHT] Required production variables: PASS", flush=True)
    print("[PREFLIGHT] Deployment preflight complete.", flush=True)


if __name__ == "__main__":
    main()
