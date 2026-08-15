import json
from pathlib import Path
from commitmate.git_utils import get_git_dir


def _get_config_path() -> Path:
    """Locates the repo-local config file inside .git/commitmate/."""
    git_dir = get_git_dir()
    config_dir = Path(git_dir) / "commitmate"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / "config.json"


def load_config() -> dict:
    """Loads the repo-local config, returning {} if none exists yet."""
    path = _get_config_path()
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError:
        return {} 


def save_config(config: dict) -> None:
    """Writes the config dict to the repo-local config file."""
    path = _get_config_path()
    path.write_text(json.dumps(config, indent=2))