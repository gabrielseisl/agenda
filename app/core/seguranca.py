"""Senhas e tokens de login (somente biblioteca padrão do Python)."""
import hashlib
import hmac
import secrets
import time

from app.core.config import settings

COOKIE_SESSAO = "meudia_sessao"
_ITERACOES = 200_000

# Segredo temporário por processo: tokens anteriores deixam de valer quando
# o servidor Python reinicia, sem alterar os usuários nem os dados no banco.
_SEGREDO_PROCESSO = secrets.token_hex(32)


def hash_senha(senha: str) -> str:
    sal = secrets.token_hex(16)
    h = hashlib.pbkdf2_hmac("sha256", senha.encode(), bytes.fromhex(sal), _ITERACOES)
    return f"pbkdf2_sha256${_ITERACOES}${sal}${h.hex()}"


def verificar_senha(senha: str, armazenado: str) -> bool:
    try:
        _, iteracoes, sal, esperado = armazenado.split("$")
        h = hashlib.pbkdf2_hmac("sha256", senha.encode(), bytes.fromhex(sal), int(iteracoes))
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(h.hex(), esperado)


def _assinar(corpo: str) -> str:
    chave = f"{settings.secret_key}:{_SEGREDO_PROCESSO}".encode()
    return hmac.new(chave, corpo.encode(), hashlib.sha256).hexdigest()


def criar_token(usuario_id: int) -> str:
    expira = int(time.time()) + settings.token_horas * 3600
    corpo = f"{usuario_id}.{expira}"
    return f"{corpo}.{_assinar(corpo)}"


def ler_token(token: str) -> int | None:
    """Devolve o id do usuário se o token for válido e não tiver expirado."""
    try:
        usuario_id, expira, assinatura = token.split(".")
        if not hmac.compare_digest(_assinar(f"{usuario_id}.{expira}"), assinatura):
            return None
        if int(expira) < time.time():
            return None
        return int(usuario_id)
    except (ValueError, AttributeError):
        return None
