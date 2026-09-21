from __future__ import annotations

import json
import os

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError

from app.detection import default_engine
from app.models import DetectResult, ParseRequest, ParseResult, RulesResponse
from app.parsing import parse_text

MAX_BODY_BYTES = 1_048_576  # 1 MiB
DEFAULT_CORS_ORIGINS = "http://localhost:3000,http://127.0.0.1:3000"


def cors_origins() -> list[str]:
    """Browser origins allowed to call this API. Override with CORS_ORIGINS."""
    raw = os.getenv("CORS_ORIGINS", DEFAULT_CORS_ORIGINS)
    return [item.strip() for item in raw.split(",") if item.strip()]


app = FastAPI(
    title="ThreatLens API",
    version="0.4.0",
    description=(
        "Log parser and detection engine (M4). Rules: brute_force, credential_spray, "
        "unusual_login, impossible_travel (simulated geo), request_frequency, "
        "restricted_access. Stateless: persistence and auth live in the Next.js app "
        "via Supabase (Option A). No AI."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins(),
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = default_engine()


@app.get("/health")
def health() -> dict[str, str]:
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


async def _read_log_text(request: Request) -> str | None:
    """Return log text, or None for an empty body. Raises HTTPException on bad input."""
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
