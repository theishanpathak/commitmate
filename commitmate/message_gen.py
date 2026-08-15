import json
import re
from commitmate.exceptions import InvalidModelResponseError


COMMIT_TYPES = ["feat", "fix", "docs", "refactor", "test", "chore", "style", "perf"]

_BAD_SCOPE_PATTERN = re.compile(
    r"(\band\b|,|/|\.(py|js|ts|jsx|tsx|json|md|txt|html|css)\b)",
    re.IGNORECASE
)

def _is_bad_scope(scope: str) -> bool:
    """
    Flags a scope as invalid if it looks like multiple joined items rather than a single noun"""
    if _BAD_SCOPE_PATTERN.search(scope):
        return True
    if len(scope.split()) > 2:
        return True
    return False


def build_prompt(diff: str, files: list[str]) -> str:
    """Constructs the full prompt sent to Ollama for commit message generation."""

    file_list = "\n".join(f"- {f}" for f in files)

    return f"""You are an expert software engineer writing a Conventional Git Commit message.

Your task is to analyze the staged changes below and output a single JSON object.

CRITICAL RULES:
1. Output ONLY valid JSON. Do not include markdown code blocks (```), introductory text, or explanations.
2. "reasoning": briefly note, in one short sentence, what the key change is across all files. This is scratch space to help you think before answering, keep it under 15 words.
3. "type": choose the ONE type that best fits the actual nature of the change, not just the most common one:
   - "feat": a new feature or capability that did not exist before
   - "fix": a bug fix, correcting incorrect behavior
   - "refactor": restructuring or renaming code with NO change in behavior
   - "docs": documentation only (README, comments, docstrings)
   - "test": adding or modifying tests only
   - "chore": maintenance, tooling, config, dependencies, build scripts
   - "style": formatting, whitespace, or naming changes with no logic change
   - "perf": a change specifically made to improve performance
   Do not default to "feat" or "fix" out of habit, pick the type that actually matches the diff.
4. "scope": ONE single word or short noun naming the module/component affected (e.g. "cli", "auth", "parser"). NEVER list multiple files, NEVER use "and", commas, slashes, or file extensions (e.g. ".py"). Leave empty ("") if the change spans multiple unrelated areas.
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

Input changes: renamed variables and reorganized helper functions in utils.py, no behavior change
Output:
{{
  "reasoning": "pure code reorganization for clarity, no functional change",
  "type": "refactor",
  "scope": "utils",
  "description": "reorganize helper functions for clarity",
  "body": ""
}}

Input changes: updated CI workflow yaml and bumped dependency versions
Output:
{{
  "reasoning": "routine maintenance of build tooling and dependencies",
  "type": "chore",
  "scope": "ci",
  "description": "update workflow config and bump dependencies",
  "body": ""
}}
[END OF EXAMPLES]

Before writing your answer, briefly consider each changed file listed above individually. Then write ONE summary that reflects meaningful changes across ALL of them, not just the last file.

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
    from the parsed JSON dict. Drops the scope entirely if it looks like
    multiple joined items (bad content), or if including it would push the
    subject line past 80 characters (length backstop).
    """
    commit_type = data["type"]
    scope = data.get("scope", "").strip()
    description = data["description"].strip()
    body = data.get("body", "").strip()

    if scope and _is_bad_scope(scope):
        scope = ""

    header = f"{commit_type}({scope}): {description}" if scope else f"{commit_type}: {description}"

    if len(header) > 80 and scope:
        scope = ""
        header = f"{commit_type}: {description}"

    if body:
        return f"{header}\n\n{body}"
    return header