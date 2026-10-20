"""Formatadores usados nos templates (filtros do Jinja)."""


def moeda(valor):
    """1850.4 -> 'R$ 1.850,40'"""
    texto = f"{float(valor):,.2f}"  # '1,850.40' (padrão americano)
    return "R$ " + texto.replace(",", "X").replace(".", ",").replace("X", ".")


def data_br(iso):
    """'2026-10-20' -> '20/10/2026'"""
    ano, mes, dia = iso.split("-")
    return f"{dia}/{mes}/{ano}"
