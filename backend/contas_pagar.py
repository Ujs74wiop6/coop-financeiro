"""CRUD de Contas a Pagar (o lado "N" da relação 1:N).

Correspondência com o enunciado:
  GetAllContasPagar  -> GET    /api/contas-pagar
  GetContaPagarByID  -> GET    /api/contas-pagar/<id>
  InsertContaPagar   -> POST   /api/contas-pagar
  UpdateContaPagar   -> PUT    /api/contas-pagar/<id>
  DeleteContaPagar   -> DELETE /api/contas-pagar/<id>   (soft delete)
"""
from datetime import date
from decimal import Decimal, InvalidOperation

from flask import Blueprint, jsonify, request

from auth import token_obrigatorio
from db import executar

bp = Blueprint("contas_pagar", __name__)


def _validar(dados):
    """Confere os campos e converte para os tipos certos.
    Devolve (valores_limpos, mensagem_de_erro)."""
    descricao = (dados.get("descricao") or "").strip()
    if not descricao or len(descricao) > 150:
        return None, "Informe a descrição (até 150 caracteres)."

    try:
        valor = Decimal(str(dados.get("valor")))
        if valor <= 0:
            raise ValueError
    except (InvalidOperation, ValueError):
        return None, "O valor deve ser um número maior que zero."

    try:
        vencimento = date.fromisoformat(dados.get("data_vencimento") or "")
    except ValueError:
        return None, "Data de vencimento inválida (use AAAA-MM-DD)."

    pago = bool(dados.get("pago", False))

    # Chave estrangeira: o plano de contas precisa existir e não estar removido
    try:
        plano_id = int(dados.get("plano_conta_id"))
    except (TypeError, ValueError):
        return None, "Selecione um plano de contas."
    plano = executar(
        "SELECT 1 FROM plano_contas WHERE id = %s AND removido = FALSE", (plano_id,), "um"
    )
    if not plano:
        return None, "Plano de contas inexistente."

    return (descricao, valor, vencimento, pago, plano_id), None


# ---------- GetAllContasPagar ----------
@bp.get("/api/contas-pagar")
@token_obrigatorio
def get_all():
    linhas = executar(
        "SELECT * FROM contas_pagar WHERE removido = FALSE ORDER BY data_vencimento, id"
    )
    return jsonify(linhas)


# ---------- GetContaPagarByID ----------
@bp.get("/api/contas-pagar/<int:id>")
@token_obrigatorio
def get_by_id(id):
    linha = executar(
        "SELECT * FROM contas_pagar WHERE id = %s AND removido = FALSE", (id,), "um"
    )
    if not linha:
        return jsonify(erro="Conta a pagar não encontrada."), 404
    return jsonify(linha)


# ---------- InsertContaPagar ----------
@bp.post("/api/contas-pagar")
@token_obrigatorio
def insert():
    valores, erro = _validar(request.get_json(silent=True) or {})
    if erro:
        return jsonify(erro=erro), 400
    nova = executar(
        "INSERT INTO contas_pagar "
        "(descricao, valor, data_vencimento, pago, plano_conta_id) "
        "VALUES (%s, %s, %s, %s, %s) RETURNING *",
        valores,
        "um",
    )
    return jsonify(nova), 201


# ---------- UpdateContaPagar ----------
@bp.put("/api/contas-pagar/<int:id>")
@token_obrigatorio
def update(id):
    valores, erro = _validar(request.get_json(silent=True) or {})
    if erro:
        return jsonify(erro=erro), 400
    atualizada = executar(
        "UPDATE contas_pagar SET descricao = %s, valor = %s, data_vencimento = %s, "
        "pago = %s, plano_conta_id = %s WHERE id = %s AND removido = FALSE RETURNING *",
        valores + (id,),
        "um",
    )
    if not atualizada:
        return jsonify(erro="Conta a pagar não encontrada."), 404
    return jsonify(atualizada)


# ---------- DeleteContaPagar (soft delete) ----------
@bp.delete("/api/contas-pagar/<int:id>")
@token_obrigatorio
def delete(id):
    afetadas = executar(
        "UPDATE contas_pagar SET removido = TRUE WHERE id = %s AND removido = FALSE",
        (id,),
        "nada",
    )
    if afetadas == 0:
        return jsonify(erro="Conta a pagar não encontrada."), 404
    return jsonify(mensagem="Conta a pagar removida.")
