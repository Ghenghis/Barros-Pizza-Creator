from __future__ import annotations

import base64
import hashlib
import json
import re
from pathlib import Path
from typing import Any

from .attachments import AttachmentError, normalize_attachment


MAX_LIBRARY_ITEMS = 500
MAX_SELECTED_ITEMS = 3


class InspirationLibrary:
    def __init__(self, root: Path):
        self.root = root
        self.index_path = root / "index.json"

    def _items(self) -> list[dict[str, Any]]:
        if not self.index_path.is_file():
            return []
        try:
            payload = json.loads(self.index_path.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError):
            return []
        values = payload.get("items", []) if isinstance(payload, dict) else []
        return [item for item in values[:MAX_LIBRARY_ITEMS] if isinstance(item, dict)]

    def status(self) -> dict[str, Any]:
        items = self._items()
        formats: dict[str, int] = {}
        total_bytes = 0
        for item in items:
            format_name = str(item.get("format", "unknown")).upper()
            formats[format_name] = formats.get(format_name, 0) + 1
            total_bytes += int(item.get("bytes", 0) or 0)
        return {
            "configured": self.index_path.is_file(),
            "count": len(items),
            "max_items": MAX_LIBRARY_ITEMS,
            "total_bytes": total_bytes,
            "formats": formats,
        }

    @staticmethod
    def _tokens(value: str) -> set[str]:
        return {token for token in re.findall(r"[a-z0-9]+", value.casefold()) if len(token) > 2}

    def select(self, prompt: str, limit: int = MAX_SELECTED_ITEMS) -> list[dict[str, Any]]:
        prompt_tokens = self._tokens(prompt)
        scored: list[tuple[int, str, dict[str, Any]]] = []
        for item in self._items():
            searchable = " ".join(
                [str(item.get("name", "")), str(item.get("caption", ""))]
                + [str(tag) for tag in item.get("tags", []) if isinstance(tag, str)]
            )
            overlap = len(prompt_tokens & self._tokens(searchable))
            stable = hashlib.sha256((prompt + str(item.get("sha256", ""))).encode("utf-8")).hexdigest()
            scored.append((overlap, stable, item))
        scored.sort(key=lambda row: (-row[0], row[1]))
        return [item for _, _, item in scored[: max(0, min(limit, MAX_SELECTED_ITEMS))]]

    def attachments_for_prompt(self, prompt: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        attachments: list[dict[str, Any]] = []
        public: list[dict[str, Any]] = []
        root = self.root.resolve()
        for item in self.select(prompt):
            relative = Path(str(item.get("path", "")))
            path = (self.root / relative).resolve()
            try:
                path.relative_to(root)
            except ValueError:
                continue
            if not path.is_file() or path.is_symlink():
                continue
            raw = path.read_bytes()
            try:
                normalized = normalize_attachment(
                    {
                        "name": str(item.get("name", path.name))[:512],
                        "mime_type": str(item.get("mime_type", "application/octet-stream")),
                        "data_base64": base64.b64encode(raw).decode("ascii"),
                    }
                )
            except (AttachmentError, OSError):
                continue
            attachments.append(normalized)
            public.append(
                {
                    "id": str(item.get("id", item.get("sha256", "")[:16])),
                    "name": normalized["name"],
                    "sha256": normalized["image_metadata"]["sha256"],
                    "width": normalized["image_metadata"]["width"],
                    "height": normalized["image_metadata"]["height"],
                }
            )
        return attachments, public
