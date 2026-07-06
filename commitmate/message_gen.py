COMMIT_TYPES = ["feat", "fix", "docs", "refactor", "test", "chore", "style", "perf"]


def build_prompt(diff: str, files: list[str]) -> str:
    """Constructs the full prompt sent to Ollama for commit message generation."""

    file_list = "\n".join(f"- {f}" for f in files)
    types_list = ", ".join(COMMIT_TYPES)

    return f"""You are a senior software engineer writing a git commit message.

Generate a commit message in Conventional Commits format based on the staged changes below.

FORMAT (strict):
<type>(<scope>): <short description>

RULES:
- <type> must be exactly one of: {types_list}
- <scope> is a short noun describing what part of the code changed (e.g. a filename, module, or feature). Omit the scope and parentheses entirely if no single scope fits.
- <short description> is lowercase, imperative mood (e.g. "add" not "added"), no period at the end, under 72 characters.
- Optionally, after the first line, you may add a blank line followed by 1-3 short bullet points explaining WHY the change was made, if the diff makes that clear.

OUTPUT CONSTRAINTS (strict):
- Output ONLY the commit message. No markdown code fences (no ```). No quotes wrapping the message. No preamble like "Here's your commit message:" or explanation after it.
- If you are unsure of the type, pick the closest match rather than inventing a new type.

CHANGED FILES:
{file_list}

--- DIFF ---
{diff}
--- END DIFF ---
""".strip()