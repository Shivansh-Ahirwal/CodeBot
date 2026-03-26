import requests
import os


OLLAMA_URL = os.getenv("OLLAMA_URL", "http://host.docker.internal:11434/api/chat")
MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
REQUEST_TIMEOUT_SECONDS = int(os.getenv("OLLAMA_TIMEOUT_SECONDS", "120"))


def ask_llm(messages):
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL,
            "messages": messages,
            "stream": False
        },
        timeout=REQUEST_TIMEOUT_SECONDS
    )

    response.raise_for_status()

    return response.json()["message"]["content"]
