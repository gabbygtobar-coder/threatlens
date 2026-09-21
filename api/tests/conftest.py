from pathlib import Path
import os

# Disable the in-memory limiter for the existing suite. Dedicated tests re-enable it.
os.environ.setdefault("RATE_LIMIT_ENABLED", "false")

import pytest
from fastapi.testclient import TestClient

from app.main import app

FIXTURES_DIR = Path(__file__).resolve().parents[2] / "fixtures"


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def fixtures_dir() -> Path:
    return FIXTURES_DIR
