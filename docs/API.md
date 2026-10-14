# Referência da API

Base URL: `http://localhost:5000/api` · Formato: JSON.

Todas as rotas, **exceto** `/login` e `/health`, exigem o cabeçalho:

```
Authorization: Bearer <token>
```

## Autenticação

### `POST /login`

```json
// corpo
{ "usuario": "admin", "senha": "admin123" }

// 200
{ "token": "eyJhbGciOi...", "usuario": "admin", "expira_em": "2026-10-13T23:30:00+00:00" }

// 401
{ "erro": "Usuário ou senha inválidos." }
```

## Plano de Contas

Campos: `id`, `codigo` (texto, até 20), `nome` (texto, até 100), `removido`.

| Operação | Método e rota | Corpo | Sucesso | Erros |
|---|---|---|---|---|
| GetAllPlanoContas | `GET /plano-contas` | — | 200 lista | 401 |
| GetPlanoContaByID | `GET /plano-contas/<id>` | — | 200 objeto | 401, 404 |
| InsertPlanoConta | `POST /plano-contas` | `{codigo, nome}` | 201 objeto criado | 400, 401, 409 (código repetido) |
| UpdatePlanoConta | `PUT /plano-contas/<id>` | `{codigo, nome}` | 200 objeto atualizado | 400, 401, 404, 409 |
| DeletePlanoConta | `DELETE /plano-contas/<id>` | — | 200 `{mensagem}` | 401, 404, 409 (tem contas ativas) |

## Contas a Pagar

Campos: `id`, `descricao` (texto, até 150), `valor` (decimal > 0), `data_vencimento` (`AAAA-MM-DD`), `pago` (booleano), `plano_conta_id` (FK), `removido`.

| Operação | Método e rota | Corpo | Sucesso | Erros |
|---|---|---|---|---|
| GetAllContasPagar | `GET /contas-pagar` | — | 200 lista | 401 |
| GetContaPagarByID | `GET /contas-pagar/<id>` | — | 200 objeto | 401, 404 |
| InsertContaPagar | `POST /contas-pagar` | `{descricao, valor, data_vencimento, pago, plano_conta_id}` | 201 objeto criado | 400, 401 |
| UpdateContaPagar | `PUT /contas-pagar/<id>` | idem | 200 objeto atualizado | 400, 401, 404 |
| DeleteContaPagar | `DELETE /contas-pagar/<id>` | — | 200 `{mensagem}` | 401, 404 |

## Códigos de status usados

| Código | Significado aqui |
|---|---|
| 200 / 201 | Deu certo / criado |
| 400 | Dado inválido (campo vazio, valor ≤ 0, data errada, plano inexistente) |
| 401 | Sem token, token inválido/expirado ou login errado |
| 404 | Registro não existe (ou já foi removido) |
| 409 | Conflito com uma regra (código repetido; plano com contas vinculadas) |

## Testando com curl

```bash
# 1) Login e guarda o token
TOKEN=$(curl -s -X POST http://localhost:5000/api/login \
  -H 'Content-Type: application/json' \
  -d '{"usuario":"admin","senha":"admin123"}' | python3 -c "import sys,json;print(json.load(sys.stdin)['token'])")

# 2) Lista as contas
curl -s http://localhost:5000/api/contas-pagar -H "Authorization: Bearer $TOKEN"

# 3) Cria uma conta
curl -s -X POST http://localhost:5000/api/contas-pagar \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"descricao":"Frete","valor":"310.00","data_vencimento":"2026-11-10","pago":false,"plano_conta_id":1}'

# 4) Sem token -> 401
curl -s -i http://localhost:5000/api/contas-pagar
```
