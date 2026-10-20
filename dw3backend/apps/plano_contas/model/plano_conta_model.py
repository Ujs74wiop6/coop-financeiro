"""MODEL de Plano de Contas (o lado "1" da relação 1:N): só SQL, nenhuma regra de negócio."""
from psycopg2.errors import UniqueViolation

from database.conexao import executar


class CodigoDuplicado(Exception):
    """Já existe um plano ativo com esse código."""


def get_all():
    return executar("SELECT * FROM plano_contas WHERE removido = FALSE ORDER BY codigo")


def get_by_id(id):
    return executar(
        "SELECT * FROM plano_contas WHERE id = %s AND removido = FALSE", (id,), "um"
    )


def insert(codigo, nome):
    try:
        return executar(
            "INSERT INTO plano_contas (codigo, nome) VALUES (%s, %s) RETURNING *",
            (codigo, nome),
            "um",
        )
    except UniqueViolation:
        raise CodigoDuplicado()


def update(id, codigo, nome):
    try:
        return executar(
            "UPDATE plano_contas SET codigo = %s, nome = %s "
            "WHERE id = %s AND removido = FALSE RETURNING *",
            (codigo, nome, id),
            "um",
        )
    except UniqueViolation:
        raise CodigoDuplicado()


def delete(id):
    """Soft delete: o registro continua na tabela, só muda removido para TRUE.
    Devolve quantas linhas foram afetadas (0 = não encontrado)."""
    return executar(
        "UPDATE plano_contas SET removido = TRUE WHERE id = %s AND removido = FALSE",
        (id,),
        "nada",
    )


def possui_contas_ativas(id):
    """True se ainda existe conta a pagar (não removida) ligada a este plano."""
    linha = executar(
        "SELECT 1 FROM contas_pagar WHERE plano_conta_id = %s AND removido = FALSE LIMIT 1",
        (id,),
        "um",
    )
    return linha is not None
