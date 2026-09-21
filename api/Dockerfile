# Minimal image for Render / Railway / Fly. Build from this directory:
#   docker build -t threatlens-api .
# The process binds 0.0.0.0:$PORT (default 8000). Health: GET /health.
# Do not bake secrets into the image — set CORS_ORIGINS (and optional RATE_LIMIT_*)
# on the host.

FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

RUN useradd --system --uid 1000 --no-create-home appuser \
    && chown -R appuser:appuser /app
USER appuser

ENV PORT=8000 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
