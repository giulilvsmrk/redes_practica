#src/main.py
from __future__ import annotations

import getpass
from pop3_server import POP3Client
from email_parser import parse_email
from errors import Pop3SecureClientError

from email import policy
from email.parser import BytesParser
from attachment_filter import export_blocked_attachment
from file_opener import open_file

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

                # Mostrar adjuntos bloqueados (si existen)
                if info["blocked_attachments"]:
                    print("\n[Adjuntos bloqueados]")
                    for b in info["blocked_attachments"]:
                        print(f"- part#{b.index} | {b.content_type} | {b.filename} | {b.disposition}")

                    # Submenú: recuperar/exportar bajo demanda
                    msg = BytesParser(policy=policy.default).parsebytes(raw)
                    exported_paths: dict[int, str] = {}

                    while True:
                        print("\nOpciones de adjuntos:")
                        print("1 - Abrir/exportar adjunto por ID")
                        print("2 - Ver adjuntos exportados en esta sesión")
                        print("3 - Borrar un adjunto exportado (por ID)")
                        print("0 - Volver al menú principal")

                        aop = input("Opción: ").strip()

                        if aop == "1":
                            try:
                                blocked_ids = {b.index for b in info["blocked_attachments"]}
                                aid = int(input("Ingrese ID (part#): ").strip())
                                if aid not in blocked_ids:
                                    print("Ese ID no corresponde a un adjunto bloqueado. Usa uno de la lista.")
                                    continue
                                path = export_blocked_attachment(msg, aid)
                                exported_paths[aid] = path
                                print(f"[OK] Exportado en: {path}")
                                print("[*] Abriendo archivo...")
                                open_file(path)
                            except Exception as e:
                                print("[ERROR adjunto]", e)

                        elif aop == "2":
                            if not exported_paths:
                                print("(No hay adjuntos exportados aún)")
                            else:
                                for k, v in exported_paths.items():
                                    print(f"- part#{k} -> {v}")

                        elif aop == "3":
                            try:
                                aid = int(input("ID (part#) a borrar: ").strip())
                                path = exported_paths.get(aid)
                                if not path:
                                    print("Ese ID no fue exportado en esta sesión.")
                                    continue
                                import os
                                os.remove(path)
                                del exported_paths[aid]
                                print("[OK] Borrado.")
                            except Exception as e:
                                print("[ERROR borrando]", e)

                        elif aop == "0":
                            break
                        else:
                            print("Opción inválida.")

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