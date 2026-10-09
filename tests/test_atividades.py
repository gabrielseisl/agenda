from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import models  # noqa: F401
from app.database.connection import Base, get_db
from app.main import app

# Banco SQLite em memória: os testes não dependem do MySQL.
engine_teste = create_engine(
    "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
)
Base.metadata.create_all(engine_teste)
SessionTeste = sessionmaker(bind=engine_teste, autoflush=False, autocommit=False)


def _db_teste():
    db = SessionTeste()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = _db_teste


def _cliente_logado(email: str, nome: str = "Teste") -> TestClient:
    c = TestClient(app)
    r = c.post("/api/auth/registrar", json={"nome": nome, "email": email, "senha": "segredo123"})
    assert r.status_code == 201
    return c


def test_exige_login():
    c = TestClient(app)
    assert c.get("/api/atividades", params={"data": "2026-10-08"}).status_code == 401
    assert c.get("/", follow_redirects=False).headers["location"] == "/login"
    assert c.get("/login").status_code == 200


def test_cadastro_login_e_sair():
    c = _cliente_logado("Ana@Exemplo.com", "Ana")
    assert c.get("/api/auth/eu").json()["email"] == "ana@exemplo.com"

    # e-mail repetido (mesmo com maiúsculas) é recusado
    r = TestClient(app).post(
        "/api/auth/registrar", json={"nome": "Outra", "email": "ana@exemplo.com", "senha": "segredo123"}
    )
    assert r.status_code == 409

    c.post("/api/auth/sair")
    assert c.get("/api/auth/eu").status_code == 401

    errado = c.post("/api/auth/entrar", json={"email": "ana@exemplo.com", "senha": "errada"})
    assert errado.status_code == 401
    certo = c.post("/api/auth/entrar", json={"email": "ana@exemplo.com", "senha": "segredo123"})
    assert certo.status_code == 200
    assert c.get("/", follow_redirects=False).status_code == 200


def test_validacao_cadastro():
    c = TestClient(app)
    assert c.post("/api/auth/registrar", json={"nome": "A", "email": "x@y.com", "senha": "123456"}).status_code == 422
    assert c.post("/api/auth/registrar", json={"nome": "Bia", "email": "invalido", "senha": "123456"}).status_code == 422
    assert c.post("/api/auth/registrar", json={"nome": "Bia", "email": "b@y.com", "senha": "123"}).status_code == 422


def test_fluxo_completo_de_atividades():
    client = _cliente_logado("fluxo@exemplo.com")
    corpo = {"titulo": "Estudar Python", "data": "2026-10-08", "horario": "09:00",
             "duracao_min": 90, "prioridade": "alta"}
    r = client.post("/api/atividades", json=corpo)
    assert r.status_code == 201
    id_ = r.json()["id"]
    assert r.json()["concluida"] is False

    client.post("/api/atividades", json={"titulo": "Sem horário", "data": "2026-10-08"})
    lista = client.get("/api/atividades", params={"data": "2026-10-08"}).json()
    assert [a["titulo"] for a in lista] == ["Estudar Python", "Sem horário"]

    assert client.patch(f"/api/atividades/{id_}/concluir").json()["concluida"] is True

    corpo["titulo"] = "Estudar FastAPI"
    assert client.put(f"/api/atividades/{id_}", json=corpo).json()["titulo"] == "Estudar FastAPI"

    assert client.delete(f"/api/atividades/{id_}").status_code == 204
    assert client.delete(f"/api/atividades/{id_}").status_code == 404


def test_atividades_sao_separadas_por_usuario():
    a = _cliente_logado("a@exemplo.com")
    b = _cliente_logado("b@exemplo.com")
    id_a = a.post("/api/atividades", json={"titulo": "Só da A", "data": "2026-10-09"}).json()["id"]

    assert b.get("/api/atividades", params={"data": "2026-10-09"}).json() == []
    assert b.delete(f"/api/atividades/{id_a}").status_code == 404
    assert b.patch(f"/api/atividades/{id_a}/concluir").status_code == 404
    assert len(a.get("/api/atividades", params={"data": "2026-10-09"}).json()) == 1


def test_validacao_atividade():
    c = _cliente_logado("valida@exemplo.com")
    assert c.post("/api/atividades", json={"titulo": "   ", "data": "2026-10-08"}).status_code == 422


def test_arquivos_estaticos():
    c = TestClient(app)
    for caminho in ("app.js", "style.css", "login.js", "login.css"):
        assert c.get(f"/static/{caminho}").status_code == 200


def test_cookie_de_sessao_some_ao_fechar_navegador():
    r = TestClient(app).post(
        "/api/auth/registrar",
        json={"nome": "Cookie", "email": "cookie@exemplo.com", "senha": "segredo123"},
    )
    cookie = r.headers["set-cookie"].lower()
    assert "httponly" in cookie
    assert "max-age" not in cookie and "expires" not in cookie
    assert TestClient(app).get("/", follow_redirects=False).headers["cache-control"] == "no-store"
