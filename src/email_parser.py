# src/email_parser.py
from __future__ import annotations

from email import policy
from email.parser import BytesParser
from email.message import Message
from typing import Dict, Any

from src.attachment_filter import extract_text_plain_only, BlockedPartInfo
from src.errors import MessageParseError


def parse_email(raw_email: bytes) -> Dict[str, Any]:
    """
    Parsea un correo electrónico en formato bytes y devuelve información segura:
    - Subject
    - From
    - Date
    - Body (solo texto plano)
    - Adjuntos bloqueados (PDF / imágenes)

    Nunca abre ni guarda adjuntos.
    """
    try:
        msg: Message = BytesParser(policy=policy.default).parsebytes(raw_email)
    except Exception as exc:
        raise MessageParseError(f"Error al parsear el mensaje MIME: {exc}") from exc

    headers = extract_headers(msg)
    body, blocked_parts = extract_safe_body(msg)

    return {
        "subject": headers.get("subject"),
        "from": headers.get("from"),
        "date": headers.get("date"),
        "body": body,
        "blocked_attachments": blocked_parts,
    }


def extract_headers(msg: Message) -> Dict[str, str | None]:
    """
    Extrae headers importantes del correo.
    """
    return {
        "subject": msg.get("Subject"),
        "from": msg.get("From"),
        "date": msg.get("Date"),
    }


def extract_safe_body(msg: Message) -> tuple[str, list[BlockedPartInfo]]:
    """
    Extrae únicamente el cuerpo del correo en texto plano,
    bloqueando PDFs e imágenes.
    """
    try:
        text, blocked = extract_text_plain_only(msg)
        return text.strip(), blocked
    except Exception as exc:
        raise MessageParseError(f"Error al extraer el cuerpo del mensaje: {exc}") from exc
