from __future__ import annotations

import json
import mimetypes
import os
import random
import time
import urllib.error
import urllib.request
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class ProviderSettings:
    provider: str = "offline"
    endpoint: str = "http://127.0.0.1:1234/v1"
    model: str = "local-model"
    api_key: str = ""
    api_key_env: str = "OPENAI_API_KEY"
    api_key_file: str = ""
    env_file: str = "G:\\private\\.env.openai"
    timeout_seconds: int = 90
    retries: int = 2
    stt_endpoint: str = ""
    stt_model: str = "whisper-1"
    tts_provider: str = "disabled"
    tts_endpoint: str = ""
    tts_region: str = ""
    tts_key: str = ""
    tts_key_env: str = "AZURE_SPEECH_KEY"
    tts_key_file: str = ""

    @classmethod
    def load(cls, path: str | os.PathLike[str]) -> "ProviderSettings":
        settings = cls()
        file_path = Path(path)
        if file_path.exists():
            payload = json.loads(file_path.read_text(encoding="utf-8"))
            for key in settings.__dataclass_fields__:
                if key in payload:
                    setattr(settings, key, payload[key])
        return settings

    def resolved_key(self) -> str:
        if self.api_key:
            return self.api_key.strip()
        if self.api_key_env and os.getenv(self.api_key_env):
            return str(os.getenv(self.api_key_env)).strip()
        key_path = Path(os.path.expandvars(self.api_key_file)) if self.api_key_file else None
        if key_path and key_path.exists():
            value = key_path.read_text(encoding="utf-8-sig", errors="replace").strip()
            if "=" in value and "\n" not in value:
                key, candidate = value.split("=", 1)
                if not self.api_key_env or key.strip() == self.api_key_env:
                    value = candidate.strip().strip('"').strip("'")
            if value:
                return value
        env_path = Path(os.path.expandvars(self.env_file)) if self.env_file else None
        if env_path and env_path.exists():
            for line in env_path.read_text(encoding="utf-8-sig", errors="replace").splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                if key.strip() == self.api_key_env:
                    return value.strip().strip('"').strip("'")
        return ""

    def resolved_tts_key(self) -> str:
        if self.tts_key:
            return self.tts_key.strip()
        if self.tts_key_env and os.getenv(self.tts_key_env):
            return str(os.getenv(self.tts_key_env)).strip()
        key_path = Path(os.path.expandvars(self.tts_key_file)) if self.tts_key_file else None
        if key_path and key_path.exists():
            value = key_path.read_text(encoding="utf-8-sig", errors="replace").strip()
            if "=" in value and "\n" not in value:
                key, candidate = value.split("=", 1)
                if not self.tts_key_env or key.strip() == self.tts_key_env:
                    value = candidate.strip().strip('"').strip("'")
            if value:
                return value
        env_path = Path(os.path.expandvars(self.env_file)) if self.env_file else None
        if env_path and env_path.exists():
            for line in env_path.read_text(encoding="utf-8-sig", errors="replace").splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                if key.strip() == self.tts_key_env:
                    return value.strip().strip('"').strip("'")
        return ""


class ProviderError(RuntimeError):
    pass


def extract_json(text: str) -> Any:
    cleaned = (text or "").strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned[3:]
        if cleaned.rstrip().endswith("```"):
            cleaned = cleaned.rstrip()[:-3].rstrip()
    candidates = [cleaned]
    for opener, closer in (("{", "}"), ("[", "]")):
        start = cleaned.find(opener)
        end = cleaned.rfind(closer)
        if start >= 0 and end > start:
            candidates.append(cleaned[start : end + 1])
    for candidate in candidates:
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            continue
    raise ProviderError("The model response did not contain valid JSON.")


