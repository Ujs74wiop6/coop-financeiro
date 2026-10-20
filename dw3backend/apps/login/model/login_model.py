"""MODEL do login: só conversa com a tabela `usuarios` (SQL)."""
from database.conexao import executar


def buscar_por_usuario(usuario):
    return executar("SELECT * FROM usuarios WHERE usuario = %s", (usuario,), "um")


def inserir(usuario, senha_hash):
    executar(
        "INSERT INTO usuarios (usuario, senha_hash) VALUES (%s, %s)",
        (usuario, senha_hash),
        "nada",
    )
