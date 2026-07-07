class CommitMateError(Exception):
    """Base exception for all CommitMate-specific errors."""
    pass


class NotAGitRepositoryError(CommitMateError):
    """Raised when the current directory is not inside a git repository."""
    def __init__(self, message="This command must be run inside a valid Git repository."):
        super().__init__(message)


class NoStagedChangesError(CommitMateError):
    """Raised when there are no staged changes to generate a commit message from."""
    def __init__(self, message="No staged changes found. Stage your changes with 'git add' first."):
        super().__init__(message)


class GitCommandError(CommitMateError):
    """Raised when a git command fails for a reason other than 'not a repo'.
    No default message — the caller must supply the actual git stderr output,
    since the failure reason varies every time."""
    def __init__(self, message):
        super().__init__(message)


class GitNotInstalledError(CommitMateError):
    """Raised when the git executable can't be found on PATH."""
    def __init__(self, message="Git is not installed or not found on PATH."):
        super().__init__(message)



# Ollama Errors
class OllamaConnectionError(CommitMateError):
    """ Raised when the Ollama is not running at all"""
    def __init__(self, message="Ollama is not running"):
        super().__init__(message)

class OllamaTimeoutError(CommitMateError):
    """ Raised when the Ollama connection timed out"""
    def __init__(self, message="Connection timed out, Ollama taking too long to respond"):
        super().__init__(message)

class InvalidModelResponseError(CommitMateError):
    """Raised when the model's response isn't valid JSON or is missing required fields."""
    def __init__(self, message):
        super().__init__(message)
