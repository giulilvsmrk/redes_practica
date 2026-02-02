#src/pop3_server.py
from __future__ import annotations
import socket
import ssl

from errors import (
    Pop3ConnectionError,
    Pop3AuthenticationError,
    Pop3ProtocolError,
    Pop3SessionClosedError,
    MessageFetchError,
)

class POP3Client:

    def __init__(self, server, port=110, use_ssl=False, timeout=10):
        self.server = server
        self.port = port
        self.use_ssl = use_ssl
        self.timeout = timeout
        self.sock = None
        self.file = None
        self.closed = True

    def connect(self):
        try:
            raw_socket = socket.create_connection(
                (self.server, self.port),
                timeout=self.timeout
            )

            if self.use_ssl:
                context = ssl.create_default_context()
                self.sock = context.wrap_socket(
                    raw_socket,
                    server_hostname=self.server
                )
            else:
                self.sock = raw_socket

            self.file = self.sock.makefile("rwb")

            response = self._readline()
            if not response.startswith(b"+OK"):
                raise Pop3ProtocolError(f"Banner inválido: {response!r}")
            self.closed = False
        except (socket.timeout, socket.gaierror, ConnectionRefusedError, ssl.SSLError) as e:
            raise Pop3ConnectionError(f"Error de conexión POP3: {e}") from e
        except Pop3ProtocolError:
            raise
        except Exception as e:
            raise Pop3ConnectionError(f"Error conectando: {e}") from e

    def login(self, user: str, password: str):
        self._require_open()
        self._send_cmd(f"USER {user}")
        resp = self._readline()
        if not resp.startswith(b"+OK"):
            raise Pop3AuthenticationError("Usuario rechazado")

        self._send_cmd(f"PASS {password}")
        resp = self._readline()
        if not resp.startswith(b"+OK"):
            raise Pop3AuthenticationError("Contraseña incorrecta o acceso bloqueado")


# cantidad correo
    def stat(self):
        self._require_open()
        self._send_cmd("STAT")
        resp = self._readline()
        if not resp.startswith(b"+OK"):
            raise Pop3ProtocolError("Error en comando STAT")

        parts = resp.decode(errors="replace").split()
        cantidad = int(parts[1])
        tam = int(parts[2])
        return cantidad, tam

# listar correos
    def list_messages(self):
        self._require_open()
        self._send_cmd("LIST")
        resp = self._readline()
        if not resp.startswith(b"+OK"):
            raise Pop3ProtocolError("Error en comando LIST")

        lines = self._read_multiline()
        mensajes = []
        for ln in lines:
            msg_id, size = ln.decode(errors="replace").split()
            mensajes.append((int(msg_id), int(size)))
        return mensajes
    
    def top(self, msg_id: int, n_lines: int = 0) -> bytes:
        self._require_open()
        try:
            self._send_cmd(f"TOP {msg_id} {n_lines}")
            resp = self._readline()
            if not resp.startswith(b"+OK"):
                raise Pop3ProtocolError(f"Error TOP {msg_id}")
            lines = self._read_multiline()
            return b"".join(lines)
        except Pop3ProtocolError:
            raise
        except Exception as e:
            raise MessageFetchError(f"Fallo en TOP {msg_id}: {e}") from e

    def retr(self, msg_id: int) -> bytes:
        self._require_open()
        try:
            self._send_cmd(f"RETR {msg_id}")
            resp = self._readline()
            if not resp.startswith(b"+OK"):
                raise Pop3ProtocolError(f"Error RETR {msg_id}")
            lines = self._read_multiline()
            return b"".join(lines)
        except Pop3ProtocolError:
            raise
        except Exception as e:
            raise MessageFetchError(f"Fallo en RETR {msg_id}: {e}") from e

# cerrar sesion
    def quit(self):
        if self.closed:
            return
        try:
            self._send_cmd("QUIT")
            _ = self._readline()
        finally:
            self.closed = True
            try:
                if self.file:
                    self.file.close()
            finally:
                if self.sock:
                    self.sock.close()

    def _send_cmd(self, cmd: str):
        if not self.file:
            raise Pop3SessionClosedError("Sesión POP3 no inicializada.")
        self.file.write((cmd + "\r\n").encode("utf-8"))
        self.file.flush()

    def _readline(self) -> bytes:
        if not self.file:
            raise Pop3SessionClosedError("Sesión POP3 no inicializada.")
        line = self.file.readline()
        if not line:
            raise Pop3ConnectionError("Conexión cerrada por el servidor.")
        return line
    
    def _read_multiline(self) -> list[bytes]:
        out: list[bytes] = []
        while True:
            line = self._readline()
            if line == b".\r\n":
                break
            if line.startswith(b".."):
                line = line[1:]
            out.append(line)
        return out

    def _require_open(self):
        if self.closed or not self.sock or not self.file:
            raise Pop3SessionClosedError("Sesión POP3 cerrada.")