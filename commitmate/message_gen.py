import json
from commitmate.exceptions import InvalidModelResponseError


COMMIT_TYPES = ["feat", "fix", "docs", "refactor", "test", "chore", "style", "perf"]


def build_prompt(diff: str, files: list[str]) -> str:
    """Constructs the full prompt sent to Ollama for commit message generation."""

    file_list = "\n".join(f"- {f}" for f in files)
    types_list = ", ".join(COMMIT_TYPES)

    return f"""You are a senior software engineer writing a git commit message.

Analyze the staged changes below and respond with a JSON object with exactly these keys:
- "type": one of {types_list}
- "scope": a short noun for what part of the code changed (e.g. a filename or module), or an empty string if no single scope fits
- "description": a short, lowercase, imperative-mood summary (e.g. "add" not "added"), no trailing period, under 72 characters
- "body": 1-3 short bullet points (as a single string, newline-separated) explaining WHY the change was made, or an empty string if not needed

Respond with ONLY the JSON object. No markdown fences, no explanation, no text outside the JSON.

CHANGED FILES:
{file_list}

--- DIFF ---
{diff}
--- END DIFF ---
""".strip()


def clean_response(raw: str) -> str:
    """
    Strips markdown code fences that Ollama sometimes adds even with format=json.
    """
    text = raw.strip()
    lines = text.splitlines()

    if lines and lines[0].strip().startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip().startswith("```"):
        lines = lines[:-1]

    return "\n".join(lines).strip()

def parse_model_response(cleaned: str) -> dict:
    """
    Parses the cleaned JSON string into a dict and validates required fields.
    Raises InvalidModelResponseError if parsing fails or fields are missing/invalid.
    """
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise InvalidModelResponseError(f"Model did not return valid JSON: {e}") from e

    if "type" not in data or "description" not in data:
        raise InvalidModelResponseError(
            f"Model response missing required fields 'type' or 'description': {data}"
        )

    if data["type"] not in COMMIT_TYPES:
        raise InvalidModelResponseError(
            f"Model returned invalid commit type '{data['type']}'. Expected one of {COMMIT_TYPES}."
        )

    return data

def assemble_commit_message(data: dict) -> str:
    """
    Builds the final 'type(scope): description' string (plus optional body)
    from the parsed JSON dict. Pure string formatting, no LLM involved.
    """
    commit_type = data["type"]
    scope = data.get("scope", "").strip()
    description = data["description"].strip()
    body = data.get("body", "").strip()

    header = f"{commit_type}({scope}): {description}" if scope else f"{commit_type}: {description}"

    if body:
        return f"{header}\n\n{body}"
    return header