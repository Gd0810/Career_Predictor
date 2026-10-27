"""
Thin wrapper around NVIDIA AI Build (https://build.nvidia.com/models) chat-completions
style endpoint. Each of the 4 AI-powered features (resume_parser, career_roadmap,
resume_analyzer, chat) can use its own API key + model, matching the 4 NVIDIA accounts
mentioned in the project spec.

If no API key is configured for a feature, or the request fails for any reason
(no network, invalid key, rate limit, etc.), `call_nvidia_ai` returns None and every
calling module falls back to a deterministic, rule-based result so the application
keeps working end-to-end without live AI access.
"""
import json
import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


def call_nvidia_ai(feature: str, system_prompt: str, user_prompt: str, json_mode: bool = True, timeout: int = 30):
    """
    feature: one of 'resume_parser' | 'career_roadmap' | 'resume_analyzer' | 'chat'
    Returns parsed JSON (dict) if json_mode else raw text. Returns None on any failure.
    """
    api_key = settings.NVIDIA_KEYS.get(feature, "")
    model = settings.NVIDIA_MODELS.get(feature, "meta/llama3-70b-instruct")

    if not api_key:
        logger.info("No NVIDIA API key configured for feature '%s' - using fallback.", feature)
        return None

    url = f"{settings.NVIDIA_API_BASE}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.3,
        "max_tokens": 1024,
    }

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        content = data["choices"][0]["message"]["content"]
        if not json_mode:
            return content
        content = content.strip()
        if content.startswith("```"):
            content = content.strip("`")
            if content.startswith("json"):
                content = content[4:]
        return json.loads(content)
    except Exception as exc:  # noqa: BLE001 - deliberately broad: AI calls must never crash the app
        logger.warning("NVIDIA AI call failed for feature '%s': %s", feature, exc)
        return None
