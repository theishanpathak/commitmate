from commitmate.config import load_config, save_config
from commitmate.git_utils import get_staged_diff, get_staged_files, git_commit
from commitmate.message_gen import build_prompt, clean_response, parse_model_response, assemble_commit_message
from commitmate.ollama_client import generate_commit_message
from commitmate.exceptions import CommitMateError, InvalidModelResponseError
from rich.console import Console
from rich.prompt import Prompt
from rich.markup import escape
import os
import tempfile
import subprocess
import shlex
import argparse

MAX_ATTEMPTS = 3
DEFAULT_MODEL = "llama3"

def edit_in_editor(initial_text: str) -> str:
    """
    Opens the user's $EDITOR with initial_text pre-filled in a temp file,
    waits for them to edit and close it, then returns the saved content.
    Falls back to nano (Mac/Linux) or notepad (Windows) if $EDITOR isn't set.
    """
    editor_cmd = os.environ.get("EDITOR", "notepad" if os.name == "nt" else "nano")

    with tempfile.NamedTemporaryFile(suffix=".txt", mode="w", delete=False) as tf:
        tf.write(initial_text)
        temp_path = tf.name

    try:
        subprocess.run(shlex.split(editor_cmd) + [temp_path])
        with open(temp_path, "r") as tf:
            edited = tf.read()
    finally:
        os.remove(temp_path)


    return edited.strip()



def generate_valid_commit_message(prompt: str, console: Console, model: str) -> dict:
    """
    Calls Ollama and validates the response, retrying up to MAX_ATTEMPTS times
    if the model returns something that fails validation.
    """
    last_error = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        with console.status(f"[bold cyan]Generating commit message with {model} (attempt {attempt}/{MAX_ATTEMPTS})..."):
            raw = generate_commit_message(prompt, model)
        try:
            cleaned = clean_response(raw)
            parsed = parse_model_response(cleaned)
            return parsed
        except InvalidModelResponseError as e:
            last_error = e
            continue
    raise last_error



def parse_args():
    parser = argparse.ArgumentParser(
        prog="commitmate",
        description="Generate a Conventional Commits-style message from staged git changes using a local Ollama model."
    )
    parser.add_argument(
        "--model",
        default=None,
        help=f"Use this model for this run only (default: {DEFAULT_MODEL}, or the repo's saved default if set)."
    )
    parser.add_argument(
        "--set-model",
        default=None,
        help="Save this model as the default for this repository, then exit."
    )
    return parser.parse_args()



def main():
    console = Console()
    args = parse_args()

    if args.set_model:
        try:
            config = load_config()
            config["model"] = args.set_model
            save_config(config)
            console.print(f"[bold green]Saved '{args.set_model}' as the default model for this repo.[/bold green]")
        except CommitMateError as e:
            console.print(f"[bold red]Error:[/bold red] {escape(str(e))}")
        return

    try:
        config = load_config()
        model = args.model or config.get("model") or DEFAULT_MODEL

        codes_changed = get_staged_diff()
        files_changed = get_staged_files()
        prompt = build_prompt(codes_changed, files_changed)
        parsed = generate_valid_commit_message(prompt, console, model=model)
        commit_message = assemble_commit_message(parsed)

    except InvalidModelResponseError:
        console.print(
            "[bold red]Error:[/bold red] The model couldn't produce a well-formatted "
            "commit message after several attempts."
        )
        console.print(
            "[yellow]Tip: this often happens with diffs spanning many unrelated files. "
            "Try staging fewer files at a time.[/yellow]"
        )
        return
    except CommitMateError as e:
        console.print(f"[bold red]Error:[/bold red] {escape(str(e))}")
        return

    while True:
        console.print("\n[bold]Generated commit message:[/bold]")
        console.print(f"[cyan]{escape(commit_message)}[/cyan]")

        choice = Prompt.ask(
            "Select an action",
            choices=["accept", "edit", "cancel"],
            default="accept"
        )

        if choice == "accept":
            try:
                git_commit(commit_message)
                console.print("[bold green]Committed.[/bold green]")
            except CommitMateError as e:
                console.print(f"[bold red]Commit failed:[/bold red] {escape(str(e))}")
            return

        elif choice == "cancel":
            console.print("[bold red]Cancelled. No commit made.[/bold red]")
            return

        elif choice == "edit":
            console.print("[dim]Opening editor — save and close the file/tab when you're done.[/dim]")
            commit_message = edit_in_editor(commit_message)


if __name__ == "__main__":
    main()