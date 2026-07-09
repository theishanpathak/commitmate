from commitmate.git_utils import get_staged_diff, get_staged_files, git_commit
from commitmate.message_gen import build_prompt, clean_response, parse_model_response, assemble_commit_message
from commitmate.ollama_client import generate_commit_message
from commitmate.exceptions import CommitMateError
from rich.console import Console
from rich.prompt import Prompt
from rich.markup import escape


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
            commit_message = Prompt.ask("Enter new commit message", default=commit_message)
            # loop back around: show the updated message, ask again
            # (lets them edit repeatedly, or accept/cancel after editing)


if __name__ == "__main__":
    main()