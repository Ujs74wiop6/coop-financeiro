"""Testes do login e da proteção JWT."""
import os
from datetime import datetime, timedelta, timezone

import jwt


def test_login_com_senha_errada_retorna_401(client):
    r = client.post("/api/login", json={"usuario": "admin", "senha": "senha-errada"})
    assert r.status_code == 401
    assert "inválidos" in r.get_json()["erro"]


def test_login_com_usuario_inexistente_retorna_401(client):
    r = client.post("/api/login", json={"usuario": "ninguem", "senha": "x"})
    assert r.status_code == 401


def test_login_correto_devolve_token(client, headers):
    # `headers` já fez o login; aqui conferimos o formato do cabeçalho
    assert headers["Authorization"].startswith("Bearer ")
    assert len(headers["Authorization"]) > 40


def test_rota_protegida_sem_token_retorna_401(client):
    assert client.get("/api/plano-contas").status_code == 401
    assert client.get("/api/contas-pagar").status_code == 401


def test_rota_protegida_com_token_invalido_retorna_401(client):
    r = client.get("/api/plano-contas", headers={"Authorization": "Bearer lixo"})
    assert r.status_code == 401


def test_rota_protegida_com_token_expirado_retorna_401(client):
    expirado = jwt.encode(
        {"sub": "admin", "exp": datetime.now(timezone.utc) - timedelta(minutes=1)},
        os.getenv("JWT_SECRET", "dev-secret-so-para-desenvolvimento-local-0123456789"),
        algorithm="HS256",
    )
    r = client.get("/api/plano-contas", headers={"Authorization": "Bearer " + expirado})
    assert r.status_code == 401
    assert "expirado" in r.get_json()["erro"].lower()


def test_token_assinado_com_outra_chave_e_recusado(client):
    falso = jwt.encode(
        {"sub": "admin", "exp": datetime.now(timezone.utc) + timedelta(minutes=5)},
        "chave-do-atacante-com-mais-de-32-caracteres!",
        algorithm="HS256",
    )
    r = client.get("/api/plano-contas", headers={"Authorization": "Bearer " + falso})
    assert r.status_code == 401
