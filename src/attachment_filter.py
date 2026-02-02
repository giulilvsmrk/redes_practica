# src/attachment_filter.py
from __future__ import annotations
from dataclasses import dataclass
from email.message import Message
from typing import Iterable


BLOCKED_MIME_PREFIXES = ("image/",)
BLOCKED_MIME_EXACT = ("application/pdf", "application/x-pdf")
BLOCKED_EXTENSIONS = (
    ".pdf",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".bmp",
    ".tiff",
    ".svg",
)


@dataclass(frozen=True)
class BlockedPartInfo:
    index: int
    content_type: str
    filename: str | None
    disposition: str | None


def _norm(s: str | None) -> str | None:
    return s.strip().lower() if s else None


def is_blocked_mime(content_type: str) -> bool:
    ct = content_type.lower().strip()
    if ct in BLOCKED_MIME_EXACT:
        return True
    return any(ct.startswith(prefix) for prefix in BLOCKED_MIME_PREFIXES)


def is_blocked_filename(filename: str | None) -> bool:
    if not filename:
        return False
    fn = filename.lower().strip()
    return any(fn.endswith(ext) for ext in BLOCKED_EXTENSIONS)


def iter_leaf_parts(msg: Message) -> Iterable[Message]:
    if msg.is_multipart():
        for part in msg.walk():
            if not part.is_multipart():
                yield part
    else:
        yield msg


def classify_parts(msg: Message) -> tuple[list[BlockedPartInfo], list[Message]]:
    blocked: list[BlockedPartInfo] = []
    allowed: list[Message] = []

    for i, part in enumerate(iter_leaf_parts(msg), start=1):
        ctype = (part.get_content_type() or "application/octet-stream").lower()
        filename = part.get_filename()
        disposition = part.get("Content-Disposition")
        disp_norm = _norm(disposition)

        blocked_by_mime = is_blocked_mime(ctype)
        blocked_by_name = is_blocked_filename(filename)

        if blocked_by_mime or blocked_by_name:
            blocked.append(
                BlockedPartInfo(
                    index=i,
                    content_type=ctype,
                    filename=filename,
                    disposition=disp_norm,
                )
            )
            continue

        allowed.append(part)

    return blocked, allowed


def extract_text_plain_only(
    msg: Message, *, max_chars: int = 50_000
) -> tuple[str, list[BlockedPartInfo]]:
    blocked, allowed_parts = classify_parts(msg)

    chunks: list[str] = []
    total = 0

    for part in allowed_parts:
        ctype = (part.get_content_type() or "").lower()

        # Solo texto plano
        if ctype != "text/plain":
            continue

        disp_norm = _norm(part.get("Content-Disposition")) or ""
        if disp_norm.startswith("attachment"):
            continue

        payload_bytes = part.get_payload(decode=True)

        if payload_bytes is None:
            payload = part.get_payload()
            if isinstance(payload, str):
                text = payload
            else:
                continue
        else:
            charset = part.get_content_charset() or "utf-8"
            try:
                text = payload_bytes.decode(charset, errors="replace")
            except LookupError:
                text = payload_bytes.decode("utf-8", errors="replace")

        if not text:
            continue

        remaining = max_chars - total
        if remaining <= 0:
            break

        if len(text) > remaining:
            text = text[:remaining]

        chunks.append(text)
        total += len(text)

        if total >= max_chars:
            break

    safe_text = "\n".join(chunks)
    return safe_text, blocked
