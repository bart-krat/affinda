import json
import logging
from openai import OpenAI, OpenAIError
from ..config import OPENAI_API_KEY

logger = logging.getLogger(__name__)

if not OPENAI_API_KEY:
    logger.warning("OPENAI_API_KEY not set - categorization will fail")
    client = None
else:
    client = OpenAI(api_key=OPENAI_API_KEY)


class CategorizationError(Exception):
    """Error during task categorization."""
    pass


async def categorise_tasks(tasks: list[str]) -> list[dict]:
    """
    Categorize tasks using OpenAI LLM.

    Args:
        tasks: List of task descriptions

    Returns:
        List of dicts with 'description' and 'category' keys

    Raises:
        CategorizationError: If categorization fails
    """
    if client is None:
        raise CategorizationError("OpenAI API key not configured")

    if not tasks:
        return []

    logger.info(f"Categorizing {len(tasks)} tasks")

    prompt = f"""Categorise each of the following tasks into exactly one of these categories: Personal, Health, or Work.

Tasks:
{chr(10).join(f"- {task}" for task in tasks)}

Respond with a JSON array where each object has "description" (the original task) and "category" (one of: Personal, Health, Work).
Example: [{{"description": "Go to gym", "category": "Health"}}]

Return ONLY the JSON array, no other text."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            timeout=30,
        )
    except OpenAIError as e:
        logger.error(f"OpenAI API error: {e}")
        raise CategorizationError(f"OpenAI API error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error calling OpenAI: {e}")
        raise CategorizationError(f"Failed to call categorization service: {str(e)}")

    if not response.choices:
        raise CategorizationError("No response from categorization service")

    content = response.choices[0].message.content
    if not content:
        raise CategorizationError("Empty response from categorization service")

    content = content.strip()

    # Handle markdown code blocks
    if content.startswith("```"):
        lines = content.split("\n")
        # Remove first line (```json or ```)
        lines = lines[1:]
        # Remove last line if it's just ``
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        content = "\n".join(lines)

    try:
        result = json.loads(content)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM response: {content[:200]}")
        raise CategorizationError(f"Invalid response format from categorization service")

    if not isinstance(result, list):
        raise CategorizationError("Invalid response format: expected list")

    # Validate and normalize results
    valid_categories = {"Personal", "Health", "Work"}
    validated = []
    for item in result:
        if not isinstance(item, dict):
            continue
        if "description" not in item or "category" not in item:
            continue

        category = item["category"]
        # Normalize category
        if category not in valid_categories:
            # Try to match case-insensitively
            for valid in valid_categories:
                if category.lower() == valid.lower():
                    category = valid
                    break
            else:
                # Default to Personal if unknown
                logger.warning(f"Unknown category '{category}', defaulting to Personal")
                category = "Personal"

        validated.append({
            "description": str(item["description"]),
            "category": category,
        })

    # Ensure we have results for all input tasks
    if len(validated) != len(tasks):
        logger.warning(f"Categorized {len(validated)} tasks, expected {len(tasks)}")
        # Fill in missing tasks with default category
        existing_descriptions = {v["description"].lower() for v in validated}
        for task in tasks:
            if task.lower() not in existing_descriptions:
                validated.append({
                    "description": task,
                    "category": "Personal",  # Default category
                })

    logger.info(f"Successfully categorized {len(validated)} tasks")
    return validated
