"""Ponto de entrada do front-end (servidor Flask, porta 8080).

Este servidor entrega as páginas HTML (views) e, por baixo dos panos, chama a API
do back-end (porta 5000) com o JWT guardado na sessão. Ele NÃO acessa o banco.
"""
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / "frontend.env")  # no Docker as variáveis já vêm prontas

import os  # noqa: E402

from flask import Flask, flash, redirect, render_template, url_for  # noqa: E402

from apps import formatadores  # noqa: E402
from apps.api_client import ErroApi, SessaoExpirada  # noqa: E402
from apps.login import sessao  # noqa: E402
from routes import contas_pagar_routes, login_routes, plano_contas_routes  # noqa: E402

# views = templates HTML | public = arquivos estáticos (CSS, JS)
app = Flask(__name__, template_folder="views", static_folder="public", static_url_path="/public")
app.secret_key = os.getenv("SECRET_KEY", "dev-chave-so-para-desenvolvimento-local-0123456789")
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax")

app.add_template_filter(formatadores.moeda, "moeda")
app.add_template_filter(formatadores.data_br, "data_br")

app.register_blueprint(login_routes.bp)
app.register_blueprint(plano_contas_routes.bp)
app.register_blueprint(contas_pagar_routes.bp)


@app.errorhandler(SessaoExpirada)
def sessao_expirada(_erro):
    """A API recusou o token: limpa a sessão e volta ao login."""
    sessao.limpar_sessao()
    flash("Sua sessão expirou. Entre novamente.", "erro")
    return redirect(url_for("login.login"))


@app.errorhandler(ErroApi)
def erro_da_api(erro):
    """Erro inesperado vindo da API (ex.: back-end fora do ar)."""
    return render_template("erro.html", mensagem=erro.mensagem), erro.status


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
