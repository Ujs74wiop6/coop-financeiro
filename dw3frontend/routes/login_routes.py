"""Rotas de entrada e saída do sistema."""
from flask import Blueprint, flash, redirect, render_template, request, url_for

from apps.api_client import ErroApi
from apps.login import login_api, sessao

bp = Blueprint("login", __name__)


@bp.get("/")
def inicio():
    return redirect(url_for("contas_pagar.lista"))


@bp.route("/login", methods=["GET", "POST"])
def login():
    if sessao.obter_token():
        return redirect(url_for("contas_pagar.lista"))

    if request.method == "GET":
        return render_template("login.html", erro=None, usuario="")

    usuario = request.form.get("usuario", "").strip()
    senha = request.form.get("senha", "")
    if not usuario or not senha:
        return render_template("login.html", erro="Preencha usuário e senha.", usuario=usuario), 400

    try:
        dados = login_api.fazer_login(usuario, senha)  # chama POST /api/login do back-end
    except ErroApi as e:
        return render_template("login.html", erro=e.mensagem, usuario=usuario), e.status

    sessao.salvar_sessao(dados)  # guarda o JWT no cookie de sessão
    return redirect(url_for("contas_pagar.lista"))


@bp.post("/logout")
def logout():
    sessao.limpar_sessao()
    flash("Você saiu do sistema.", "ok")
    return redirect(url_for("login.login"))
