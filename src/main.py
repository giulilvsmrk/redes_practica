from __future__ import annotations

import getpass
from pop3_server import POP3Client
from email_parser import parse_email
from errors import Pop3SecureClientError

def main():

    SERVER = "localhost"
    PORT = 110
    USE_SSL = False
    

    user = input("Usuario: ").strip()
    password = getpass.getpass("Contraseña: ")

    client = POP3Client(SERVER, PORT, USE_SSL)

    try:
        print("[*] Conectando...")
        client.connect()

        print("[*] Login...")
        client.login(user, password)

        while True:
            print("\nOpciones:")
            print("1 - Mostrar cantidad (STAT)")
            print("2 - Listar Subjects (TOP 0)")
            print("3 - Ver cuerpo seguro de un correo (RETR + filtro)")
            print("0 - Salir (QUIT)")
            op = input("Opción: ").strip()

            if op == "1":
                count, size = client.stat()
                print(f"+OK {count} mensajes, {size} bytes total")

            elif op == "2":
                count, _ = client.stat()
                if count == 0:
                    print("(INBOX vacía)")
                    continue
                for i in range(1, count + 1):
                    headers_bytes = client.top(i, 0)  # solo headers
                    info = parse_email(headers_bytes)
                    print(f"{i:03d} | {info['subject'] or '(sin subject)'}")

            elif op == "3":
                idx = int(input("ID del correo (1..N): ").strip())
                raw = client.retr(idx)
                info = parse_email(raw)

                print("\n" + "=" * 70)
                print("Subject:", info["subject"])
                print("From   :", info["from"])
                print("Date   :", info["date"])
                print("-" * 70)
                body = info["body"] or "(sin cuerpo text/plain o bloqueado por seguridad)"
                print(body)
                if info["blocked_attachments"]:
                    print("\n[Adjuntos bloqueados]")
                    for b in info["blocked_attachments"]:
                        print(f"- part#{b.index} | {b.content_type} | {b.filename} | {b.disposition}")
                print("=" * 70)

            elif op == "0":
                break

            else:
                print("Opción inválida.")

    except Pop3SecureClientError as e:
        print("[ERROR]", e)
    finally:
        client.quit()
        print("[*] Sesión cerrada.")

if __name__ == "__main__":
    main()