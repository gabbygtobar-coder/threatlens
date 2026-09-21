"""Static checks for M6 harden/deploy files.

No live Vercel/Render/Supabase. These tests only read the repo.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
WEB_SOURCE_SUFFIXES = {".ts", ".tsx", ".js", ".mjs"}


def test_dockerfile_is_minimal_and_avoids_env_files() -> None:
    dockerfile = (REPO_ROOT / "api" / "Dockerfile").read_text(encoding="utf-8")
    assert "FROM python:3.12-slim" in dockerfile
    assert "uvicorn app.main:app" in dockerfile
    assert "0.0.0.0" in dockerfile
    assert "COPY app ./app" in dockerfile
    assert "COPY .env" not in dockerfile
    dockerignore = (REPO_ROOT / "api" / ".dockerignore").read_text(encoding="utf-8")
    assert ".env" in dockerignore
    assert "tests" in dockerignore


def test_deploy_docs_cover_gabby_steps() -> None:
    text = (REPO_ROOT / "docs" / "deploy.md").read_text(encoding="utf-8")
    for needle in (
        "Supabase",
        "Confirm email",
        "CORS_ORIGINS",
        "Root Directory",
        "`web`",
        "NEXT_PUBLIC_API_URL",
        "NEXT_PUBLIC_SUPABASE_URL",
        "NEXT_PUBLIC_SUPABASE_ANON_KEY",
        "service_role",
        "/health",
        "/rules",
        "/analyze",
        "/analyses",
        "brute_force",
    ):
        assert needle in text, f"missing {needle!r} in docs/deploy.md"


def test_next_config_sets_security_headers() -> None:
    text = (REPO_ROOT / "web" / "next.config.ts").read_text(encoding="utf-8")
    for header in (
        "X-Content-Type-Options",
        "X-Frame-Options",
        "Referrer-Policy",
        "Permissions-Policy",
        "Cross-Origin-Opener-Policy",
        "poweredByHeader: false",
    ):
        assert header in text, f"missing {header!r} in next.config.ts"


def test_web_source_does_not_reference_service_role_key() -> None:
    offenders: list[str] = []
    for path in (REPO_ROOT / "web").rglob("*"):
        if not path.is_file() or path.suffix not in WEB_SOURCE_SUFFIXES:
            continue
        if "node_modules" in path.parts or ".next" in path.parts:
            continue
        text = path.read_text(encoding="utf-8")
        if "SUPABASE_SERVICE_ROLE" in text or "service_role" in text.lower():
            # Prose warnings are allowed; an env lookup is not.
            if "process.env" in text and "SERVICE_ROLE" in text:
                offenders.append(str(path.relative_to(REPO_ROOT)))
            elif "createClient" in text and "service_role" in text.lower():
                offenders.append(str(path.relative_to(REPO_ROOT)))
    assert offenders == []


def test_no_root_vercel_json() -> None:
    assert not (REPO_ROOT / "vercel.json").exists()
    assert not (REPO_ROOT / "web" / "vercel.json").exists()
