import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from src.main import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def mock_openai_response():
    """Create a mock OpenAI API response."""
    def _create_mock(content: str):
        mock_response = AsyncMock()
        mock_response.choices = [AsyncMock()]
        mock_response.choices[0].message.content = content
        return mock_response
    return _create_mock


@pytest.fixture
def mock_openai_client(mock_openai_response):
    """Mock the OpenAI client for testing."""
    with patch("src.submodules.categoriser.client") as mock_client:
        yield mock_client


@pytest.fixture
def sample_tasks():
    """Sample tasks for testing."""
    return ["Go to gym", "Call mom", "Review quarterly report"]


@pytest.fixture
def sample_categorised_response():
    """Sample categorised response matching expected API output."""
    return [
        {"description": "Go to gym", "category": "Health"},
        {"description": "Call mom", "category": "Personal"},
        {"description": "Review quarterly report", "category": "Work"},
    ]
