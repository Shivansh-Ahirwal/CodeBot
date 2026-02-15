import requests


OLLAMA_URL = "http://host.docker.internal:11434/api/chat"
MODEL = "qwen2.5:7b"


def ask_llm(messages):
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL,
            "messages": messages,
            "stream": False
        },
        timeout=120
    )

    response.raise_for_status()

    return response.json()["message"]["content"]
