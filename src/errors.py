# src/errors.py
from __future__ import annotations


class Pop3SecureClientError(Exception):
    """Error base del cliente POP3 seguro."""

# Sesión POP3
class Pop3ConnectionError(Pop3SecureClientError):
    """Fallo de conexion, TLS o socket."""


class Pop3AuthenticationError(Pop3SecureClientError):
    """Credenciales invalidas o AUTH rechazada."""


class Pop3ProtocolError(Pop3SecureClientError):
    """Respuesta POP3 invalida o comando fallido."""


class Pop3SessionClosedError(Pop3SecureClientError):
    """Uso de sesión cerrada o quit prematuro."""


class MessageFetchError(Pop3SecureClientError):
    """Fallo al obtener el contenido del mensaje (TOP/RETR)."""


class MessageParseError(Pop3SecureClientError):
    """Fallo al parsear MIME/headers/cuerpo."""


# Seguridad de contenido 
class UnsafeContentBlockedError(Pop3SecureClientError):
    """Se detecto contenido no permitido (PDF/imagenes) y fue bloqueado."""

    def __init__(self, reason: str, *, content_type: str | None = None, filename: str | None = None):
        self.reason = reason
        self.content_type = content_type
        self.filename = filename
        msg = f"Blocked unsafe content: {reason}"
        if content_type:
            msg += f" | content_type={content_type}"
        if filename:
            msg += f" | filename={filename}"
        super().__init__(msg)