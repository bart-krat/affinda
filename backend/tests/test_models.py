"""Unit tests for Pydantic models."""

import pytest
from pydantic import ValidationError

from src.models.task import CategoriseRequest, CategorisedTask, CategoriseResponse


class TestCategoriseRequest:
    """Tests for CategoriseRequest model."""

    def test_valid_request_with_tasks(self):
        """Should create request with list of tasks."""
        request = CategoriseRequest(tasks=["Go to gym", "Call mom"])
        assert request.tasks == ["Go to gym", "Call mom"]

    def test_empty_list_raises(self):
        """Should raise error for empty tasks list."""
        with pytest.raises(ValidationError, match="cannot be empty"):
            CategoriseRequest(tasks=[])

    def test_valid_request_with_single_task(self):
        """Should create request with single task."""
        request = CategoriseRequest(tasks=["Single task"])
        assert len(request.tasks) == 1

    def test_invalid_request_missing_tasks(self):
        """Should raise error when tasks field is missing."""
        with pytest.raises(ValidationError):
            CategoriseRequest()

    def test_invalid_request_wrong_type(self):
        """Should raise error when tasks is not a list."""
        with pytest.raises(ValidationError):
            CategoriseRequest(tasks="not a list")

    def test_invalid_request_wrong_item_type(self):
        """Should raise error when tasks contains non-strings."""
        with pytest.raises(ValidationError):
            CategoriseRequest(tasks=[123, 456])

    def test_strips_whitespace(self):
        """Should strip whitespace from tasks."""
        request = CategoriseRequest(tasks=["  Go to gym  ", "  Call mom  "])
        assert request.tasks == ["Go to gym", "Call mom"]

    def test_filters_empty_strings(self):
        """Should filter out empty strings after stripping."""
        request = CategoriseRequest(tasks=["Go to gym", "   ", "Call mom"])
        assert request.tasks == ["Go to gym", "Call mom"]

    def test_max_tasks_limit(self):
        """Should reject more than 50 tasks."""
        tasks = [f"Task {i}" for i in range(51)]
        with pytest.raises(ValidationError, match="Maximum 50 tasks"):
            CategoriseRequest(tasks=tasks)

    def test_task_length_limit(self):
        """Should reject tasks over 500 characters."""
        long_task = "x" * 501
        with pytest.raises(ValidationError, match="too long"):
            CategoriseRequest(tasks=[long_task])


class TestCategorisedTask:
    """Tests for CategorisedTask model."""

    def test_valid_task(self):
        """Should create categorised task with description and category."""
        task = CategorisedTask(description="Go to gym", category="Health")
        assert task.description == "Go to gym"
        assert task.category == "Health"

    def test_valid_categories(self):
        """Should accept valid category values."""
        for category in ["Personal", "Health", "Work"]:
            task = CategorisedTask(description="Task", category=category)
            assert task.category == category

    def test_missing_description(self):
        """Should raise error when description is missing."""
        with pytest.raises(ValidationError):
            CategorisedTask(category="Health")

    def test_missing_category(self):
        """Should raise error when category is missing."""
        with pytest.raises(ValidationError):
            CategorisedTask(description="Go to gym")

    def test_invalid_category_rejected(self):
        """Should reject invalid category values."""
        with pytest.raises(ValidationError):
            CategorisedTask(description="Task", category="Invalid")


class TestCategoriseResponse:
    """Tests for CategoriseResponse model."""

    def test_valid_response_with_tasks(self):
        """Should create response with list of categorised tasks."""
        response = CategoriseResponse(
            categorised=[
                CategorisedTask(description="Go to gym", category="Health"),
                CategorisedTask(description="Call mom", category="Personal"),
            ]
        )
        assert len(response.categorised) == 2

    def test_valid_response_empty_list(self):
        """Should create response with empty categorised list."""
        response = CategoriseResponse(categorised=[])
        assert response.categorised == []

    def test_missing_categorised_field(self):
        """Should raise error when categorised field is missing."""
        with pytest.raises(ValidationError):
            CategoriseResponse()

    def test_response_from_dict_list(self):
        """Should create response from dict representations."""
        response = CategoriseResponse(
            categorised=[
                {"description": "Task 1", "category": "Work"},
                {"description": "Task 2", "category": "Health"},
            ]
        )
        assert len(response.categorised) == 2
        assert response.categorised[0].description == "Task 1"
