
import os

import requests

AI_PROVIDER = os.environ.get("AI_PROVIDER", "ollama").lower()
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434").rstrip("/")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "gemma4:e2b")
OPENAI_API_URL = os.environ.get("OPENAI_API_URL", "https://api.openai.com/v1").rstrip("/")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")


def ask_model(prompt: str) -> str:
    if AI_PROVIDER == "openai":
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is required when AI_PROVIDER is openai.")

        response = requests.post(
            f"{OPENAI_API_URL}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": OPENAI_MODEL,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=120,
        )
    elif AI_PROVIDER == "ollama":
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
            },
            timeout=120,
        )
    else:
        raise RuntimeError(f"Unsupported AI_PROVIDER: {AI_PROVIDER}")

    response.raise_for_status()
    payload = response.json()
    if AI_PROVIDER == "openai":
        choices = payload.get("choices")
        answer = choices[0].get("message", {}).get("content") if choices else None
    else:
        answer = payload.get("response")

    if not isinstance(answer, str) or not answer.strip():
        raise ValueError(f"{AI_PROVIDER} returned an empty or invalid response.")

    return answer.strip()
