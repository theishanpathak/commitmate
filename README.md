# CommitMate

A command-line tool that reads your staged git changes and generates a [Conventional Commits](https://www.conventionalcommits.org/)-style commit message using a local LLM via [Ollama](https://ollama.com/) — no cloud API, no API keys, nothing leaves your machine.

You review the generated message and choose to accept it, edit it, or cancel — CommitMate never commits anything without your explicit approval.

## Why

Writing good commit messages consistently is tedious, and generic "wip" or "fix stuff" commits make a project's history much less useful. CommitMate looks at what you've actually staged and proposes a properly formatted message you can accept as-is or tweak, without sending your code to any external service.

## Prerequisites

- Python 3.11 or later
- [Ollama](https://ollama.com/) installed and running locally
- A model pulled in Ollama (this tool defaults to `llama3`):
  ```bash
  ollama pull llama3
  ```
- Ollama's server running (usually automatic after install, or start manually):
  ```bash
  ollama serve
  ```

## Installation

Clone the repo and install it as an editable local package:

```bash
git clone https://github.com/theishanpathak/commitmate.git
cd commitmate
pip install -e .
```

This registers a `commitmate` command on your system, callable from any git repository.

## Usage

1. Stage some changes:
   ```bash
   git add <files>
   ```
2. Run:
   ```bash
   commitmate
   ```
3. CommitMate will show a generated commit message and prompt you to choose:
   - **accept** — commits immediately with the generated message
   - **edit** — opens the message in your `$EDITOR` (falls back to `nano` on Mac/Linux, `notepad` on Windows) so you can revise it before committing
   - **cancel** — exits without committing; your staged changes are left untouched

## How It Works

- **`git_utils.py`** — the only module that shells out to git (via `subprocess`). Retrieves the staged diff and file list, and performs the actual commit.
- **`ollama_client.py`** — a thin HTTP wrapper around Ollama's local `/api/generate` endpoint. Knows nothing about commit messages or git; it just sends a prompt and returns whatever text comes back.
- **`message_gen.py`** — pure, I/O-free logic. Builds the prompt (asking the model to return structured JSON rather than free text), and parses/validates/assembles that JSON into the final `type(scope): description` message.
- **`exceptions.py`** — a small hierarchy of custom exceptions (e.g. `NotAGitRepositoryError`, `NoStagedChangesError`, `OllamaConnectionError`) so failures are caught and reported cleanly instead of surfacing as raw stack traces.
- **`cli.py`** — the composition root. Orchestrates the pipeline above and drives the accept/edit/cancel loop using [`rich`](https://github.com/Textualize/rich) for terminal output.

The model is prompted to return a JSON object (`type`, `scope`, `description`, `body`) rather than a fully formatted commit message string. The actual `type(scope): description` text is then assembled in plain Python. This was a deliberate pivot after an earlier version — which asked the model to return the final formatted string directly — proved unreliable: local models frequently added preambles, markdown fences, or trailing explanations despite explicit instructions not to. Constraining the model to fill in a small number of discrete fields, and letting Python own the final formatting, removed that failure mode almost entirely.

## Known Limitations

- **No diff truncation.** Very large staged diffs are sent to the model in full, with no length guard. This could hit context limits or slow down generation on large changes.
- **Self-referential prompt confusion.** If a staged diff itself contains text that looks like prompt instructions (for example, testing CommitMate on a diff to its own `message_gen.py`, which contains the prompt-building code), the model can occasionally get confused about what's an instruction versus what's data to summarize.
- **GUI editors need a `--wait`-style flag.** The `edit` flow waits for your editor process to exit before continuing. Terminal editors (`nano`, `vim`) work out of the box. GUI editors need an explicit wait flag, e.g.:
  ```bash
  export EDITOR="code --wait"
  ```
  Without it, editors like VS Code return immediately and CommitMate will read the file back before you've finished editing.
- **Model is currently fixed to `llama3`.** `generate_commit_message()` accepts a `model` parameter internally, but there's no CLI flag yet to change it without editing the code. A `--model` option is a natural next step.
- **No automated test suite yet.** The pure functions in `message_gen.py` (especially `clean_response` and `parse_model_response`) are strong candidates for unit tests; this hasn't been added yet.

## Configuration

- **`$EDITOR`** — controls which editor opens during the `edit` flow. Defaults to `nano` (Mac/Linux) or `notepad` (Windows) if unset.
- **Model** — currently hardcoded to `llama3` as the default in `ollama_client.generate_commit_message()`. Change the default there, or pass a different value to `generate_commit_message(prompt, model="...")` if calling it programmatically.

## Requirements

- `requests`
- `rich`

(See `requirements.txt`.)

## Author

Ishan Pathak
[theishanpathak.com](https://theishanpathak.com)

