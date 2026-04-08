from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any
from urllib import request


@dataclass
class LLMConfig:
    provider: str
    model: str
    api_base: str
    api_key_env: str
    temperature: float
    max_tokens: int
    timeout_sec: int


class BaseLLMClient:
    def summarize(self, *, system_prompt: str, user_content: str) -> str:
        raise NotImplementedError


class OpenAICompatibleClient(BaseLLMClient):
    def __init__(self, cfg: LLMConfig):
        self.cfg = cfg

    def summarize(self, *, system_prompt: str, user_content: str) -> str:
        api_key = os.getenv(self.cfg.api_key_env)
        if not api_key:
            raise RuntimeError(f"Missing API key env var: {self.cfg.api_key_env}")

        payload: dict[str, Any] = {
            "model": self.cfg.model,
            "temperature": self.cfg.temperature,
            "max_tokens": self.cfg.max_tokens,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
        }
        data = json.dumps(payload).encode("utf-8")
        base = self.cfg.api_base.rstrip("/")
        req = request.Request(
            url=f"{base}/chat/completions",
            data=data,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with request.urlopen(req, timeout=self.cfg.timeout_sec) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        return body["choices"][0]["message"]["content"].strip()


class OllamaClient(BaseLLMClient):
    def __init__(self, cfg: LLMConfig):
        self.cfg = cfg

    def summarize(self, *, system_prompt: str, user_content: str) -> str:
        payload = {
            "model": self.cfg.model,
            "stream": False,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            "options": {
                "temperature": self.cfg.temperature,
            },
        }
        data = json.dumps(payload).encode("utf-8")
        base = self.cfg.api_base.rstrip("/")
        req = request.Request(
            url=f"{base}/api/chat",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with request.urlopen(req, timeout=self.cfg.timeout_sec) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        return body["message"]["content"].strip()


def build_llm_client(llm_section: dict[str, Any]) -> BaseLLMClient:
    cfg = LLMConfig(
        provider=str(llm_section.get("provider", "openai_compatible")),
        model=str(llm_section.get("model", "gpt-4.1-mini")),
        api_base=str(llm_section.get("api_base", "https://api.openai.com/v1")),
        api_key_env=str(llm_section.get("api_key_env", "OPENAI_API_KEY")),
        temperature=float(llm_section.get("temperature", 0.2)),
        max_tokens=int(llm_section.get("max_tokens", 1200)),
        timeout_sec=int(llm_section.get("timeout_sec", 120)),
    )

    if cfg.provider == "openai_compatible":
        return OpenAICompatibleClient(cfg)
    if cfg.provider == "ollama":
        return OllamaClient(cfg)

    raise ValueError(f"Unsupported llm.provider: {cfg.provider}")
