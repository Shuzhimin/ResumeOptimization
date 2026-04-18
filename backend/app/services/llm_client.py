import json
import re

import httpx

from backend.app.core.config import Settings


class DeepSeekClient:
    def __init__(self, settings: Settings):
        self.settings = settings

    async def chat_json(self, system_prompt: str, user_prompt: str) -> dict:
        if not self.settings.deepseek_api_key:
            raise ValueError("DEEPSEEK_API_KEY is not configured.")

        url = f"{self.settings.deepseek_base_url.rstrip('/')}/chat/completions"
        payload = {
            "model": self.settings.deepseek_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.3,
            "response_format": {"type": "json_object"},
        }
        headers = {
            "Authorization": f"Bearer {self.settings.deepseek_api_key}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
        except httpx.HTTPError as exc:
            response_text = ""
            if isinstance(exc, httpx.HTTPStatusError):
                response_text = exc.response.text[:500]
            raise RuntimeError(f"DeepSeek request failed: {exc}. Response: {response_text}") from exc

        data = response.json()
        try:
            content = data["choices"][0]["message"]["content"]
            return self._parse_json_content(content)
        except (KeyError, IndexError, json.JSONDecodeError, TypeError) as exc:
            raise RuntimeError("DeepSeek returned an invalid JSON response.") from exc

    @staticmethod
    def _parse_json_content(content: str) -> dict:
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            fenced_match = re.search(r"```(?:json)?\s*(\{.*\})\s*```", content, re.DOTALL)
            if fenced_match:
                return json.loads(fenced_match.group(1))

            object_match = re.search(r"(\{.*\})", content, re.DOTALL)
            if object_match:
                return json.loads(object_match.group(1))
            raise
