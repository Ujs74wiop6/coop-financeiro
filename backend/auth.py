"""Login e proteção das rotas com JWT.

Fluxo:
  1. O usuário envia usuário+senha para POST /api/login
  2. Se estiverem certos, o servidor devolve um TOKEN (JWT) assinado com JWT_SECRET
  3. Nas próximas requisições o cliente manda o token no cabeçalho
         Authorization: Bearer <token>
  4. O decorator @token_obrigatorio confere a assinatura e a validade do token
"""
import os
from datetime import datetime, timedelta, timezone
from functools import wraps

import jwt
from flask import Blueprint, jsonify, request
from werkzeug.security import check_password_hash, generate_password_hash

from db import executar

bp = Blueprint("auth", __name__)

JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret")
JWT_EXPIRA_MINUTOS = int(os.getenv("JWT_EXPIRA_MINUTOS", "60"))


def criar_admin_se_nao_existir():
    """No primeiro start cria o usuário inicial (senha guardada como hash)."""
    usuario = os.getenv("ADMIN_USUARIO", "admin")
    senha = os.getenv("ADMIN_SENHA", "admin123")
    existe = executar("SELECT id FROM usuarios WHERE usuario = %s", (usuario,), "um")
    if not existe:
        executar(
            "INSERT INTO usuarios (usuario, senha_hash) VALUES (%s, %s)",
            (usuario, generate_password_hash(senha)),
            "nada",
        )
        print(f"Usuário '{usuario}' criado.")


def token_obrigatorio(funcao):
    """Decorator: bloqueia a rota se não vier um JWT válido."""

    @wraps(funcao)
    def verificar(*args, **kwargs):
        cabecalho = request.headers.get("Authorization", "")
        if not cabecalho.startswith("Bearer "):
            return jsonify(erro="Token não informado."), 401
        token = cabecalho.split(" ", 1)[1]
        try:
            jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return jsonify(erro="Token expirado. Faça login novamente."), 401
        except jwt.InvalidTokenError:
            return jsonify(erro="Token inválido."), 401
        return funcao(*args, **kwargs)

    return verificar


@bp.post("/api/login")
def login():
    dados = request.get_json(silent=True) or {}
    usuario = (dados.get("usuario") or "").strip()
    senha = dados.get("senha") or ""

    linha = executar("SELECT * FROM usuarios WHERE usuario = %s", (usuario,), "um")
    # Mesma mensagem para usuário inexistente e senha errada (não revela qual deu erro)
    if not linha or not check_password_hash(linha["senha_hash"], senha):
        return jsonify(erro="Usuário ou senha inválidos."), 401

    expira = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRA_MINUTOS)
    token = jwt.encode(
        {"sub": linha["usuario"], "exp": expira}, JWT_SECRET, algorithm="HS256"
    )
    return jsonify(token=token, usuario=linha["usuario"], expira_em=expira.isoformat())
