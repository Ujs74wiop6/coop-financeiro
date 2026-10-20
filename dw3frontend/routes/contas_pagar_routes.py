"""Telas de Contas a Pagar.

  GET  /contas-pagar                 lista (com busca, filtro e resumo)
  GET  /contas-pagar/nova            formulário vazio
  POST /contas-pagar/nova            InsertContaPagar
  GET  /contas-pagar/<id>/editar     formulário preenchido (GetContaPagarByID)
  POST /contas-pagar/<id>/editar     UpdateContaPagar
  POST /contas-pagar/<id>/excluir    DeleteContaPagar
"""
from flask import Blueprint, flash, redirect, render_template, request, url_for

from apps.api_client import ErroApi
from apps.contas_pagar import contas_pagar_api as api
from apps.contas_pagar import contas_pagar_regras as regras
from apps.login.sessao import login_obrigatorio
from apps.plano_contas.plano_contas_api import get_all_plano_contas

bp = Blueprint("contas_pagar", __name__, url_prefix="/contas-pagar")


@bp.get("")
@login_obrigatorio
def lista():
    contas = regras.anotar_status(api.get_all_contas_pagar())
    planos = get_all_plano_contas()
    nomes_planos = {p["id"]: f'{p["codigo"]} - {p["nome"]}' for p in planos}

    busca = request.args.get("q", "")
    filtro_status = request.args.get("status", "")
    return render_template(
        "contas_pagar/lista.html",
        contas=regras.filtrar(contas, busca, filtro_status),
        resumo=regras.calcular_resumo(contas),  # o resumo considera todas as contas
        nomes_planos=nomes_planos,
        busca=busca,
        filtro_status=filtro_status,
    )


@bp.route("/nova", methods=["GET", "POST"])
@login_obrigatorio
def nova():
    return _formulario(None)


@bp.route("/<int:id>/editar", methods=["GET", "POST"])
@login_obrigatorio
def editar(id):
    return _formulario(id)


def _formulario(id):
    """Mesmo formulário para criar (id=None) e editar."""
    planos = get_all_plano_contas()
    if not planos:
        flash("Cadastre um plano de contas antes de criar uma conta a pagar.", "erro")
        return redirect(url_for("plano_contas.lista"))

    if request.method == "GET":
        conta = {
            "descricao": "",
            "valor": "",
            "data_vencimento": regras.hoje_iso(),
            "pago": False,
            "plano_conta_id": planos[0]["id"],
        }
        if id:
            try:
                conta = api.get_conta_pagar_by_id(id)
            except ErroApi as e:
                if e.status != 404:
                    raise
                flash(e.mensagem, "erro")
                return redirect(url_for("contas_pagar.lista"))
        return render_template("contas_pagar/form.html", conta=conta, id=id, planos=planos, erro=None)

    dados = {
        "descricao": request.form.get("descricao", "").strip(),
        "valor": request.form.get("valor", "").strip().replace(",", "."),
        "data_vencimento": request.form.get("data_vencimento", ""),
        "pago": "pago" in request.form,  # checkbox: só vem no formulário se marcado
        "plano_conta_id": request.form.get("plano_conta_id", type=int),
    }
    try:
        if id:
            api.update_conta_pagar(id, dados)
        else:
            api.insert_conta_pagar(dados)
    except ErroApi as e:
        if e.status not in (400, 404, 409):
            raise
        return (
            render_template("contas_pagar/form.html", conta=dados, id=id, planos=planos, erro=e.mensagem),
            e.status,
        )

    flash("Conta a pagar atualizada." if id else "Conta a pagar criada.", "ok")
    return redirect(url_for("contas_pagar.lista"))


@bp.post("/<int:id>/excluir")
@login_obrigatorio
def excluir(id):
    try:
        api.delete_conta_pagar(id)
        flash("Conta a pagar removida.", "ok")
    except ErroApi as e:
        if e.status != 404:
            raise
        flash(e.mensagem, "erro")
    return redirect(url_for("contas_pagar.lista"))
