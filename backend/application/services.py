from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import jwt
from werkzeug.security import check_password_hash

from backend.infrastructure.supabase_repository import SupabaseRepository


class AuthService:
    def __init__(self, repo: SupabaseRepository):
        self.repo = repo

    def login(self, email: str, password: str) -> Optional[dict[str, Any]]:
        usuario = self.repo.buscar_usuario_por_email(email)
        if not usuario or not usuario.get("activo", True):
            return None
        try:
            return usuario if check_password_hash(usuario["password_hash"], password) else None
        except (KeyError, ValueError):
            return None

    @staticmethod
    def generar_token(usuario: dict[str, Any], secret: str) -> str:
        now = datetime.now(timezone.utc)
        return jwt.encode(
            {
                "sub": str(usuario["id"]),
                "email": usuario["email"],
                "rol": usuario["rol"],
                "iat": now,
                "exp": now + timedelta(hours=8),
            },
            secret,
            algorithm="HS256",
        )
