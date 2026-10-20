"""Itens compartilhados pelos testes (o pytest carrega este arquivo sozinho).

Os testes são de integração: usam a API de verdade e o PostgreSQL de verdade.
Rode com o banco no ar (ex.: `docker compose up -d db`) ou dentro do container:
    docker compose exec backend pytest -v
"""
import os
import uuid

import pytest
from dotenv import load_dotenv

load_dotenv()

from app import app  # noqa: E402
from apps.login.controller import login_controller  # noqa: E402
from database.conexao import executar  # noqa: E402


@pytest.fixture(scope="session")
def client():
    """Cliente HTTP de teste: chama as rotas sem precisar subir o servidor."""
    login_controller.criar_admin_se_nao_existir()
    app.config["TESTING"] = True
    return app.test_client()


@pytest.fixture(scope="session")
def headers(client):
    """Cabeçalho com um JWT válido, obtido pelo login de verdade."""
    resposta = client.post(
        "/api/login",
        json={
            "usuario": os.getenv("ADMIN_USUARIO", "admin"),
            "senha": os.getenv("ADMIN_SENHA", "admin123"),
        },
    )
    return {"Authorization": "Bearer " + resposta.get_json()["token"]}


@pytest.fixture
def plano(client, headers):
    """Cria um plano de contas só para o teste e apaga (de verdade) no final."""
    codigo = "T-" + uuid.uuid4().hex[:8]
    criado = client.post(
        "/api/plano-contas", json={"codigo": codigo, "nome": "Plano de teste"}, headers=headers
    ).get_json()
    yield criado
    executar("DELETE FROM contas_pagar WHERE plano_conta_id = %s", (criado["id"],), "nada")
    executar("DELETE FROM plano_contas WHERE id = %s", (criado["id"],), "nada")


def dados_conta(plano_id, **alteracoes):
    """Corpo válido de uma conta a pagar; os testes trocam só o campo que querem."""
    dados = {
        "descricao": "Conta de teste",
        "valor": "150.75",
        "data_vencimento": "2026-12-31",
        "pago": False,
        "plano_conta_id": plano_id,
    }
    dados.update(alteracoes)
    return dados
