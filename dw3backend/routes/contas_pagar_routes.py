"""Rotas de Contas a Pagar (todas protegidas por JWT).

  GetAllContasPagar  -> GET    /api/contas-pagar
  GetContaPagarByID  -> GET    /api/contas-pagar/<id>
  InsertContaPagar   -> POST   /api/contas-pagar
  UpdateContaPagar   -> PUT    /api/contas-pagar/<id>
  DeleteContaPagar   -> DELETE /api/contas-pagar/<id>   (soft delete)
"""
from flask import Blueprint, jsonify, request

from apps.contas_pagar.controller import conta_pagar_controller as controller
from apps.login.controller.login_controller import token_obrigatorio

bp = Blueprint("contas_pagar", __name__, url_prefix="/api/contas-pagar")


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
