"""Testes das 5 APIs de Plano de Contas e das regras de negócio."""
from conftest import dados_conta
from database.conexao import executar


def test_get_all_lista_somente_ativos(client, headers, plano):
    r = client.get("/api/plano-contas", headers=headers)
    assert r.status_code == 200
    ids = [p["id"] for p in r.get_json()]
    assert plano["id"] in ids


def test_get_by_id(client, headers, plano):
    r = client.get(f"/api/plano-contas/{plano['id']}", headers=headers)
    assert r.status_code == 200
    assert r.get_json()["codigo"] == plano["codigo"]


def test_get_by_id_inexistente_retorna_404(client, headers):
    assert client.get("/api/plano-contas/999999", headers=headers).status_code == 404


def test_insert_retorna_201_e_campos(client, headers, plano):
    assert plano["id"] > 0
    assert plano["removido"] is False


def test_insert_sem_nome_retorna_400(client, headers):
    r = client.post("/api/plano-contas", json={"codigo": "X-1", "nome": " "}, headers=headers)
    assert r.status_code == 400


def test_insert_codigo_duplicado_retorna_409(client, headers, plano):
    r = client.post(
        "/api/plano-contas", json={"codigo": plano["codigo"], "nome": "Outro"}, headers=headers
    )
    assert r.status_code == 409


def test_update(client, headers, plano):
    r = client.put(
        f"/api/plano-contas/{plano['id']}",
        json={"codigo": plano["codigo"], "nome": "Nome alterado"},
        headers=headers,
    )
    assert r.status_code == 200
    assert r.get_json()["nome"] == "Nome alterado"


def test_update_inexistente_retorna_404(client, headers):
    r = client.put(
        "/api/plano-contas/999999", json={"codigo": "Z-9", "nome": "x"}, headers=headers
    )
    assert r.status_code == 404


def test_delete_e_soft_delete(client, headers, plano):
    r = client.delete(f"/api/plano-contas/{plano['id']}", headers=headers)
    assert r.status_code == 200

    # some das consultas...
    assert client.get(f"/api/plano-contas/{plano['id']}", headers=headers).status_code == 404
    ids = [p["id"] for p in client.get("/api/plano-contas", headers=headers).get_json()]
    assert plano["id"] not in ids

    # ...mas continua fisicamente na tabela, com removido = TRUE
    linha = executar("SELECT removido FROM plano_contas WHERE id = %s", (plano["id"],), "um")
    assert linha["removido"] is True


def test_delete_inexistente_retorna_404(client, headers):
    assert client.delete("/api/plano-contas/999999", headers=headers).status_code == 404


def test_delete_plano_com_conta_ativa_retorna_409(client, headers, plano):
    client.post("/api/contas-pagar", json=dados_conta(plano["id"]), headers=headers)
    r = client.delete(f"/api/plano-contas/{plano['id']}", headers=headers)
    assert r.status_code == 409
