from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.seguranca import COOKIE_SESSAO, ler_token
from app.database.connection import get_db
from app.models.usuario import Usuario


def usuario_atual(request: Request, db: Session = Depends(get_db)) -> Usuario:
    """Exige login: devolve o usuário do cookie ou responde 401."""
    usuario_id = ler_token(request.cookies.get(COOKIE_SESSAO, ""))
    usuario = db.get(Usuario, usuario_id) if usuario_id else None
    if usuario is None:
        raise HTTPException(status_code=401, detail="Sessão expirada. Entre novamente.")
    return usuario
