"""
Shared LLM utility for all agents.
Handles Ollama call + strips <think>...</think> blocks (qwen3, deepseek-r1, etc.)
"""
import re
import requests
import config.settings as _cfg


def strip_think(text: str) -> str:
    """Remove <think>...</think> reasoning blocks that qwen3/deepseek emit."""
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    return text.strip()


def call_ollama(
    prompt: str,
    temperature: float = 0.2,
    num_predict: int = 600,
    timeout: int = 60,
    model: str = None,
) -> tuple[str, str]:
    """
    Call Ollama and return (clean_response, error).
    clean_response has <think> blocks stripped.
    On error, clean_response="" and error contains the message.
    """
    try:
        resp = requests.post(
            f"{_cfg.OLLAMA_BASE_URL}/api/generate",
            json={
                "model": model or _cfg.OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": temperature, "num_predict": num_predict},
            },
            timeout=timeout,
        )
        resp.raise_for_status()
        raw = resp.json().get("response", "")
        return strip_think(raw), ""
    except Exception as e:
        return "", str(e)


def extract_json_object(text: str) -> str | None:
    """Find and return the first JSON object {...} in text."""
    match = re.search(r"\{.*\}", text, re.DOTALL)
    return match.group() if match else None


def extract_json_array(text: str) -> str | None:
    """Find and return the first JSON array [...] in text."""
    match = re.search(r"\[.*\]", text, re.DOTALL)
    return match.group() if match else None
