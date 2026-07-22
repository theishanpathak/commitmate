# CommitMate

A command-line tool that reads your staged git changes and generates a [Conventional Commits](https://www.conventionalcommits.org/)-style commit message using a local LLM via [Ollama](https://ollama.com/) — no cloud API, no API keys, nothing leaves your machine.

You review the generated message and choose to accept it, edit it, or cancel — CommitMate never commits anything without your explicit approval.

## Why

Writing good commit messages consistently is tedious, and generic "wip" or "fix stuff" commits make a project's history much less useful. CommitMate looks at what you've actually staged and proposes a properly formatted message you can accept as-is or tweak, without sending your code to any external service.

## Prerequisites

- Python 3.9 or later
- [Ollama](https://ollama.com/) installed and running locally
- A model pulled in Ollama. The tool defaults to `llama3`:
  ```bash
  ollama pull llama3
  ```
  `qwen2.5-coder:7b` is also recommended and performed better in testing on multi-file diffs (see Known Limitations below). If you want to use it, pull it too and pass `--model qwen2.5-coder:7b`:
  ```bash
  ollama pull qwen2.5-coder:7b
  ```
- Ollama's server running (usually automatic after install, or start manually):
  ```bash
  ollama serve
  ```

## Installation

### For users

Install directly from PyPI:

```bash
pip install commitmate
```

This registers a `commitmate` command on your system, callable from any git repository.

### For developers / contributors

If you want to modify the source, run tests, or contribute:

```bash
git clone https://github.com/theishanpathak/commitmate.git
cd commitmate
pip install -e .
```

The `-e` (editable) install links the `commitmate` command back to your local source files, so any changes you make take effect immediately without reinstalling.

## Usage

1. Stage some changes:
   ```bash
   git add <files>
   ```
   Tip: for best results, stage related changes together rather than many unrelated files at once. Smaller local models can struggle to summarize a diff spanning several unrelated files into a single, well-formatted commit message.
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
- **`exceptions.py`** — a small hierarchy of custom exceptions (e.g. `NotAGitRepositoryError`, `NoStagedChangesError`, `OllamaConnectionError`, `InvalidModelResponseError`) so failures are caught and reported cleanly instead of surfacing as raw stack traces.
- **`cli.py`** — the composition root. Orchestrates the pipeline above, retries generation a few times if the model's response fails validation, and drives the accept/edit/cancel loop using [`rich`](https://github.com/Textualize/rich) for terminal output.

The model is prompted to return a JSON object (`reasoning`, `type`, `scope`, `description`, `body`) rather than a fully formatted commit message string. The actual `type(scope): description` text is then assembled in plain Python. This was a deliberate pivot after an earlier version — which asked the model to return the final formatted string directly — proved unreliable: local models frequently added preambles, markdown fences, or trailing explanations despite explicit instructions not to. Constraining the model to fill in a small number of discrete fields, and letting Python own the final formatting, removed that failure mode almost entirely.

A `reasoning` field is requested first in the JSON schema, before the other fields. Since JSON keys are generated in order, this gives the model a place to briefly "think" about the change before committing to a `type`/`description`, without breaking strict JSON output. This measurably improved how often the description stayed within a reasonable length.

If the model's response fails validation (wrong type, description too short, malformed JSON, etc.) after a few attempts, CommitMate shows a friendly message suggesting the diff may be too large or span too many unrelated files, rather than surfacing the raw internal validation error.

## Known Limitations

- **Multi-file diffs can produce longer subject lines.** Smaller/general-purpose local models (tested: `llama3`, the default) sometimes struggle to keep the commit description under the ~72-character convention when a diff spans multiple unrelated files. In testing, `qwen2.5-coder:7b` performed noticeably better at staying within length limits on the same diffs. Consider passing `--model qwen2.5-coder:7b` if you run into this.
- **No diff truncation.** Very large staged diffs are sent to the model in full, with no length guard. This could hit context limits or slow down generation on large changes.
- **Self-referential prompt confusion.** If a staged diff itself contains text that looks like prompt instructions (for example, testing CommitMate on a diff to its own `message_gen.py`, which contains the prompt-building code), the model can occasionally get confused about what's an instruction versus what's data to summarize.
- **GUI editors need a `--wait`-style flag.** The `edit` flow waits for your editor process to exit before continuing. Terminal editors (`nano`, `vim`) work out of the box. GUI editors need an explicit wait flag, e.g.:
  ```bash
  export EDITOR="code --wait"
  ```
  Without it, editors like VS Code return immediately and CommitMate will read the file back before you've finished editing.

## Testing

Run the test suite with:
```bash
pip install -e ".[dev]"
pytest
```
Tests currently cover the pure logic in `message_gen.py` (prompt cleanup, response validation, and message assembly). `git_utils.py` and `ollama_client.py` involve subprocess/network calls and aren't covered yet — mocking those is a natural next step.


## Configuration

- **`$EDITOR`** — controls which editor opens during the `edit` flow. Defaults to `nano` (Mac/Linux) or `notepad` (Windows) if unset.
- **`--model`** — choose which Ollama model to use. Defaults to `llama3`:
  ```bash
  commitmate --model qwen2.5-coder:7b
  ```
  See Known Limitations above for why `qwen2.5-coder:7b` may give better results on multi-file diffs.

## Requirements

- `requests`
- `rich`

(See `requirements.txt`.)

## Contributing

Contributions are welcome. After cloning and installing with `pip install -e .` (see Installation above), you can make changes and test them immediately with the `commitmate` command, no reinstall needed.

If you want to build the distributable package yourself:
```bash
pip install build
python -m build
```
This produces a `.whl` and `.tar.gz` in `dist/`, which you can install into a fresh virtual environment to verify the packaging is correct before opening a PR.

## Author

Ishan Pathak
[theishanpathak.com](https://theishanpathak.com)