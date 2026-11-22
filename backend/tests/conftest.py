import os

os.environ["ENVIRONMENT"] = "test"
os.environ["RATE_LIMIT_PER_MINUTE"] = "1000"

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import app

get_settings.cache_clear()


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    get_settings.cache_clear()
    with TestClient(app) as test_client:
        yield test_client
