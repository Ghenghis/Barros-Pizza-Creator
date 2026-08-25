from __future__ import annotations

import base64
import binascii
import hashlib
from typing import Any


MAX_ATTACHMENT_BYTES = 4 * 1024 * 1024
MAX_ATTACHMENTS = 8
MAX_TOTAL_IMAGE_BYTES = 12 * 1024 * 1024
SUPPORTED_IMAGE_MIME = {"image/png", "image/jpeg", "image/webp"}


class AttachmentError(ValueError):
    pass


def _positive_dimensions(width: int, height: int, kind: str) -> tuple[int, int]:
    if width < 1 or height < 1 or width > 32768 or height > 32768:
        raise AttachmentError(f"{kind} dimensions are invalid: {width}x{height}")
    return width, height


def _png_dimensions(data: bytes) -> tuple[int, int]:
    signature = b"\x89PNG\r\n\x1a\n"
    if len(data) < 24 or not data.startswith(signature):
        raise AttachmentError("Invalid PNG signature/header.")
    if data[12:16] != b"IHDR":
        raise AttachmentError("PNG is missing the required IHDR chunk.")
    width = int.from_bytes(data[16:20], "big")
    height = int.from_bytes(data[20:24], "big")
    return _positive_dimensions(width, height, "PNG")


_JPEG_SOF = {
    0xC0, 0xC1, 0xC2, 0xC3,
    0xC5, 0xC6, 0xC7,
    0xC9, 0xCA, 0xCB,
    0xCD, 0xCE, 0xCF,
}


def _jpeg_dimensions(data: bytes) -> tuple[int, int]:
    if len(data) < 4 or data[:2] != b"\xff\xd8":
        raise AttachmentError("Invalid JPEG SOI marker.")
    pos = 2
    while pos < len(data):
        if data[pos] != 0xFF:
            pos += 1
            continue
        while pos < len(data) and data[pos] == 0xFF:
            pos += 1
        if pos >= len(data):
            break
        marker = data[pos]
        pos += 1
        if marker in {0xD8, 0xD9, 0x01} or 0xD0 <= marker <= 0xD7:
            continue
        if marker == 0xDA:  # scan data begins; dimensions must already be declared
            break
        if pos + 2 > len(data):
            raise AttachmentError("JPEG segment length is truncated.")
        segment_length = int.from_bytes(data[pos:pos + 2], "big")
        if segment_length < 2 or pos + segment_length > len(data):
            raise AttachmentError("JPEG segment length is invalid or truncated.")
        if marker in _JPEG_SOF:
            if segment_length < 7:
                raise AttachmentError("JPEG SOF segment is too short.")
            height = int.from_bytes(data[pos + 3:pos + 5], "big")
            width = int.from_bytes(data[pos + 5:pos + 7], "big")
            return _positive_dimensions(width, height, "JPEG")
        pos += segment_length
    raise AttachmentError("JPEG has no supported SOF dimensions marker.")


def _webp_dimensions(data: bytes) -> tuple[int, int]:
    if len(data) < 20 or data[:4] != b"RIFF" or data[8:12] != b"WEBP":
        raise AttachmentError("Invalid WebP RIFF header.")
    declared = int.from_bytes(data[4:8], "little") + 8
    if declared > len(data):
        raise AttachmentError("WebP RIFF payload is truncated.")
    pos = 12
    while pos + 8 <= len(data):
        kind = data[pos:pos + 4]
        size = int.from_bytes(data[pos + 4:pos + 8], "little")
        start = pos + 8
        end = start + size
        if end > len(data):
            raise AttachmentError("WebP chunk is truncated.")
        chunk = data[start:end]
        if kind == b"VP8X":
            if len(chunk) < 10:
                raise AttachmentError("WebP VP8X header is truncated.")
            width = 1 + int.from_bytes(chunk[4:7], "little")
            height = 1 + int.from_bytes(chunk[7:10], "little")
            return _positive_dimensions(width, height, "WebP")
        if kind == b"VP8L":
            if len(chunk) < 5 or chunk[0] != 0x2F:
                raise AttachmentError("WebP VP8L header is invalid.")
            bits = int.from_bytes(chunk[1:5], "little")
            width = 1 + (bits & 0x3FFF)
            height = 1 + ((bits >> 14) & 0x3FFF)
            return _positive_dimensions(width, height, "WebP")
        if kind == b"VP8 ":
            if len(chunk) < 10 or chunk[3:6] != b"\x9d\x01\x2a":
                raise AttachmentError("WebP VP8 frame header is invalid.")
            width = int.from_bytes(chunk[6:8], "little") & 0x3FFF
            height = int.from_bytes(chunk[8:10], "little") & 0x3FFF
            return _positive_dimensions(width, height, "WebP")
        pos = end + (size & 1)
    raise AttachmentError("WebP has no supported VP8/VP8L/VP8X image chunk.")


