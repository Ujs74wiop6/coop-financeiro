"""Sessão do usuário no front-end.

O JWT e os dados vindos do back-end ficam num COOKIE de sessão do Flask
(assinado com SECRET_KEY e marcado como HttpOnly: o JavaScript da página não consegue ler).
"""
from functools import wraps

from flask import redirect, session, url_for


def salvar_sessao(dados):
    session["token"] = dados["token"]
    session["usuario"] = dados["usuario"]
    session["expira_em"] = dados["expira_em"]


def limpar_sessao():
    session.clear()


def obter_token():
    return session.get("token")


def login_obrigatorio(funcao):
    """Decorator: sem token na sessão, a página manda o usuário para o login."""

    @wraps(funcao)
    def verificar(*args, **kwargs):
        if not obter_token():
            return redirect(url_for("login.login"))
        return funcao(*args, **kwargs)

    return verificar
