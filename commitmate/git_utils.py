import subprocess

def get_staged_diff():
    """
    Runs `git diff --staged` and returns the diff as a string.
    """
    try:
        result = subprocess.run(
            ['git', 'diff', '--staged'],
            capture_output=True, 
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"git diff failed: {e.stderr.strip()}") from e
    except FileNotFoundError:
        raise RuntimeError("git is not installed or not found on PATH") from e




def get_staged_files():
    """
    Runs `git diff --staged --name-only` and returns a list of changed file paths.
    Raises RuntimeError if git isn't installed or the command fails.
    """
    try:
        result = subprocess.run(
            ['git', 'diff', '--staged', '--name-only'], 
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip().splitlines()
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"git diff --name-only failed: {e.stderr.strip()}") from e
    except FileNotFoundError as e:
        raise RuntimeError("git is not installed or not found on PATH") from e
    