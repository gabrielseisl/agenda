from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.dependencias import usuario_atual
from app.database.connection import get_db
from app.models.atividade import Atividade
from app.models.usuario import Usuario
from app.schemas.atividade import AtividadeIn, AtividadeOut

router = APIRouter(prefix="/api/atividades", tags=["Atividades"])

ORDEM_PRIORIDADE = {"alta": 0, "media": 1, "baixa": 2}


def _buscar(db: Session, atividade_id: int, usuario: Usuario) -> Atividade:
    atividade = db.get(Atividade, atividade_id)
    # Atividade de outro usuário aparece como "não encontrada".
    if atividade is None or atividade.usuario_id != usuario.id:
        raise HTTPException(status_code=404, detail="Atividade não encontrada.")
    return atividade


@router.get("", response_model=list[AtividadeOut])
def listar(
    data: date,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(usuario_atual),
):
    """Lista as atividades do dia do usuário logado."""
    itens = db.scalars(
        select(Atividade).where(Atividade.usuario_id == usuario.id, Atividade.data == data)
    ).all()
    return sorted(
        itens,
        key=lambda a: (
            a.horario is None,
            a.horario or 0,
            ORDEM_PRIORIDADE.get(a.prioridade, 9),
            a.id,
        ),
    )


@router.post("", response_model=AtividadeOut, status_code=201)
def criar(
    dados: AtividadeIn,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(usuario_atual),
):
    atividade = Atividade(**dados.model_dump(), usuario_id=usuario.id)
    db.add(atividade)
    db.commit()
    db.refresh(atividade)
    return atividade


@router.put("/{atividade_id}", response_model=AtividadeOut)
def atualizar(
    atividade_id: int,
    dados: AtividadeIn,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(usuario_atual),
):
    atividade = _buscar(db, atividade_id, usuario)
    for campo, valor in dados.model_dump().items():
        setattr(atividade, campo, valor)
    db.commit()
    db.refresh(atividade)
    return atividade


@router.patch("/{atividade_id}/concluir", response_model=AtividadeOut)
def alternar_conclusao(
    atividade_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(usuario_atual),
):
    atividade = _buscar(db, atividade_id, usuario)
    atividade.concluida = not atividade.concluida
    db.commit()
    db.refresh(atividade)
    return atividade


@router.delete("/{atividade_id}", status_code=204)
def excluir(
    atividade_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(usuario_atual),
):
    atividade = _buscar(db, atividade_id, usuario)
    db.delete(atividade)
    db.commit()
    return Response(status_code=204)
