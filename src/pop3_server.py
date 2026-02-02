import socket
import ssl


class POP3Client:

    def __init__(self, server, port=110, use_ssl=False, timeout=10):
        self.server = server
        self.port = port
        self.use_ssl = use_ssl
        self.timeout = timeout
        self.sock = None
        self.file = None

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
                raise Exception("El servidor no respondió con +OK")

        except Exception as e:
            raise Exception(f"Error de conexión POP3: {e}")

    def login(self, user, password):
        self._send_cmd(f"USER {user}")
        resp = self._readline()
        if not resp.startswith(b"+OK"):
            raise Exception("Usuario rechazado")

        self._send_cmd(f"PASS {password}")
        resp = self._readline()
        if not resp.startswith(b"+OK"):
            raise Exception("Contraseña incorrecta")

# cantidad correo
    def stat(self):
        self._send_cmd("STAT")
        resp = self._readline()

        if not resp.startswith(b"+OK"):
            raise Exception("Error en comando STAT")
        
        print(resp.decode().strip())

        parts = resp.decode().split()
        cantidad = int(parts[1])
        tamaño = int(parts[2])

        return cantidad, tamaño

# listar correos
    def list_messages(self):
        self._send_cmd("LIST")
        resp = self._readline()

        if not resp.startswith(b"+OK"):
            raise Exception("Error en comando LIST")
        
        print(resp.decode().strip())
        mensajes = []

        while True:
            line = self._readline()
            if line == b".\r\n":
                break

            print(line.decode().strip())
            msg_id, size = line.decode().split()
            mensajes.append((int(msg_id), int(size)))

        return mensajes
# cerrar sesion
    def quit(self):
        try:
            self._send_cmd("QUIT")
            self._readline()
        finally:
            if self.file:
                self.file.close()
            if self.sock:
                self.sock.close()

    def _send_cmd(self, cmd):
        self.file.write((cmd + "\r\n").encode("utf-8"))
        self.file.flush()

    def _readline(self):
        return self.file.readline()
