"""Telas de Plano de Contas.

  GET  /plano-contas                 lista (com busca)
  GET  /plano-contas/novo            formulário vazio
  POST /plano-contas/novo            InsertPlanoConta
  GET  /plano-contas/<id>/editar     formulário preenchido (GetPlanoContaByID)
  POST /plano-contas/<id>/editar     UpdatePlanoConta
  POST /plano-contas/<id>/excluir    DeletePlanoConta
"""
from flask import Blueprint, flash, redirect, render_template, request, url_for

from apps.api_client import ErroApi
from apps.login.sessao import login_obrigatorio
from apps.plano_contas import plano_contas_api as api

bp = Blueprint("plano_contas", __name__, url_prefix="/plano-contas")


@bp.get("")
@login_obrigatorio
def lista():
    planos = api.get_all_plano_contas()
    busca = request.args.get("q", "")
    termo = busca.strip().lower()
    if termo:
        planos = [p for p in planos if termo in p["codigo"].lower() or termo in p["nome"].lower()]
    return render_template("plano_contas/lista.html", planos=planos, busca=busca)


@bp.route("/novo", methods=["GET", "POST"])
@login_obrigatorio
def novo():
    return _formulario(None)


@bp.route("/<int:id>/editar", methods=["GET", "POST"])
@login_obrigatorio
def editar(id):
    return _formulario(id)


def _formulario(id):
    """Mesmo formulário para criar (id=None) e editar."""
    if request.method == "GET":
        plano = {"codigo": "", "nome": ""}
        if id:
            try:
                plano = api.get_plano_conta_by_id(id)
            except ErroApi as e:
                if e.status != 404:
                    raise
                flash(e.mensagem, "erro")
                return redirect(url_for("plano_contas.lista"))
        return render_template("plano_contas/form.html", plano=plano, id=id, erro=None)

    dados = {
        "codigo": request.form.get("codigo", "").strip(),
        "nome": request.form.get("nome", "").strip(),
    }
    try:
        if id:
            api.update_plano_conta(id, dados)
        else:
            api.insert_plano_conta(dados)
    except ErroApi as e:
        if e.status not in (400, 404, 409):
            raise
        # volta para o formulário mantendo o que o usuário digitou
        return render_template("plano_contas/form.html", plano=dados, id=id, erro=e.mensagem), e.status

    flash("Plano de contas atualizado." if id else "Plano de contas criado.", "ok")
    return redirect(url_for("plano_contas.lista"))


@bp.post("/<int:id>/excluir")
@login_obrigatorio
def excluir(id):
    try:
        api.delete_plano_conta(id)
        flash("Plano de contas removido.", "ok")
    except ErroApi as e:
        if e.status not in (404, 409):  # 409 = ainda tem contas a pagar vinculadas
            raise
        flash(e.mensagem, "erro")
    return redirect(url_for("plano_contas.lista"))
