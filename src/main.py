from pop3_server import POP3Client
import getpass

def main():
    SERVER = "localhost"
    PORT = 110
    USE_SSL = False

    USER = input("Usuario: ")
    PASSWORD = getpass.getpass("Contraseña: ")

    client = POP3Client(SERVER, PORT, USE_SSL)

    try:
        print("[*] Conectando al servidor POP3...")
        client.connect()

        print("[*] Iniciando sesión...")
        client.login(USER, PASSWORD)

        while True:
            print("\nSeleccione una opción:")
            print("1 - Mostrar cantidad de correos")
            print("2 - Listar correos")
            print("0 - Cerrar sesión")

            opcion = input("Opción: ")

            if opcion == "1":
                print("\n[STAT]")
                client.stat()

            elif opcion == "2":
                print("\n[LIST]")
                client.list_messages()

            elif opcion == "0":
                print("\nCerrando sesión...")
                break

            else:
                print("Opción inválida")

    except Exception as e:
        print("[ERROR]", e)

    finally:
        client.quit()

if __name__ == "__main__":
    main()