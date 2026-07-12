"""Create the first CurrierMsj administrator without exposing a public endpoint."""
import argparse
import getpass

from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

from backend.infrastructure.supabase_repository import get_repo


def validate_password(password: str) -> None:
    if len(password) < 12:
        raise ValueError("La contrasena debe tener al menos 12 caracteres")


def main() -> None:
    parser = argparse.ArgumentParser(description="Crear el administrador inicial")
    parser.add_argument("--email", required=True)
    parser.add_argument("--name", required=True)
    args = parser.parse_args()

    load_dotenv()
    email = args.email.strip().lower()
    if "@" not in email:
        raise SystemExit("Email invalido")
    if get_repo().buscar_usuario_por_email(email):
        raise SystemExit("Ya existe un usuario con ese email")

    password = getpass.getpass("Contrasena (minimo 12 caracteres): ")
    confirmation = getpass.getpass("Repite la contrasena: ")
    if password != confirmation:
        raise SystemExit("Las contrasenas no coinciden")
    try:
        validate_password(password)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc

    result = get_repo().client.table("usuarios").insert({
        "email": email,
        "password_hash": generate_password_hash(password),
        "nombre": args.name.strip(),
        "rol": "admin",
        "activo": True,
    }).execute()
    if not result.data:
        raise SystemExit("Supabase no devolvio el usuario creado")
    print(f"Administrador creado: {email}")


if __name__ == "__main__":
    main()