def inspect_image_bytes(data: bytes) -> dict[str, Any]:
    """Identify and parse supported image bytes without trusting filename/MIME."""
    if not data:
        raise AttachmentError("Image attachment is empty.")
    if len(data) > MAX_ATTACHMENT_BYTES:
        raise AttachmentError(f"Image attachment exceeds {MAX_ATTACHMENT_BYTES} decoded bytes.")
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        mime = "image/png"
        width, height = _png_dimensions(data)
        format_name = "PNG"
    elif data.startswith(b"\xff\xd8"):
        mime = "image/jpeg"
        width, height = _jpeg_dimensions(data)
        format_name = "JPEG"
    elif data.startswith(b"RIFF") and len(data) >= 12 and data[8:12] == b"WEBP":
        mime = "image/webp"
        width, height = _webp_dimensions(data)
        format_name = "WEBP"
    else:
        raise AttachmentError("Unsupported or unrecognized image bytes; expected PNG, JPEG, or WebP.")
    return {
        "mime_type": mime,
        "format": format_name,
        "width": width,
        "height": height,
        "bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
    }


def normalize_attachment(attachment: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(attachment, dict):
        raise AttachmentError("Each attachment must be a JSON object.")
    result = dict(attachment)
    name = str(result.get("name", "attachment"))[:512]
    declared_mime = str(result.get("mime_type", "application/octet-stream") or "application/octet-stream").lower()
    encoded = str(result.get("data_base64", "") or "")
    text = str(result.get("text", "") or "")
    result["name"] = name

    if encoded:
        try:
            raw = base64.b64decode(encoded, validate=True)
        except (binascii.Error, ValueError) as exc:
            raise AttachmentError(f"{name}: data_base64 is not valid base64.") from exc
        metadata = inspect_image_bytes(raw)
        if declared_mime.startswith("image/") and declared_mime != metadata["mime_type"]:
            raise AttachmentError(
                f"{name}: declared MIME {declared_mime} does not match decoded {metadata['mime_type']}."
            )
        if declared_mime not in {"application/octet-stream", ""} and not declared_mime.startswith("image/"):
            raise AttachmentError(f"{name}: binary image data cannot use MIME {declared_mime}.")
        result["mime_type"] = metadata["mime_type"]
        result["image_metadata"] = metadata
        result["text"] = ""
        return result

    if declared_mime.startswith("image/"):
        raise AttachmentError(f"{name}: image attachment is missing data_base64.")
    if not text:
        raise AttachmentError(f"{name}: attachment contains neither image data nor text.")
    result["data_base64"] = ""
    result["text"] = text[:12000]
    return result


def normalize_attachments(value: Any) -> list[dict[str, Any]]:
    if value in (None, ""):
        return []
    if not isinstance(value, list):
        raise AttachmentError("attachments must be a JSON array.")
    if len(value) > MAX_ATTACHMENTS:
        raise AttachmentError(f"At most {MAX_ATTACHMENTS} attachments are allowed per request.")
    normalized = [normalize_attachment(item) for item in value]
    total = sum(
        int(item.get("image_metadata", {}).get("bytes", 0))
        for item in normalized
        if isinstance(item.get("image_metadata"), dict)
    )
    if total > MAX_TOTAL_IMAGE_BYTES:
        raise AttachmentError(f"Decoded image attachments exceed {MAX_TOTAL_IMAGE_BYTES} total bytes.")
    return normalized
