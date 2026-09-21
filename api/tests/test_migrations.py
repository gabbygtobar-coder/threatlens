"""Static checks for M4 migrations and env templates.

These tests read files in the repo. They do not connect to Supabase and must
stay green in CI without credentials.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MIGRATIONS_DIR = REPO_ROOT / "supabase" / "migrations"


def _migration_sql() -> str:
    files = sorted(MIGRATIONS_DIR.glob("*.sql"))
    assert files, f"expected SQL files in {MIGRATIONS_DIR}"
    return "\n".join(path.read_text(encoding="utf-8") for path in files).lower()


def test_migrations_directory_has_sql() -> None:
    sql_files = list(MIGRATIONS_DIR.glob("*.sql"))
    assert sql_files, "supabase/migrations/ must contain at least one .sql file"


def test_schema_defines_required_tables() -> None:
    sql = _migration_sql()
    for table in ("profiles", "analyses", "incidents"):
        assert f"create table public.{table}" in sql, f"missing table {table}"


def test_schema_enables_rls() -> None:
    sql = _migration_sql()
    for table in ("profiles", "analyses", "incidents"):
        assert f"alter table public.{table} enable row level security" in sql, (
            f"RLS not enabled on {table}"
        )


def test_schema_has_own_row_policies() -> None:
    sql = _migration_sql()
    for table in ("profiles", "analyses", "incidents"):
        for action in ("select", "insert", "update", "delete"):
            needle = f"{table}_{action}_own"
            assert needle in sql, f"missing policy {needle}"
    assert "auth.uid()" in sql
    assert "auth.users" in sql


def test_incidents_insert_checks_parent_analysis() -> None:
    sql = _migration_sql()
    assert "incidents_insert_own" in sql
    assert "from public.analyses" in sql


def test_web_env_example_lists_public_keys_only() -> None:
    text = (REPO_ROOT / "web" / ".env.example").read_text(encoding="utf-8")
    assert "NEXT_PUBLIC_SUPABASE_URL=" in text
    assert "NEXT_PUBLIC_SUPABASE_ANON_KEY=" in text
    assert "NEXT_PUBLIC_API_URL=" in text
    assert "SERVICE_ROLE" not in text.replace("SUPABASE_SERVICE_ROLE_KEY", "")
    lowered = text.lower()
    assert "service_role" in lowered
    assert "never" in lowered


def test_api_env_example_documents_cors() -> None:
    text = (REPO_ROOT / "api" / ".env.example").read_text(encoding="utf-8")
    assert "CORS_ORIGINS=" in text
    assert "localhost:3000" in text
