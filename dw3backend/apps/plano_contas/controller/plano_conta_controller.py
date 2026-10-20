"""CONTROLLER de Plano de Contas: valida os dados, aplica as regras de negócio,
chama o model e devolve (corpo, status_http). Não conhece Flask: é só Python."""
from apps.plano_contas.model import plano_conta_model
from apps.plano_contas.model.plano_conta_model import CodigoDuplicado

NAO_ENCONTRADO = {"erro": "Plano de contas não encontrado."}
CODIGO_REPETIDO = {"erro": "Já existe um plano de contas com esse código."}


def _validar(dados):
    """Devolve (valores_limpos, mensagem_de_erro)."""
    codigo = (dados.get("codigo") or "").strip()
    nome = (dados.get("nome") or "").strip()
    if not codigo or not nome:
        return None, "Informe código e nome."
    if len(codigo) > 20 or len(nome) > 100:
        return None, "Código (máx. 20) ou nome (máx. 100) muito longo."
    return (codigo, nome), None


# GetAllPlanoContas
def get_all():
    return plano_conta_model.get_all(), 200


# GetPlanoContaByID
def get_by_id(id):
    plano = plano_conta_model.get_by_id(id)
    if not plano:
        return NAO_ENCONTRADO, 404
    return plano, 200


# InsertPlanoConta
def insert(dados):
    valores, erro = _validar(dados)
    if erro:
        return {"erro": erro}, 400
    try:
        return plano_conta_model.insert(*valores), 201
    except CodigoDuplicado:
        return CODIGO_REPETIDO, 409


# UpdatePlanoConta
def update(id, dados):
    valores, erro = _validar(dados)
    if erro:
        return {"erro": erro}, 400
    try:
        plano = plano_conta_model.update(id, *valores)
    except CodigoDuplicado:
        return CODIGO_REPETIDO, 409
    if not plano:
        return NAO_ENCONTRADO, 404
    return plano, 200


# DeletePlanoConta (soft delete)
def delete(id):
    # Regra de negócio: não remove um plano que ainda tem contas a pagar ativas
    if plano_conta_model.possui_contas_ativas(id):
        return {"erro": "Este plano possui contas a pagar vinculadas. Remova-as antes."}, 409
    if plano_conta_model.delete(id) == 0:
        return NAO_ENCONTRADO, 404
    return {"mensagem": "Plano de contas removido."}, 200
