"""MODEL de Contas a Pagar (o lado "N" da relação 1:N): só SQL, nenhuma regra de negócio."""
from database.conexao import executar


def get_all():
    return executar(
        "SELECT * FROM contas_pagar WHERE removido = FALSE ORDER BY data_vencimento, id"
    )


def get_by_id(id):
    return executar(
        "SELECT * FROM contas_pagar WHERE id = %s AND removido = FALSE", (id,), "um"
    )


def insert(descricao, valor, data_vencimento, pago, plano_conta_id):
    return executar(
        "INSERT INTO contas_pagar (descricao, valor, data_vencimento, pago, plano_conta_id) "
        "VALUES (%s, %s, %s, %s, %s) RETURNING *",
        (descricao, valor, data_vencimento, pago, plano_conta_id),
        "um",
    )


def update(id, descricao, valor, data_vencimento, pago, plano_conta_id):
    return executar(
        "UPDATE contas_pagar SET descricao = %s, valor = %s, data_vencimento = %s, "
        "pago = %s, plano_conta_id = %s WHERE id = %s AND removido = FALSE RETURNING *",
        (descricao, valor, data_vencimento, pago, plano_conta_id, id),
        "um",
    )


def delete(id):
    """Soft delete: só muda removido para TRUE. Devolve a qtd de linhas afetadas."""
    return executar(
        "UPDATE contas_pagar SET removido = TRUE WHERE id = %s AND removido = FALSE",
        (id,),
        "nada",
    )
