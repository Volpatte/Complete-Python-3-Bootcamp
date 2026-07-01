"""Hash de senha e helpers de autenticação.

Usa PBKDF2-HMAC-SHA256 da biblioteca padrão (sem dependências extras).
Em produção pode-se trocar por bcrypt/argon2 mantendo a mesma interface.
"""

from __future__ import annotations

import hashlib
import hmac
import os
import secrets
import string

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import Usuario

_ITERACOES = 200_000


def senha_temporaria(n: int = 8) -> str:
    """Gera uma senha inicial/temporária legível (letras + dígitos)."""
    alfabeto = string.ascii_letters + string.digits
    return "".join(secrets.choice(alfabeto) for _ in range(n))


def hash_senha(senha: str, salt: str | None = None) -> str:
    salt = salt or os.urandom(16).hex()
    dk = hashlib.pbkdf2_hmac("sha256", senha.encode(), bytes.fromhex(salt), _ITERACOES).hex()
    return f"{salt}${dk}"


def verificar_senha(senha: str, armazenado: str) -> bool:
    try:
        salt, dk = armazenado.split("$", 1)
    except ValueError:
        return False
    calc = hashlib.pbkdf2_hmac("sha256", senha.encode(), bytes.fromhex(salt), _ITERACOES).hex()
    return hmac.compare_digest(calc, dk)


def autenticar(db: Session, email: str, senha: str) -> Usuario | None:
    user = db.scalar(select(Usuario).where(Usuario.email == email.strip().lower()))
    if user and user.ativo and verificar_senha(senha, user.senha_hash):
        return user
    return None
