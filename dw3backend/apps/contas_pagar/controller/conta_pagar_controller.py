"""CONTROLLER de Contas a Pagar: valida os dados, aplica as regras de negócio,
chama o model e devolve (corpo, status_http). Não conhece Flask: é só Python."""
from datetime import date
from decimal import Decimal, InvalidOperation

from apps.contas_pagar.model import conta_pagar_model
from apps.plano_contas.model import plano_conta_model

NAO_ENCONTRADA = {"erro": "Conta a pagar não encontrada."}


def _validar(dados):
    """Confere os campos e converte para os tipos certos.
    Devolve (valores_limpos, mensagem_de_erro)."""
    descricao = (dados.get("descricao") or "").strip()
    if not descricao or len(descricao) > 150:
        return None, "Informe a descrição (até 150 caracteres)."

    try:
        valor = Decimal(str(dados.get("valor")))
        if not valor.is_finite() or valor <= 0:
            raise ValueError
    except (InvalidOperation, ValueError):
        return None, "O valor deve ser um número maior que zero."

    try:
        vencimento = date.fromisoformat(dados.get("data_vencimento") or "")
    except ValueError:
        return None, "Data de vencimento inválida (use AAAA-MM-DD)."

    pago = bool(dados.get("pago", False))

    # Chave estrangeira: o plano de contas precisa existir e não estar removido
    try:
        plano_id = int(dados.get("plano_conta_id"))
    except (TypeError, ValueError):
        return None, "Selecione um plano de contas."
    if not plano_conta_model.get_by_id(plano_id):
        return None, "Plano de contas inexistente."

    return (descricao, valor, vencimento, pago, plano_id), None


# GetAllContasPagar
def get_all():
    return conta_pagar_model.get_all(), 200


# GetContaPagarByID
def get_by_id(id):
    conta = conta_pagar_model.get_by_id(id)
    if not conta:
        return NAO_ENCONTRADA, 404
    return conta, 200


# InsertContaPagar
def insert(dados):
    valores, erro = _validar(dados)
    if erro:
        return {"erro": erro}, 400
    return conta_pagar_model.insert(*valores), 201


# UpdateContaPagar
def update(id, dados):
    valores, erro = _validar(dados)
    if erro:
        return {"erro": erro}, 400
    conta = conta_pagar_model.update(id, *valores)
    if not conta:
        return NAO_ENCONTRADA, 404
    return conta, 200


# DeleteContaPagar (soft delete)
def delete(id):
    if conta_pagar_model.delete(id) == 0:
        return NAO_ENCONTRADA, 404
    return {"mensagem": "Conta a pagar removida."}, 200
