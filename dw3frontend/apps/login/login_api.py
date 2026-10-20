"""Função do front-end que usa a API de login do back-end."""
from apps.api_client import requisicao


def fazer_login(usuario, senha):
    return requisicao("POST", "/login", {"usuario": usuario, "senha": senha})
