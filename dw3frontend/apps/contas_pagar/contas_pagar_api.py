"""As 5 funções do front-end para Contas a Pagar.
Cada função usa UMA API do back-end."""
from apps.api_client import requisicao


def get_all_contas_pagar():
    return requisicao("GET", "/contas-pagar")


def get_conta_pagar_by_id(id):
    return requisicao("GET", f"/contas-pagar/{id}")


def insert_conta_pagar(conta):
    return requisicao("POST", "/contas-pagar", conta)


def update_conta_pagar(id, conta):
    return requisicao("PUT", f"/contas-pagar/{id}", conta)


def delete_conta_pagar(id):
    return requisicao("DELETE", f"/contas-pagar/{id}")
