import json
from openai import OpenAI
from ..config import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)


async def categorise_tasks(tasks: list[str]) -> list[dict]:
    prompt = f"""Categorise each of the following tasks into exactly one of these categories: Personal, Health, or Work.

Tasks:
{chr(10).join(f"- {task}" for task in tasks)}

Respond with a JSON array where each object has "description" (the original task) and "category" (one of: Personal, Health, Work).
Example: [{{"description": "Go to gym", "category": "Health"}}]

Return ONLY the JSON array, no other text."""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )

    content = response.choices[0].message.content.strip()
    if content.startswith("```"):
        content = content.split("\n", 1)[1].rsplit("```", 1)[0]

    return json.loads(content)
