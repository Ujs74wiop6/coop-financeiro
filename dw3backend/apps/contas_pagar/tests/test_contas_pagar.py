"""Testes das 5 APIs de Contas a Pagar e das validações."""
import pytest

from conftest import dados_conta
from database.conexao import executar


@pytest.fixture
def conta(client, headers, plano):
    r = client.post("/api/contas-pagar", json=dados_conta(plano["id"]), headers=headers)
    return r.get_json()


def test_insert_retorna_201_com_tipos_corretos(client, headers, plano, conta):
    assert conta["id"] > 0
    assert conta["valor"] == 150.75           # decimal
    assert conta["data_vencimento"] == "2026-12-31"  # data em ISO
    assert conta["descricao"] == "Conta de teste"    # texto
    assert conta["plano_conta_id"] == plano["id"]


def test_get_all_inclui_a_conta(client, headers, conta):
    r = client.get("/api/contas-pagar", headers=headers)
    assert r.status_code == 200
    assert conta["id"] in [c["id"] for c in r.get_json()]


def test_get_by_id(client, headers, conta):
    r = client.get(f"/api/contas-pagar/{conta['id']}", headers=headers)
    assert r.status_code == 200
    assert r.get_json()["id"] == conta["id"]


def test_get_by_id_inexistente_retorna_404(client, headers):
    assert client.get("/api/contas-pagar/999999", headers=headers).status_code == 404


def test_update(client, headers, plano, conta):
    novos = dados_conta(plano["id"], descricao="Alterada", valor="200.00", pago=True)
    r = client.put(f"/api/contas-pagar/{conta['id']}", json=novos, headers=headers)
    assert r.status_code == 200
    corpo = r.get_json()
    assert corpo["descricao"] == "Alterada"
    assert corpo["valor"] == 200.0
    assert corpo["pago"] is True


def test_update_inexistente_retorna_404(client, headers, plano):
    r = client.put("/api/contas-pagar/999999", json=dados_conta(plano["id"]), headers=headers)
    assert r.status_code == 404


def test_delete_e_soft_delete(client, headers, conta):
    assert client.delete(f"/api/contas-pagar/{conta['id']}", headers=headers).status_code == 200
    assert client.get(f"/api/contas-pagar/{conta['id']}", headers=headers).status_code == 404
    ids = [c["id"] for c in client.get("/api/contas-pagar", headers=headers).get_json()]
    assert conta["id"] not in ids

    linha = executar("SELECT removido FROM contas_pagar WHERE id = %s", (conta["id"],), "um")
    assert linha["removido"] is True


def test_delete_duas_vezes_retorna_404_na_segunda(client, headers, conta):
    client.delete(f"/api/contas-pagar/{conta['id']}", headers=headers)
    assert client.delete(f"/api/contas-pagar/{conta['id']}", headers=headers).status_code == 404


def test_apos_remover_a_conta_o_plano_pode_ser_removido(client, headers, plano, conta):
    client.delete(f"/api/contas-pagar/{conta['id']}", headers=headers)
    assert client.delete(f"/api/plano-contas/{plano['id']}", headers=headers).status_code == 200


@pytest.mark.parametrize(
    "campo, valor_invalido",
    [
        ("descricao", "   "),
        ("valor", "0"),
        ("valor", "-10"),
        ("valor", "abc"),
        ("valor", "NaN"),
        ("data_vencimento", "31/12/2026"),
        ("data_vencimento", ""),
        ("plano_conta_id", 999999),
        ("plano_conta_id", None),
    ],
)
def test_insert_com_dado_invalido_retorna_400(client, headers, plano, campo, valor_invalido):
    corpo = dados_conta(plano["id"], **{campo: valor_invalido})
    r = client.post("/api/contas-pagar", json=corpo, headers=headers)
    assert r.status_code == 400
    assert "erro" in r.get_json()
