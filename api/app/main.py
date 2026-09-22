from __future__ import annotations

import json
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError

from app.detection import default_engine
from app.explain import explain_configured, explain_incidents
from app.models import (
    DetectResult,
    ExplainRequest,
    ExplainResponse,
    ParseRequest,
    ParseResult,
    RulesResponse,
)
from app.parsing import parse_text
from app.rate_limit import RateLimitMiddleware, rate_limit_config_summary

MAX_BODY_BYTES = 1_048_576  # 1 MiB — keep this bound; see docs/deploy.md
DEFAULT_CORS_ORIGINS = "http://localhost:3000,http://127.0.0.1:3000"

logger = logging.getLogger("uvicorn.error")


def cors_origins() -> list[str]:
    """Browser origins allowed to call this API. Override with CORS_ORIGINS.

    Default is local Next.js only. A deployed Vercel origin will not work until
    CORS_ORIGINS lists it explicitly. Wildcard ``*`` is accepted but logged as a
    warning — prefer the exact https origin so this stays production-safe.
    """
    raw = os.getenv("CORS_ORIGINS", DEFAULT_CORS_ORIGINS)
    return [item.strip() for item in raw.split(",") if item.strip()]


@asynccontextmanager
async def lifespan(_app: FastAPI):
    origins = cors_origins()
    if any(origin == "*" for origin in origins):
        logger.warning(
            "CORS_ORIGINS includes '*'. Prefer explicit https origins for the Vercel app."
        )
    # Startup logs are config only — never env dumps, bodies, or keys.
    logger.info(
        "API ready: cors_origins=%s max_body_bytes=%s rate_limit=%s explain_configured=%s",
        origins,
        MAX_BODY_BYTES,
        rate_limit_config_summary(),
        explain_configured(),
    )
    yield


app = FastAPI(
    title="ThreatLens API",
    version="0.7.0",
    description=(
        "Log parser and detection engine. Rules: brute_force, credential_spray, "
        "unusual_login, impossible_travel (simulated geo), request_frequency, "
        "restricted_access. Optional POST /explain summarizes incidents the engine "
        "already returned — it does not detect, score, or invent findings. "
        "Missing OPENAI_API_KEY returns 503. Stateless: persistence and auth live "
        "in the Next.js app via Supabase (Option A). 1 MiB body cap; in-memory POST rate limit."
    ),
    lifespan=lifespan,
)

# Last add_middleware call is outermost. CORS must wrap the rate limiter so 429
# responses still include Access-Control-Allow-Origin.
app.add_middleware(RateLimitMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins(),
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

engine = default_engine()


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness only. No config, no secrets, no dependency on Supabase."""
    return {"status": "ok"}


@app.get("/rules", response_model=RulesResponse)
def list_rules() -> RulesResponse:
    """Registered detectors and their thresholds."""
    return RulesResponse(rules=engine.rule_info())


@app.post(
    "/parse",
    response_model=ParseResult,
    responses={
        400: {"description": "Body is not valid UTF-8 or JSON envelope"},
        413: {"description": "Body exceeds 1 MiB"},
        429: {"description": "Rate limit exceeded"},
    },
)
async def parse_logs(request: Request) -> ParseResult:
    """Normalize raw auth/access log text. Does not run detection."""
    text = await _read_log_text(request)
    if text is None:
        return ParseResult(events=[], errors=[])
    return parse_text(text)


@app.post(
    "/detect",
    response_model=DetectResult,
    responses={
        400: {"description": "Body is not valid UTF-8 or JSON envelope"},
        413: {"description": "Body exceeds 1 MiB"},
        429: {"description": "Rate limit exceeded"},
    },
)
async def detect_logs(request: Request) -> DetectResult:
    """Parse log text and run the registered detection rules."""
    text = await _read_log_text(request)
    if text is None:
        return DetectResult(events_count=0, incidents=[], parse_errors=[])
    parsed = parse_text(text)
    incidents = engine.run(parsed.events)
    return DetectResult(
        events_count=len(parsed.events),
        incidents=incidents,
        parse_errors=parsed.errors,
    )


@app.post(
    "/explain",
    response_model=ExplainResponse,
    responses={
        400: {"description": "No incidents to explain, or the body is not valid JSON"},
        413: {"description": "Body exceeds 1 MiB"},
        422: {"description": "Incidents payload failed validation"},
        429: {"description": "Rate limit exceeded"},
        502: {"description": "Explain provider failed; no explanation was invented"},
        503: {"description": "OPENAI_API_KEY is not set"},
    },
)
async def explain(request: Request) -> ExplainResponse:
    """Summarize incidents the caller already has. Does not run detection."""
    parsed = await _read_explain_request(request)
    return ExplainResponse(explanation=explain_incidents(parsed))


async def _read_explain_request(request: Request) -> ExplainRequest:
    raw = await request.body()
    if len(raw) > MAX_BODY_BYTES:
        raise HTTPException(status_code=413, detail="Request body exceeds 1 MiB limit.")
    if not raw:
        raise HTTPException(
            status_code=400,
            detail='JSON body must be {"incidents": [...]} from the detection engine.',
        )
    try:
        decoded = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=400, detail="Body must be valid UTF-8.") from exc
    try:
        payload = json.loads(decoded)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {exc.msg}") from exc
    try:
        return ExplainRequest.model_validate(payload)
    except ValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail='JSON body must be {"incidents": [...], "context"?: string}.',
        ) from exc


async def _read_log_text(request: Request) -> str | None:
    """Return log text, or None for an empty body. Raises HTTPException on bad input.

    Request bodies are not logged. Oversized bodies are rejected before parse.
    """
    raw = await request.body()
    if len(raw) > MAX_BODY_BYTES:
        raise HTTPException(status_code=413, detail="Request body exceeds 1 MiB limit.")
    if not raw:
        return None

    try:
        decoded = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=400, detail="Body must be valid UTF-8.") from exc

    content_type = (request.headers.get("content-type") or "").split(";")[0].strip().lower()
    text = _extract_text(decoded, content_type)
    if len(text.encode("utf-8")) > MAX_BODY_BYTES:
        raise HTTPException(status_code=413, detail="text exceeds 1 MiB limit.")
    return text


def _extract_text(decoded: str, content_type: str) -> str:
    if content_type != "application/json":
        return decoded

    try:
        payload = json.loads(decoded)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {exc.msg}") from exc

    try:
        parsed = ParseRequest.model_validate(payload)
    except ValidationError as exc:
        raise HTTPException(
            status_code=400,
            detail='JSON body must be {"text": "<log lines>"}.',
        ) from exc
    return parsed.text
