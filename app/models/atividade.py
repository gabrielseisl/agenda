from datetime import date, datetime, time

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Time, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.connection import Base


class Atividade(Base):
    __tablename__ = "atividades"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    usuario_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id", ondelete="CASCADE"), index=True
    )
    titulo: Mapped[str] = mapped_column(String(150))
    data: Mapped[date] = mapped_column(Date, index=True)
    horario: Mapped[time | None] = mapped_column(Time, nullable=True)
    duracao_min: Mapped[int] = mapped_column(Integer, default=30)
    prioridade: Mapped[str] = mapped_column(String(10), default="media")
    concluida: Mapped[bool] = mapped_column(Boolean, default=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
