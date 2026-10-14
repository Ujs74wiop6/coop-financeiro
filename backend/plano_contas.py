"""CRUD de Plano de Contas (o lado "1" da relação 1:N).

Correspondência com o enunciado:
  GetAllPlanoContas  -> GET    /api/plano-contas
  GetPlanoContaByID  -> GET    /api/plano-contas/<id>
  InsertPlanoConta   -> POST   /api/plano-contas
  UpdatePlanoConta   -> PUT    /api/plano-contas/<id>
  DeletePlanoConta   -> DELETE /api/plano-contas/<id>   (soft delete)
"""
from flask import Blueprint, jsonify, request
from psycopg2.errors import UniqueViolation

from auth import token_obrigatorio
from db import executar

bp = Blueprint("plano_contas", __name__)


def _validar(dados):
    """Devolve (valores_limpos, mensagem_de_erro)."""
    codigo = (dados.get("codigo") or "").strip()
    nome = (dados.get("nome") or "").strip()
    if not codigo or not nome:
        return None, "Informe código e nome."
    if len(codigo) > 20 or len(nome) > 100:
        return None, "Código (máx. 20) ou nome (máx. 100) muito longo."
    return (codigo, nome), None


# ---------- GetAllPlanoContas ----------
@bp.get("/api/plano-contas")
@token_obrigatorio
def get_all():
    linhas = executar("SELECT * FROM plano_contas WHERE removido = FALSE ORDER BY codigo")
    return jsonify(linhas)


# ---------- GetPlanoContaByID ----------
@bp.get("/api/plano-contas/<int:id>")
@token_obrigatorio
def get_by_id(id):
    linha = executar(
        "SELECT * FROM plano_contas WHERE id = %s AND removido = FALSE", (id,), "um"
    )
    if not linha:
        return jsonify(erro="Plano de contas não encontrado."), 404
    return jsonify(linha)


# ---------- InsertPlanoConta ----------
@bp.post("/api/plano-contas")
@token_obrigatorio
def insert():
    valores, erro = _validar(request.get_json(silent=True) or {})
    if erro:
        return jsonify(erro=erro), 400
    try:
        nova = executar(
            "INSERT INTO plano_contas (codigo, nome) VALUES (%s, %s) RETURNING *",
            valores,
            "um",
        )
    except UniqueViolation:
        return jsonify(erro="Já existe um plano de contas com esse código."), 409
    return jsonify(nova), 201


# ---------- UpdatePlanoConta ----------
@bp.put("/api/plano-contas/<int:id>")
@token_obrigatorio
def update(id):
    valores, erro = _validar(request.get_json(silent=True) or {})
    if erro:
        return jsonify(erro=erro), 400
    try:
        atualizada = executar(
            "UPDATE plano_contas SET codigo = %s, nome = %s "
            "WHERE id = %s AND removido = FALSE RETURNING *",
            valores + (id,),
            "um",
        )
    except UniqueViolation:
        return jsonify(erro="Já existe um plano de contas com esse código."), 409
    if not atualizada:
        return jsonify(erro="Plano de contas não encontrado."), 404
    return jsonify(atualizada)


# ---------- DeletePlanoConta (soft delete) ----------
@bp.delete("/api/plano-contas/<int:id>")
@token_obrigatorio
def delete(id):
    # Regra de negócio: não remove um plano que ainda tem contas a pagar ativas
    em_uso = executar(
        "SELECT 1 FROM contas_pagar WHERE plano_conta_id = %s AND removido = FALSE LIMIT 1",
        (id,),
        "um",
    )
    if em_uso:
        return jsonify(erro="Este plano possui contas a pagar vinculadas. Remova-as antes."), 409

    # Soft delete: o registro continua na tabela, só muda removido para TRUE
    afetadas = executar(
        "UPDATE plano_contas SET removido = TRUE WHERE id = %s AND removido = FALSE",
        (id,),
        "nada",
    )
    if afetadas == 0:
        return jsonify(erro="Plano de contas não encontrado."), 404
    return jsonify(mensagem="Plano de contas removido.")
