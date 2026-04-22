"""Unit tests for the categoriser module."""

import json
import pytest
from unittest.mock import MagicMock, patch

from src.submodules.categoriser import categorise_tasks


class TestCategoriseTasks:
    """Tests for categorise_tasks function."""

    @pytest.fixture
    def mock_completion(self):
        """Create a mock completion response."""
        def _create(content: str):
            mock = MagicMock()
            mock.choices = [MagicMock()]
            mock.choices[0].message.content = content
            return mock
        return _create

    @pytest.mark.asyncio
    async def test_categorise_single_task(self, mock_completion):
        """Should categorise a single task."""
        expected_response = [{"description": "Go to gym", "category": "Health"}]

        with patch("src.submodules.categoriser.client") as mock_client:
            mock_client.chat.completions.create.return_value = mock_completion(
                json.dumps(expected_response)
            )

            result = await categorise_tasks(["Go to gym"])

            assert result == expected_response
            mock_client.chat.completions.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_categorise_multiple_tasks(self, mock_completion):
        """Should categorise multiple tasks."""
        expected_response = [
            {"description": "Go to gym", "category": "Health"},
            {"description": "Call mom", "category": "Personal"},
            {"description": "Review report", "category": "Work"},
        ]

        with patch("src.submodules.categoriser.client") as mock_client:
            mock_client.chat.completions.create.return_value = mock_completion(
                json.dumps(expected_response)
            )

            result = await categorise_tasks(["Go to gym", "Call mom", "Review report"])

            assert result == expected_response
            assert len(result) == 3

    @pytest.mark.asyncio
    async def test_categorise_empty_tasks(self, mock_completion):
        """Should handle empty tasks list."""
        expected_response = []

        with patch("src.submodules.categoriser.client") as mock_client:
            mock_client.chat.completions.create.return_value = mock_completion(
                json.dumps(expected_response)
            )

            result = await categorise_tasks([])

            assert result == []

    @pytest.mark.asyncio
    async def test_handles_markdown_code_block(self, mock_completion):
        """Should strip markdown code blocks from response."""
        expected_response = [{"description": "Go to gym", "category": "Health"}]
        markdown_wrapped = f"```json\n{json.dumps(expected_response)}\n```"

        with patch("src.submodules.categoriser.client") as mock_client:
            mock_client.chat.completions.create.return_value = mock_completion(
                markdown_wrapped
            )

            result = await categorise_tasks(["Go to gym"])

            assert result == expected_response

    @pytest.mark.asyncio
    async def test_handles_markdown_without_language(self, mock_completion):
        """Should strip markdown code blocks without language specifier."""
        expected_response = [{"description": "Task", "category": "Work"}]
        markdown_wrapped = f"```\n{json.dumps(expected_response)}\n```"

        with patch("src.submodules.categoriser.client") as mock_client:
            mock_client.chat.completions.create.return_value = mock_completion(
                markdown_wrapped
            )

            result = await categorise_tasks(["Task"])

            assert result == expected_response

    @pytest.mark.asyncio
    async def test_uses_correct_model(self, mock_completion):
        """Should use gpt-4o-mini model."""
        with patch("src.submodules.categoriser.client") as mock_client:
            mock_client.chat.completions.create.return_value = mock_completion("[]")

            await categorise_tasks(["Test"])

            call_args = mock_client.chat.completions.create.call_args
            assert call_args.kwargs["model"] == "gpt-4o-mini"

    @pytest.mark.asyncio
    async def test_uses_zero_temperature(self, mock_completion):
        """Should use temperature=0 for deterministic responses."""
        with patch("src.submodules.categoriser.client") as mock_client:
            mock_client.chat.completions.create.return_value = mock_completion("[]")

            await categorise_tasks(["Test"])

            call_args = mock_client.chat.completions.create.call_args
            assert call_args.kwargs["temperature"] == 0

    @pytest.mark.asyncio
    async def test_prompt_includes_all_tasks(self, mock_completion):
        """Should include all tasks in the prompt."""
        tasks = ["Task 1", "Task 2", "Task 3"]

        with patch("src.submodules.categoriser.client") as mock_client:
            mock_client.chat.completions.create.return_value = mock_completion("[]")

            await categorise_tasks(tasks)

            call_args = mock_client.chat.completions.create.call_args
            prompt = call_args.kwargs["messages"][0]["content"]

            for task in tasks:
                assert task in prompt

    @pytest.mark.asyncio
    async def test_raises_on_invalid_json_response(self, mock_completion):
        """Should raise error when OpenAI returns invalid JSON."""
        from src.submodules.categoriser import CategorizationError

        with patch("src.submodules.categoriser.client") as mock_client:
            mock_client.chat.completions.create.return_value = mock_completion(
                "This is not valid JSON"
            )

            with pytest.raises(CategorizationError, match="Invalid response format"):
                await categorise_tasks(["Test"])
