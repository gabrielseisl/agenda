from datetime import date, time
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AtividadeIn(BaseModel):
    titulo: str = Field(min_length=1, max_length=150)
    data: date
    horario: time | None = None
    duracao_min: int = Field(default=30, ge=1, le=1440)
    prioridade: Literal["alta", "media", "baixa"] = "media"

    @field_validator("titulo")
    @classmethod
    def limpar_titulo(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("O título não pode ficar vazio.")
        return v


class AtividadeOut(AtividadeIn):
    model_config = ConfigDict(from_attributes=True)

    id: int
    concluida: bool
