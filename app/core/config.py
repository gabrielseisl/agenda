"""Configuração central do projeto (valores vêm do arquivo .env)."""
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

RAIZ = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    app_name: str = "Meu Dia"
    app_env: str = "development"

    db_host: str = "localhost"
    db_port: int = 3306
    db_name: str = "agenda"
    db_user: str = "root"
    db_password: str = ""

    # Chave usada para assinar o cookie de login. Troque no .env.
    secret_key: str = "troque-esta-chave-no-arquivo-env"
    # Quantas horas o login continua valendo.
    token_horas: int = 24 * 7

    model_config = SettingsConfigDict(
        env_file=RAIZ / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
