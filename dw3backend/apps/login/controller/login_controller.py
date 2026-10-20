"""CONTROLLER do login + proteção das rotas com JWT.

Fluxo:
  1. O front envia usuário+senha para POST /api/login
  2. Se estiverem certos, o servidor devolve um TOKEN (JWT) assinado com JWT_SECRET
  3. Nas próximas requisições o cliente manda o token no cabeçalho
         Authorization: Bearer <token>
  4. O decorator @token_obrigatorio confere a assinatura e a validade do token
"""
import os
from datetime import datetime, timedelta, timezone
from functools import wraps

import jwt
from flask import jsonify, request
from werkzeug.security import check_password_hash, generate_password_hash

from apps.login.model import login_model


def _segredo():
    return os.getenv("JWT_SECRET", "dev-secret-so-para-desenvolvimento-local-0123456789")


def criar_admin_se_nao_existir():
    """No primeiro start cria o usuário inicial (a senha é guardada como hash)."""
    usuario = os.getenv("ADMIN_USUARIO", "admin")
    senha = os.getenv("ADMIN_SENHA", "admin123")
    if not login_model.buscar_por_usuario(usuario):
        login_model.inserir(usuario, generate_password_hash(senha))
        print(f"Usuário '{usuario}' criado.")


def login(dados):
    """Valida usuário e senha. Devolve (corpo, status_http)."""
    usuario = (dados.get("usuario") or "").strip()
    senha = dados.get("senha") or ""

    linha = login_model.buscar_por_usuario(usuario)
    # Mesma mensagem para usuário inexistente e senha errada (não revela qual deu erro)
    if not linha or not check_password_hash(linha["senha_hash"], senha):
        return {"erro": "Usuário ou senha inválidos."}, 401

    minutos = int(os.getenv("JWT_EXPIRA_MINUTOS", "60"))
    expira = datetime.now(timezone.utc) + timedelta(minutes=minutos)
    token = jwt.encode({"sub": linha["usuario"], "exp": expira}, _segredo(), algorithm="HS256")
    return {"token": token, "usuario": linha["usuario"], "expira_em": expira.isoformat()}, 200


def token_obrigatorio(funcao):
    """Decorator: bloqueia a rota se não vier um JWT válido."""

    @wraps(funcao)
    def verificar(*args, **kwargs):
        cabecalho = request.headers.get("Authorization", "")
        if not cabecalho.startswith("Bearer "):
            return jsonify(erro="Token não informado."), 401
        token = cabecalho.split(" ", 1)[1]
        try:
            jwt.decode(token, _segredo(), algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return jsonify(erro="Token expirado. Faça login novamente."), 401
        except jwt.InvalidTokenError:
            return jsonify(erro="Token inválido."), 401
        return funcao(*args, **kwargs)

    return verificar
