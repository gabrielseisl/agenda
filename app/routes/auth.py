from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.dependencias import usuario_atual
from app.core.seguranca import (
    COOKIE_SESSAO,
    criar_token,
    hash_senha,
    verificar_senha,
)
from app.database.connection import get_db
from app.models.usuario import Usuario
from app.schemas.usuario import LoginIn, RegistroIn, UsuarioOut

router = APIRouter(prefix="/api/auth", tags=["Autenticação"])


def _iniciar_sessao(resposta: Response, usuario_id: int) -> None:
    # Sem max_age: é um cookie de sessão e some quando o navegador é fechado.
    resposta.set_cookie(
        COOKIE_SESSAO,
        criar_token(usuario_id),
        httponly=True,
        samesite="lax",
        path="/",
    )


@router.post("/registrar", response_model=UsuarioOut, status_code=201)
def registrar(dados: RegistroIn, resposta: Response, db: Session = Depends(get_db)):
    if db.scalar(select(Usuario).where(Usuario.email == dados.email)):
        raise HTTPException(status_code=409, detail="Já existe uma conta com este e-mail.")
    usuario = Usuario(nome=dados.nome, email=dados.email, senha_hash=hash_senha(dados.senha))
    db.add(usuario)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Já existe uma conta com este e-mail.")
    db.refresh(usuario)
    _iniciar_sessao(resposta, usuario.id)
    return usuario


@router.post("/entrar", response_model=UsuarioOut)
def entrar(dados: LoginIn, resposta: Response, db: Session = Depends(get_db)):
    usuario = db.scalar(select(Usuario).where(Usuario.email == dados.email))
    if usuario is None or not verificar_senha(dados.senha, usuario.senha_hash):
        raise HTTPException(status_code=401, detail="E-mail ou senha incorretos.")
    _iniciar_sessao(resposta, usuario.id)
    return usuario


@router.post("/sair")
def sair(resposta: Response):
    resposta.delete_cookie(COOKIE_SESSAO, path="/")
    return {"ok": True}


@router.get("/eu", response_model=UsuarioOut)
def quem_sou_eu(usuario: Usuario = Depends(usuario_atual)):
    return usuario
