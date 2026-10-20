"""Cálculos de apresentação da tela de Contas a Pagar (status, resumo e filtros)."""
from datetime import date

ROTULO_STATUS = {"paga": "Paga", "vencida": "Vencida", "aberto": "Em aberto"}


def hoje_iso():
    return date.today().isoformat()


def status_da_conta(conta):
    """paga | vencida | aberto. Datas ISO ('AAAA-MM-DD') podem ser comparadas como texto."""
    if conta["pago"]:
        return "paga"
    return "vencida" if conta["data_vencimento"] < hoje_iso() else "aberto"


def anotar_status(contas):
    """Acrescenta em cada conta o status e o rótulo para o template usar."""
    for conta in contas:
        conta["status"] = status_da_conta(conta)
        conta["status_rotulo"] = ROTULO_STATUS[conta["status"]]
    return contas


def calcular_resumo(contas):
    """Soma o valor das contas por status."""
    resumo = {"aberto": 0.0, "vencida": 0.0, "paga": 0.0}
    for conta in contas:
        resumo[conta["status"]] += conta["valor"]
    return resumo


def filtrar(contas, termo, status):
    termo = termo.strip().lower()
    return [
        c
        for c in contas
        if termo in c["descricao"].lower() and (status == "" or c["status"] == status)
    ]
