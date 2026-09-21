from __future__ import annotations

import json

from fastapi import FastAPI, HTTPException, Request
from pydantic import ValidationError

from app.models import ParseRequest, ParseResult
from app.parsing import parse_text

MAX_BODY_BYTES = 1_048_576  # 1 MiB

app = FastAPI(
    title="ThreatLens API",
    version="0.1.0",
    description="Log parser (M1). Detection is not implemented yet.",
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


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
    raw = await request.body()
    if len(raw) > MAX_BODY_BYTES:
        raise HTTPException(status_code=413, detail="Request body exceeds 1 MiB limit.")
    if not raw:
        return ParseResult(events=[], errors=[])

    try:
        decoded = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=400, detail="Body must be valid UTF-8.") from exc

    content_type = (request.headers.get("content-type") or "").split(";")[0].strip().lower()
    text = _extract_text(decoded, content_type)
    if len(text.encode("utf-8")) > MAX_BODY_BYTES:
        raise HTTPException(status_code=413, detail="text exceeds 1 MiB limit.")
    return parse_text(text)


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
