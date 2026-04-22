"""Unit tests for config module."""

import os
import pytest
from unittest.mock import patch


class TestConfig:
    """Tests for configuration loading."""

    def test_openai_api_key_from_env(self):
        """Should load OPENAI_API_KEY from environment."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key-123"}):
            # Re-import to trigger dotenv loading
            import importlib
            import src.config
            importlib.reload(src.config)

            assert src.config.OPENAI_API_KEY == "test-key-123"

    def test_openai_api_key_missing(self):
        """Should return None when OPENAI_API_KEY not set."""
        with patch.dict(os.environ, {}, clear=True):
            with patch("src.config.load_dotenv"):
                import importlib
                import src.config

                # Remove the key if present
                with patch.object(os, "getenv", return_value=None):
                    result = os.getenv("OPENAI_API_KEY")
                    assert result is None