class ProviderClient:
    def __init__(self, settings: ProviderSettings):
        self.settings = settings

    @property
    def online(self) -> bool:
        return self.settings.provider.casefold() not in {"", "offline", "none"}

    def complete(
        self,
        system: str,
        user: str,
        temperature: float = 0.65,
        *,
        timeout_seconds: int | None = None,
        retries: int | None = None,
    ) -> str:
        return self.complete_multimodal(
            system,
            user,
            [],
            temperature,
            timeout_seconds=timeout_seconds,
            retries=retries,
        )

    def complete_multimodal(
        self,
        system: str,
        user: str,
        attachments: list[dict[str, Any]],
        temperature: float = 0.65,
        *,
        timeout_seconds: int | None = None,
        retries: int | None = None,
    ) -> str:
        provider = self.settings.provider.casefold()
        if not self.online:
            raise ProviderError("Provider is configured for offline mode.")
        if provider == "ollama":
            return self._ollama(
                system, user, temperature, attachments, timeout_seconds, retries
            )
        if provider == "anthropic":
            return self._anthropic(
                system, user, temperature, attachments, timeout_seconds, retries
            )
        return self._openai_compatible(
            system, user, temperature, attachments, timeout_seconds, retries
        )

    def _request(
        self,
        request: urllib.request.Request,
        timeout_seconds: int | None = None,
        retries: int | None = None,
    ) -> bytes:
        effective_timeout = max(
            1,
            int(self.settings.timeout_seconds if timeout_seconds is None else timeout_seconds),
        )
        effective_retries = max(
            0,
            int(self.settings.retries if retries is None else retries),
        )
        last_error: Exception | None = None
        for attempt in range(effective_retries + 1):
            try:
                with urllib.request.urlopen(request, timeout=effective_timeout) as response:
                    return response.read()
            except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
                last_error = exc
                if attempt >= effective_retries:
                    break
                time.sleep((2**attempt) + random.random() * 0.2)
        raise ProviderError("Provider request failed: %s" % last_error)

    def _openai_compatible(
        self,
        system: str,
        user: str,
        temperature: float,
        attachments: list[dict[str, Any]],
        timeout_seconds: int | None = None,
        retries: int | None = None,
    ) -> str:
        endpoint = self.settings.endpoint.rstrip("/")
        if not endpoint.endswith("/chat/completions"):
            endpoint += "/chat/completions"
        user_content: Any = user
        image_parts = []
        for attachment in attachments:
            mime = str(attachment.get("mime_type", ""))
            encoded = str(attachment.get("data_base64", ""))
            if mime.startswith("image/") and encoded:
                image_parts.append(
                    {"type": "image_url", "image_url": {"url": "data:%s;base64,%s" % (mime, encoded)}}
                )
        if image_parts:
            user_content = [{"type": "text", "text": user}] + image_parts
        payload = {
            "model": self.settings.model,
            "temperature": temperature,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user_content},
            ],
        }
        headers = {"Content-Type": "application/json"}
        key = self.settings.resolved_key()
        if key:
            headers["Authorization"] = "Bearer " + key
        raw = self._request(
            urllib.request.Request(
                endpoint,
                data=json.dumps(payload).encode("utf-8"),
                headers=headers,
                method="POST",
            ),
            timeout_seconds,
            retries,
        )
        response = json.loads(raw.decode("utf-8"))
        return str(response["choices"][0]["message"]["content"])

    def _ollama(
        self,
        system: str,
        user: str,
        temperature: float,
        attachments: list[dict[str, Any]],
        timeout_seconds: int | None = None,
        retries: int | None = None,
    ) -> str:
        endpoint = self.settings.endpoint.rstrip("/")
        if endpoint.endswith("/v1"):
            endpoint = endpoint[:-3]
        if not endpoint.endswith("/api/chat"):
            endpoint += "/api/chat"
        user_message: dict[str, Any] = {"role": "user", "content": user}
        images = [
            str(item.get("data_base64"))
            for item in attachments
            if str(item.get("mime_type", "")).startswith("image/") and item.get("data_base64")
        ]
        if images:
            user_message["images"] = images
        payload = {
            "model": self.settings.model,
            "stream": False,
            "options": {"temperature": temperature},
            "messages": [
                {"role": "system", "content": system},
                user_message,
            ],
        }
        raw = self._request(
            urllib.request.Request(
                endpoint,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            ),
            timeout_seconds,
            retries,
        )
        response = json.loads(raw.decode("utf-8"))
        return str(response["message"]["content"])

    def _anthropic(
        self,
        system: str,
        user: str,
        temperature: float,
        attachments: list[dict[str, Any]],
        timeout_seconds: int | None = None,
        retries: int | None = None,
    ) -> str:
        endpoint = self.settings.endpoint.rstrip("/")
        if not endpoint.endswith("/messages"):
            endpoint += "/messages"
        content: Any = user
        parts: list[dict[str, Any]] = []
        for item in attachments:
            mime = str(item.get("mime_type", ""))
            encoded = str(item.get("data_base64", ""))
            if mime.startswith("image/") and encoded:
                parts.append(
                    {"type": "image", "source": {"type": "base64", "media_type": mime, "data": encoded}}
                )
        if parts:
            content = parts + [{"type": "text", "text": user}]
        payload = {
            "model": self.settings.model,
            "max_tokens": 1800,
            "temperature": temperature,
            "system": system,
            "messages": [{"role": "user", "content": content}],
        }
        headers = {
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01",
            "x-api-key": self.settings.resolved_key(),
        }
        raw = self._request(
            urllib.request.Request(
                endpoint,
                data=json.dumps(payload).encode("utf-8"),
                headers=headers,
                method="POST",
            ),
            timeout_seconds,
            retries,
        )
        response = json.loads(raw.decode("utf-8"))
        return str(response["content"][0]["text"])

    def transcribe(self, wav: bytes, filename: str = "voice.wav") -> str:
        endpoint = (self.settings.stt_endpoint or self.settings.endpoint).rstrip("/")
        if endpoint.endswith("/v1"):
            endpoint += "/audio/transcriptions"
        elif not endpoint.endswith("/audio/transcriptions"):
            endpoint += "/v1/audio/transcriptions"
        boundary = "----BarrosAI" + uuid.uuid4().hex
        chunks: list[bytes] = []

        def add_field(name: str, value: str) -> None:
            chunks.extend(
                [
                    ("--%s\r\n" % boundary).encode(),
                    ('Content-Disposition: form-data; name="%s"\r\n\r\n' % name).encode(),
                    value.encode(),
                    b"\r\n",
                ]
            )

        add_field("model", self.settings.stt_model)
        mime = mimetypes.guess_type(filename)[0] or "audio/wav"
        chunks.extend(
            [
                ("--%s\r\n" % boundary).encode(),
                ('Content-Disposition: form-data; name="file"; filename="%s"\r\n' % filename).encode(),
                ("Content-Type: %s\r\n\r\n" % mime).encode(),
                wav,
                b"\r\n",
                ("--%s--\r\n" % boundary).encode(),
            ]
        )
        headers = {"Content-Type": "multipart/form-data; boundary=" + boundary}
        key = self.settings.resolved_key()
        if key:
            headers["Authorization"] = "Bearer " + key
        raw = self._request(
            urllib.request.Request(endpoint, data=b"".join(chunks), headers=headers, method="POST")
        )
        response = json.loads(raw.decode("utf-8"))
        return str(response.get("text", "")).strip()
