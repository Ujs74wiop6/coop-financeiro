# Arquitetura

## 1. Visão geral (componentes e portas)

O navegador baixa o front-end do servidor da porta 8080 e, a partir daí, o JavaScript chama a API da porta 5000. Somente a API conversa com o banco.

```mermaid
flowchart LR
    U([Usuário<br/>navegador])

    subgraph Docker["Docker Compose"]
        F["frontend<br/>python http.server<br/>:8080<br/>HTML · CSS · JS"]
        B["backend<br/>Flask API REST<br/>:5000"]
        D[("db<br/>PostgreSQL<br/>:5432")]
    end

    U -- "1. abre a página" --> F
    U -- "2. fetch + JWT<br/>(JSON)" --> B
    B -- "3. SQL (psycopg2)" --> D
    F -. "nunca acessa" .-x D
```

## 2. Modelo de dados (relação 1:N)

Um plano de contas (ex.: "Energia elétrica") classifica várias contas a pagar. Cada conta pertence a exatamente um plano.

```mermaid
erDiagram
    PLANO_CONTAS ||--o{ CONTAS_PAGAR : "classifica"
    PLANO_CONTAS {
        int id PK
        varchar codigo "texto, único entre ativos"
        varchar nome "texto"
        boolean removido "soft delete"
    }
    CONTAS_PAGAR {
        int id PK
        varchar descricao "texto"
        numeric valor "decimal(12,2), maior que 0"
        date data_vencimento "data"
        boolean pago
        int plano_conta_id FK
        boolean removido "soft delete"
    }
    USUARIOS {
        int id PK
        varchar usuario "único"
        varchar senha_hash "hash, nunca a senha pura"
    }
```

`USUARIOS` é uma tabela de apoio só para o login; não faz parte do CRUD pedido e não se relaciona com as outras.

## 3. Login e uso do JWT

```mermaid
sequenceDiagram
    actor U as Usuário
    participant F as Front-end (:8080)
    participant B as Back-end (:5000)
    participant D as PostgreSQL

    U->>F: digita usuário e senha
    F->>B: POST /api/login {usuario, senha}
    B->>D: SELECT * FROM usuarios WHERE usuario = %s
    D-->>B: linha com senha_hash
    B->>B: confere a senha contra o hash
    alt credenciais corretas
        B-->>F: 200 {token (JWT), usuario, expira_em}
        F->>F: guarda o token no localStorage
        F->>U: abre app.html
    else credenciais erradas
        B-->>F: 401 "Usuário ou senha inválidos."
        F->>U: mostra a mensagem de erro
    end

    Note over F,B: A partir daqui, toda chamada leva o token

    U->>F: abre "Contas a Pagar"
    F->>B: GET /api/contas-pagar<br/>Authorization: Bearer token
    B->>B: @token_obrigatorio valida assinatura e validade
    alt token válido
        B->>D: SELECT ... WHERE removido = FALSE
        D-->>B: linhas
        B-->>F: 200 [ ...contas ]
    else token ausente, inválido ou expirado
        B-->>F: 401
        F->>F: apaga a sessão e volta ao login
    end
```

## 4. Soft delete (exclusão lógica)

```mermaid
flowchart TD
    A([DELETE /api/plano-contas/id]) --> T{Token válido?}
    T -- não --> E1[401]
    T -- sim --> U{Há contas a pagar<br/>ativas neste plano?}
    U -- sim --> E2[409 conflito<br/>remova as contas antes]
    U -- não --> S["UPDATE plano_contas<br/>SET removido = TRUE<br/>WHERE id = ? AND removido = FALSE"]
    S --> R{Alguma linha<br/>afetada?}
    R -- não --> E3[404 não encontrado]
    R -- sim --> OK[200 removido]
```

O registro **continua na tabela**; apenas deixa de aparecer, porque `GetAll` e `GetByID` filtram `removido = FALSE`.
`DELETE /api/contas-pagar/id` segue o mesmo caminho, sem a verificação de vínculo.

## 5. Mapa: função do front → rota da API → SQL

| Função do front (`api.js`) | Rota | Operação SQL |
|---|---|---|
| `getAllPlanoContas()` | `GET /api/plano-contas` | `SELECT` onde `removido = FALSE` |
| `getPlanoContaByID(id)` | `GET /api/plano-contas/<id>` | `SELECT` por id, `removido = FALSE` |
| `insertPlanoConta(p)` | `POST /api/plano-contas` | `INSERT ... RETURNING *` |
| `updatePlanoConta(id, p)` | `PUT /api/plano-contas/<id>` | `UPDATE ... RETURNING *` |
| `deletePlanoConta(id)` | `DELETE /api/plano-contas/<id>` | `UPDATE ... SET removido = TRUE` |
| `getAllContasPagar()` | `GET /api/contas-pagar` | `SELECT` onde `removido = FALSE` |
| `getContaPagarByID(id)` | `GET /api/contas-pagar/<id>` | `SELECT` por id, `removido = FALSE` |
| `insertContaPagar(c)` | `POST /api/contas-pagar` | `INSERT ... RETURNING *` |
| `updateContaPagar(id, c)` | `PUT /api/contas-pagar/<id>` | `UPDATE ... RETURNING *` |
| `deleteContaPagar(id)` | `DELETE /api/contas-pagar/<id>` | `UPDATE ... SET removido = TRUE` |

## 6. Decisões de projeto

| Decisão | Motivo |
|---|---|
| **Flask** em vez de um framework maior | Poucas linhas por rota; fácil de ler e explicar. |
| **SQL puro** (psycopg2), sem ORM | Mostra exatamente o que roda no banco; combina com o foco em dados. |
| Parâmetros `%s` em todo SQL | Evita *SQL Injection*: o valor nunca é concatenado no texto do comando. |
| `NUMERIC(12,2)` para dinheiro | Não tem erro de arredondamento do `float`. |
| Senha com **hash** (`werkzeug.security`) | Se o banco vazar, as senhas não ficam expostas. |
| JWT assinado com `HS256` e expiração | O servidor não guarda sessão; o token carrega usuário e validade. |
| **CORS** restrito a `localhost:8080` | O navegador bloqueia chamadas entre portas diferentes, a menos que a API autorize. |
| Índice único parcial em `plano_contas.codigo` | Impede código repetido entre ativos, mas libera o código de um registro removido. |
| Front sem framework | Menos "mágica"; cada função faz uma coisa visível. |

## 7. Limitações conhecidas (e como evoluir)

- O servidor do Flask (`app.run`) e o `http.server` são para desenvolvimento/demonstração. Em produção: Gunicorn + Nginx.
- O token fica no `localStorage`, que é legível por JavaScript. Mais seguro: cookie `HttpOnly`. Foi mantido assim por ser permitido no enunciado e mais simples de demonstrar.
- Todos os usuários têm o mesmo nível de acesso (não há perfis).
- Não há paginação; para milhares de registros seria necessário.
