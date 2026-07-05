import subprocess
from commitmate.exceptions import (
    GitNotInstalledError, 
    NotAGitRepositoryError, 
    GitCommandError,
    NoStagedChangesError
)

def get_staged_diff():
    """
    Runs `git diff --staged` and returns the diff as a string.
    Raises NoStagedChangesError if there's nothing staged.
    """
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
    