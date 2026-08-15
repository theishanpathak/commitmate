import subprocess
from commitmate.exceptions import (
    GitNotInstalledError, 
    NotAGitRepositoryError, 
    GitCommandError,
    NoStagedChangesError
)


def _ensure_in_git_repo():
    """
    Uses `git rev-parse --is-inside-work-tree` to reliably check whether the
    current directory is inside a git repository. This is more robust than
    parsing `git diff`'s error text, which can vary across git versions.
    """
    try:
        subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            capture_output=True,
            text=True,
            check=True
        )
    except subprocess.CalledProcessError as e:
        raise NotAGitRepositoryError() from e
    except FileNotFoundError as e:
        raise GitNotInstalledError() from e



def get_staged_diff():
    """
    Runs `git diff --staged` and returns the diff as a string.
    Raises NoStagedChangesError if there's nothing staged.
    """
    _ensure_in_git_repo()
    try:
        result = subprocess.run(
            ['git', 'diff', '--staged'],
            capture_output=True, 
            text=True,
            check=True
        )
    except subprocess.CalledProcessError as e:
        if "not a git repository" in e.stderr.strip().casefold():
            raise NotAGitRepositoryError() from e
        else:
            raise GitCommandError(e.stderr.strip()) from e
    except FileNotFoundError as e:
        raise GitNotInstalledError() from e
    
    if not result.stdout.strip():
        raise NoStagedChangesError()
    
    return result.stdout
    

def get_staged_files():
    """
      Runs `git diff --staged --name-only` and returns a list of changed file paths.
    """
    _ensure_in_git_repo()
    try:
        result = subprocess.run(
            ['git', 'diff', '--staged', '--name-only'], 
            capture_output=True,
            text=True,
            check=True
        )
    except subprocess.CalledProcessError as e:
        if "not a git repository" in e.stderr.strip().casefold():
            raise NotAGitRepositoryError() from e
        else:
            raise GitCommandError(e.stderr.strip()) from e
    except FileNotFoundError as e:
        raise GitNotInstalledError() from e
    
    return result.stdout.strip().splitlines()
    

def git_commit(message: str):
    """Runs 'git commit -m ...' with the approved message."""
    try:
        subprocess.run(
            ["git", "commit", "-m", message],
            capture_output=True,
            text= True,
            check=True
        )
    except subprocess.CalledProcessError as e:
        raise GitCommandError(e.stderr.strip()) from e

def get_git_dir() -> str:
    """Returns the path to the current repo's .git directory."""
    _ensure_in_git_repo()
    result = subprocess.run(
        ["git", "rev-parse", "--git-dir"],
        capture_output=True,
        text=True,
        check=True
    )
    return result.stdout.strip()