import requests
from commitmate.exceptions import (
    OllamaConnectionError,
    OllamaTimeoutError
)


def generate_commit_message(prompt: str, model: str = "llama3", timeout: int = 30):

    url = "http://localhost:11434/api/generate"

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False
    }

    try:
        response = requests.post(url, json = payload, timeout=timeout)
        response.raise_for_status()

        data = response.json()
        return data["response"]
    except requests.exceptions.Timeout as e:
        raise OllamaTimeoutError() from e
    except requests.exceptions.ConnectionError as e:
        raise OllamaConnectionError() from e
