"""As 5 funções do front-end para Plano de Contas.
Cada função usa UMA API do back-end."""
from apps.api_client import requisicao


def get_all_plano_contas():
    return requisicao("GET", "/plano-contas")


def get_plano_conta_by_id(id):
    return requisicao("GET", f"/plano-contas/{id}")


def insert_plano_conta(plano):
    return requisicao("POST", "/plano-contas", plano)


def update_plano_conta(id, plano):
    return requisicao("PUT", f"/plano-contas/{id}", plano)


def delete_plano_conta(id):
    return requisicao("DELETE", f"/plano-contas/{id}")
