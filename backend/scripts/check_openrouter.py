"""Verify OpenRouter connectivity and report API key limits."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[2]
ENV_PATH = ROOT_DIR / ".env"
OPENROUTER_BASE = "https://openrouter.ai/api/v1"


def load_api_key() -> str:
    load_dotenv(ENV_PATH)
    api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
    if not api_key:
        print(f"ERROR: OPENROUTER_API_KEY is missing. Expected it in {ENV_PATH}")
        sys.exit(1)
    return api_key


def auth_headers(api_key: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }


def print_key_limits(data: dict) -> None:
    print("\n=== API key limits ===")
    print(f"  Label:            {data.get('label', 'n/a')}")
    print(f"  Free tier:        {data.get('is_free_tier', 'n/a')}")
    print(f"  Credit limit:     {data.get('limit')}")
    print(f"  Limit remaining:  {data.get('limit_remaining')}")
    print(f"  Limit reset:      {data.get('limit_reset')}")
    print(f"  Usage (all time): ${data.get('usage', 0):.4f}")
    print(f"  Usage (daily):    ${data.get('usage_daily', 0):.4f}")
    print(f"  Usage (weekly):   ${data.get('usage_weekly', 0):.4f}")
    print(f"  Usage (monthly):  ${data.get('usage_monthly', 0):.4f}")


def check_key_info(client: httpx.Client) -> bool:
    response = client.get(f"{OPENROUTER_BASE}/key")
    if response.status_code != 200:
        print(f"ERROR: GET /key failed ({response.status_code}): {response.text}")
        return False

    data = response.json().get("data", {})
    print_key_limits(data)
    return True


def check_chat_completion(client: httpx.Client, model: str) -> bool:
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": "Reply with exactly: OK"}],
        "max_tokens": 10,
    }
    response = client.post(f"{OPENROUTER_BASE}/chat/completions", json=payload)
    if response.status_code != 200:
        print(f"\nERROR: Chat completion failed ({response.status_code}): {response.text}")
        return False

    body = response.json()
    reply = body["choices"][0]["message"]["content"].strip()
    model_used = body.get("model", model)
    print("\n=== Chat completion test ===")
    print(f"  Model:    {model_used}")
    print(f"  Response: {reply!r}")
    print("  Status:   OK")
    return True


def main() -> None:
    api_key = load_api_key()
    masked = f"...{api_key[-8:]}" if len(api_key) > 8 else "(set)"
    model = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")

    print("OpenRouter check")
    print(f"  Env file: {ENV_PATH}")
    print(f"  API key:  {masked}")
    print(f"  Model:    {model}")

    headers = auth_headers(api_key)
    with httpx.Client(headers=headers, timeout=60.0) as client:
        key_ok = check_key_info(client)
        chat_ok = check_chat_completion(client, model) if key_ok else False

    if key_ok and chat_ok:
        print("\nResult: OpenRouter is working.")
        sys.exit(0)

    print("\nResult: OpenRouter check failed.")
    sys.exit(1)


if __name__ == "__main__":
    main()
