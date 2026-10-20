"""Função base de comunicação com o back-end.

Toda chamada à API passa por `requisicao()`: ela monta o cabeçalho com o JWT,
faz o pedido HTTP (biblioteca `requests`) e traduz as respostas de erro em exceções.
"""
import os

import requests

from apps.login import sessao


class ErroApi(Exception):
    """A API respondeu com erro (ou está fora do ar). `status` é o código HTTP."""

    def __init__(self, mensagem, status=500):
        super().__init__(mensagem)
        self.mensagem = mensagem
        self.status = status


class SessaoExpirada(Exception):
    """A API recusou o token (ausente, inválido ou expirado)."""


def requisicao(metodo, caminho, corpo=None):
    url = os.getenv("BACKEND_URL", "http://localhost:5000/api") + caminho

    cabecalhos = {}
    token = sessao.obter_token()
    if token:
        cabecalhos["Authorization"] = "Bearer " + token  # é isto que a API valida

    try:
        resposta = requests.request(metodo, url, json=corpo, headers=cabecalhos, timeout=10)
    except requests.RequestException:
        raise ErroApi("Não foi possível conectar à API. Ela está no ar?", 503)

    try:
        dados = resposta.json()
    except ValueError:
        dados = {}

    # 401 fora do login = token ausente/expirado/inválido -> volta para o login
    if resposta.status_code == 401 and caminho != "/login":
        raise SessaoExpirada()
    if not resposta.ok:
        raise ErroApi(dados.get("erro", f"Erro inesperado ({resposta.status_code})."), resposta.status_code)
    return dados
