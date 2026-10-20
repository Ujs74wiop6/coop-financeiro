"""Rotas de autenticação. A rota só recebe a requisição, chama o controller e devolve JSON."""
from flask import Blueprint, jsonify, request

from apps.login.controller import login_controller

bp = Blueprint("login", __name__)


@bp.post("/api/login")
def login():
    corpo, status = login_controller.login(request.get_json(silent=True) or {})
    return jsonify(corpo), status
