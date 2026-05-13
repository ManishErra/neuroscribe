"""
Apply backend/sql/create_reports_table.sql to Postgres (e.g. Supabase) and verify.

Usage (from repo root or backend/):
  python scripts/apply_reports_migration.py apply-verify
  python scripts/apply_reports_migration.py apply
  python scripts/apply_reports_migration.py verify

Requires DATABASE_URL in environment or backend/.env (same as the FastAPI app).
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))
os.chdir(BACKEND)

from dotenv import load_dotenv  # noqa: E402

load_dotenv(BACKEND / ".env")
load_dotenv(BACKEND.parent / ".env")

from sqlalchemy import create_engine, text  # noqa: E402


def _sql_statements(sql_path: Path) -> list[str]:
    raw = sql_path.read_text(encoding="utf-8")
    lines: list[str] = []
    for line in raw.splitlines():
        if line.strip().startswith("--"):
            continue
        lines.append(line)
    body = "\n".join(lines)
    out: list[str] = []
    for chunk in body.split(";"):
        s = chunk.strip()
        if s:
            out.append(s + ";")
    return out


def get_engine():
    url = os.getenv("DATABASE_URL")
    if not url or not str(url).strip():
        print(
            "ERROR: DATABASE_URL is not set. Add it to backend/.env or your shell.",
            file=sys.stderr,
        )
        print(
            "Supabase: Project Settings → Database → Connection string (URI), "
            "use the direct (not pooled) URL for DDL if you hit pooler limits.",
            file=sys.stderr,
        )
        sys.exit(2)
    try:
        return create_engine(
            str(url).strip(),
            connect_args={"sslmode": "require"},
        )
    except ModuleNotFoundError as exc:
        if "psycopg2" in str(exc).lower():
            print(
                "ERROR: PostgreSQL driver not installed for this Python environment.",
                file=sys.stderr,
            )
            print(
                "  pip install psycopg2-binary",
                file=sys.stderr,
            )
            print(
                "Or run the SQL in Supabase → SQL Editor (see backend/sql/).",
                file=sys.stderr,
            )
        raise


def apply_migration(engine, sql_path: Path) -> None:
    bad, missing, _present = _reports_schema_mismatch(engine)
    if bad:
        print(
            "ERROR: public.reports exists but does not match the Day-12 migration.",
            file=sys.stderr,
        )
        print(f"  Missing columns: {sorted(missing)}", file=sys.stderr)
        print(
            "  CREATE TABLE IF NOT EXISTS does not change an existing table. "
            "Fix the table (e.g. backup/rename then re-run apply, or hand-write ALTERs), "
            "then run verify.",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"Applying migration from:\n  {sql_path}\n")

    stmts = _sql_statements(sql_path)
    if not stmts:
        raise RuntimeError(f"No SQL statements found in {sql_path}")

    for i, stmt in enumerate(stmts):
        is_extension = stmt.upper().lstrip().startswith("CREATE EXTENSION")
        print(f"Executing {i + 1}/{len(stmts)}...")
        if is_extension:
            with engine.connect() as conn:
                conn = conn.execution_options(isolation_level="AUTOCOMMIT")
                conn.execute(text(stmt))
        else:
            with engine.begin() as conn:
                conn.execute(text(stmt))
    print("Migration finished successfully.")


def _expected_report_columns() -> set[str]:
    return {
        "id",
        "patient_id",
        "file_path",
        "original_filename",
        "mime_type",
        "title",
        "report_date",
        "ocr_text",
        "ocr_status",
        "ocr_error",
        "created_at",
    }


def _reports_schema_mismatch(engine) -> tuple[bool, set[str], set[str]]:
    """Return (mismatch, missing_cols, present_cols) if reports exists but wrong shape."""
    expected = _expected_report_columns()
    with engine.connect() as conn:
        reg = conn.execute(
            text("SELECT to_regclass('public.reports') AS reg")
        ).scalar()
        if reg is None:
            return False, set(), set()
        rows = conn.execute(
            text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_schema = 'public' AND table_name = 'reports'"
            )
        ).fetchall()
        present = {r[0] for r in rows}
        missing = expected - present
        if missing:
            return True, missing, present
        return False, set(), present


def verify(engine) -> bool:
    required = _expected_report_columns()
    ok = True
    with engine.connect() as conn:
        reg = conn.execute(
            text("SELECT to_regclass('public.reports') AS reg")
        ).scalar()
        print("\n[table_exists]")
        print(f"  to_regclass('public.reports') = {reg!r}")
        if reg is None:
            ok = False
            print("  FAIL: public.reports not found.")

        rows = conn.execute(
            text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_schema = 'public' AND table_name = 'reports'"
            )
        ).fetchall()
        present = {r[0] for r in rows}
        print("\n[columns]")
        missing = sorted(required - present)
        extra = sorted(present - required)
        if missing:
            ok = False
            print(f"  FAIL: missing columns: {missing}")
        if extra:
            print(f"  (extra columns not in Day-12 spec: {extra})")
        if not missing:
            print(f"  All {len(required)} expected columns present.")

        rows = conn.execute(
            text(
                "SELECT indexname FROM pg_indexes "
                "WHERE schemaname = 'public' AND tablename = 'reports' ORDER BY 1"
            )
        ).fetchall()
        print("\n[indexes]")
        for (iname,) in rows:
            print(f"  {iname}")
        names = {r[0] for r in rows}
        for need in ("ix_reports_patient_id", "ix_reports_ocr_status"):
            if need not in names:
                ok = False
                print(f"  FAIL: missing index {need}")
    return ok


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command",
        nargs="?",
        choices=("apply", "verify", "apply-verify"),
        default="apply-verify",
    )
    parser.add_argument(
        "--sql",
        type=Path,
        default=BACKEND / "sql" / "create_reports_table.sql",
        help="Path to create_reports_table.sql",
    )
    args = parser.parse_args()
    sql_path = args.sql.resolve()
    if not sql_path.is_file():
        print(f"ERROR: SQL file not found: {sql_path}", file=sys.stderr)
        sys.exit(1)

    engine = get_engine()

    if args.command in ("apply", "apply-verify"):
        apply_migration(engine, sql_path)

    if args.command in ("verify", "apply-verify"):
        print("\n--- Verification ---")
        if not verify(engine):
            sys.exit(1)
        print("\nVerification passed.")

    sys.exit(0)


if __name__ == "__main__":
    main()
