from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, Response
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import SQLAlchemyError

from app import models  # noqa: F401  (registra as tabelas)
from app.core.config import settings
from app.core.seguranca import COOKIE_SESSAO, ler_token
from app.database.connection import Base, engine
from app.routes import atividades, auth, health

STATIC_DIR = Path(__file__).parent / "static"
SEM_CACHE = {"Cache-Control": "no-store"}


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Cria as tabelas que ainda não existem (o database 'agenda' já deve existir).
    try:
        Base.metadata.create_all(bind=engine)
    except SQLAlchemyError as erro:
        primeira_linha = str(erro).splitlines()[0]
        print(f"\n[AVISO] Não foi possível acessar o MySQL: {primeira_linha}")
        print("Confira o .env, se o MySQL está ligado e se o database existe.\n")
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(atividades.router)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


def _logado(request: Request) -> bool:
    return ler_token(request.cookies.get(COOKIE_SESSAO, "")) is not None


@app.get("/", include_in_schema=False)
def pagina_inicial(request: Request):
    if not _logado(request):
        return RedirectResponse("/login")
    return FileResponse(STATIC_DIR / "index.html", headers=SEM_CACHE)


@app.get("/login", include_in_schema=False)
def pagina_login(resposta: Response):
    # A rota de login nunca redireciona para a agenda por causa de um cookie antigo.
    resposta.delete_cookie(COOKIE_SESSAO, path="/")
    return FileResponse(STATIC_DIR / "login.html", headers=SEM_CACHE)
