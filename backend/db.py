"""Acesso ao banco de dados (PostgreSQL).

Só o back-end conversa com o banco. O front-end nunca chega aqui.
Usamos SQL puro com psycopg2, para ficar claro o que roda no banco.
"""
import os
from datetime import date
from decimal import Decimal

import psycopg2
from psycopg2.extras import RealDictCursor


def conectar():
    """Abre uma conexão nova com o banco, lendo os dados das variáveis de ambiente."""
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        dbname=os.getenv("DB_NAME", "financeiro"),
        user=os.getenv("DB_USER", "financeiro"),
        password=os.getenv("DB_PASSWORD", ""),
    )


def executar(sql, params=(), retorno="todos"):
    """Executa um comando SQL.

    sql     -> o comando, com %s no lugar dos valores (evita SQL Injection)
    params  -> tupla com os valores, na ordem dos %s
    retorno -> "todos": devolve lista de linhas (SELECT com várias linhas)
               "um"   : devolve uma linha ou None (SELECT por id, INSERT ... RETURNING)
               "nada" : não devolve nada; devolve só a qtd de linhas afetadas
    """
    conn = conectar()
    try:
        # 'with conn' faz COMMIT se tudo der certo e ROLLBACK se der erro
        with conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, params)
            if retorno == "todos":
                return [_serializar(l) for l in cur.fetchall()]
            if retorno == "um":
                linha = cur.fetchone()
                return _serializar(linha) if linha else None
            return cur.rowcount
    finally:
        conn.close()


def _serializar(linha):
    """Converte tipos que o JSON não entende: date -> 'AAAA-MM-DD', Decimal -> float."""
    resultado = {}
    for campo, valor in linha.items():
        if isinstance(valor, date):
            valor = valor.isoformat()
        elif isinstance(valor, Decimal):
            valor = float(valor)
        resultado[campo] = valor
    return resultado
