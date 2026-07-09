from commitmate.git_utils import get_staged_diff, get_staged_files, git_commit
from commitmate.message_gen import build_prompt, clean_response, parse_model_response, assemble_commit_message
from commitmate.ollama_client import generate_commit_message
from commitmate.exceptions import CommitMateError
from rich.console import Console
from rich.prompt import Prompt
from rich.markup import escape
import os
import tempfile
import subprocess
import shlex

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



def main():
    console = Console()

    try:
        codes_changed = get_staged_diff()
        files_changed = get_staged_files()
        prompt = build_prompt(codes_changed, files_changed)
        raw_commit_message = generate_commit_message(prompt)
        cleaned = clean_response(raw_commit_message)
        parsed = parse_model_response(cleaned)
        commit_message = assemble_commit_message(parsed)
    except CommitMateError as e:
        console.print(f"[bold red]Error:[/bold red] {escape(str(e))}")
        return

    while True:
        console.print("\n[bold]Generated commit message:[/bold]")

        console.print(f"[cyan]{commit_message}[/cyan]")

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