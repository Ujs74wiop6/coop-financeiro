"""Rotas de Plano de Contas (todas protegidas por JWT).

  GetAllPlanoContas  -> GET    /api/plano-contas
  GetPlanoContaByID  -> GET    /api/plano-contas/<id>
  InsertPlanoConta   -> POST   /api/plano-contas
  UpdatePlanoConta   -> PUT    /api/plano-contas/<id>
  DeletePlanoConta   -> DELETE /api/plano-contas/<id>   (soft delete)
"""
from flask import Blueprint, jsonify, request

from apps.login.controller.login_controller import token_obrigatorio
from apps.plano_contas.controller import plano_conta_controller as controller

bp = Blueprint("plano_contas", __name__, url_prefix="/api/plano-contas")


@bp.get("")
@token_obrigatorio
def get_all():
    corpo, status = controller.get_all()
    return jsonify(corpo), status


@bp.get("/<int:id>")
@token_obrigatorio
def get_by_id(id):
    corpo, status = controller.get_by_id(id)
    return jsonify(corpo), status


@bp.post("")
@token_obrigatorio
def insert():
    corpo, status = controller.insert(request.get_json(silent=True) or {})
    return jsonify(corpo), status


@bp.put("/<int:id>")
@token_obrigatorio
def update(id):
    corpo, status = controller.update(id, request.get_json(silent=True) or {})
    return jsonify(corpo), status


@bp.delete("/<int:id>")
@token_obrigatorio
def delete(id):
    corpo, status = controller.delete(id)
    return jsonify(corpo), status
