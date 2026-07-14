import json
from commitmate.exceptions import InvalidModelResponseError


COMMIT_TYPES = ["feat", "fix", "docs", "refactor", "test", "chore", "style", "perf"]


def build_prompt(diff: str, files: list[str]) -> str:
    """Constructs the full prompt sent to Ollama for commit message generation."""

    file_list = "\n".join(f"- {f}" for f in files)
    types_list = ", ".join(COMMIT_TYPES)

    return f"""You are an expert software engineer writing a Conventional Git Commit message.

Your task is to analyze the staged changes below and output a single JSON object.

CRITICAL RULES:
1. Output ONLY valid JSON. Do not include markdown code blocks (```), introductory text, or explanations.
2. "reasoning": briefly note, in one short sentence, what the key change is across all files. This is scratch space to help you think before answering, keep it under 15 words.
3. "type": must be exactly one of {types_list}.
4. "scope": a short noun for the changed module. Leave empty ("") if broad.
5. "description": MUST be a short, descriptive phrase starting with an imperative verb (e.g., "add support for user login", NOT just a single word like "add" or "update").
6. "description": MUST NOT have trailing punctuation (no periods or semicolons at the end). MUST be 5-9 words long, this is a hard limit, not a suggestion.
7. "body": 1-3 short bullet points explaining WHY the change was made, or an empty string ("").

Respond with ONLY the JSON object, with keys in this exact order: reasoning, type, scope, description, body. No markdown fences, no explanation, no text outside the JSON.

[EXAMPLES]
Input changes: Added support for fetching from tavily and startup search.
Output:
{{
  "reasoning": "added tavily search integration and startup-specific query support",
  "type": "feat",
  "scope": "web_search",
  "description": "add tavily search and startup query support",
  "body": "- integrate tavily API for expanded data sources\\n- enable targeted startup queries"
}}

Input changes: fixed the api timeout crash
Output:
{{
  "reasoning": "client was crashing on slow api responses due to no timeout handling",
  "type": "fix",
  "scope": "api",
  "description": "resolve timeout crash in client module",
  "body": ""
}}
[END OF EXAMPLES]
Before writing your answer, briefly consider each changed file listed above individually. Then write ONE summary description that reflects meaningful changes across ALL of them, not just the last file.

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
    Raises InvalidModelResponseError if parsing fails, fields are missing,
    or fields are the wrong type.
    """
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise InvalidModelResponseError(f"Model did not return valid JSON: {e}") from e

    if not isinstance(data, dict):
        raise InvalidModelResponseError(f"Model response must be a JSON object, got {type(data).__name__}")

    if "type" not in data or "description" not in data:
        raise InvalidModelResponseError(
            f"Model response missing required fields 'type' or 'description': {data}"
        )

    if data["type"] not in COMMIT_TYPES:
        raise InvalidModelResponseError(
            f"Model returned invalid commit type '{data['type']}'. Expected one of {COMMIT_TYPES}."
        )

    if not isinstance(data["description"], str):
        raise InvalidModelResponseError(
            f"'description' must be a string, got {type(data['description']).__name__}"
        )

    if len(data["description"].split()) < 3:
        raise InvalidModelResponseError(
            f"Description too short (must be at least 3 words): '{data['description']}'"
        )

    if "scope" in data and not isinstance(data["scope"], str):
        raise InvalidModelResponseError(
            f"'scope' must be a string, got {type(data['scope']).__name__}"
        )

    if isinstance(data.get("body"), list):
        data["body"] = "\n".join(str(item) for item in data["body"])
    elif "body" in data and not isinstance(data["body"], str):
        raise InvalidModelResponseError(
            f"'body' must be a string or list, got {type(data['body']).__name__}"
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