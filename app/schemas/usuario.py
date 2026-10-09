import re

from pydantic import BaseModel, ConfigDict, Field, field_validator

_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _limpar_email(v: str) -> str:
    v = v.strip().lower()
    if not _EMAIL.match(v):
        raise ValueError("Informe um e-mail válido.")
    return v


class RegistroIn(BaseModel):
    nome: str = Field(min_length=2, max_length=100)
    email: str = Field(max_length=150)
    senha: str = Field(min_length=6, max_length=128)

    @field_validator("nome")
    @classmethod
    def limpar_nome(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Informe seu nome.")
        return v

    @field_validator("email")
    @classmethod
    def validar_email(cls, v: str) -> str:
        return _limpar_email(v)


class LoginIn(BaseModel):
    email: str = Field(max_length=150)
    senha: str = Field(max_length=128)

    @field_validator("email")
    @classmethod
    def normalizar_email(cls, v: str) -> str:
        return v.strip().lower()


class UsuarioOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    email: str
