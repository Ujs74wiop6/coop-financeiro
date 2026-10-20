# Roteiro para explicar e demonstrar o projeto

O professor avalia "mesa a mesa" e o enunciado proíbe *vibe coding*. Isso significa que **você precisa entender e saber explicar cada parte**. Este roteiro ajuda a estudar na ordem em que o código é executado. Se alguma parte não ficar clara, leia o arquivo indicado com calma: todos têm comentários.

---

## 1. A ideia em 30 segundos

> "É o módulo financeiro de um ERP de cooperativa. Cadastro **Planos de Contas** (categorias, como *Energia elétrica*) e **Contas a Pagar**. Cada conta pertence a um plano: relação **1:N**. Para entrar é preciso fazer **login**; a API devolve um **token JWT**, que o site guarda na sessão e envia em toda chamada à API. Exclusões são **soft delete**: o registro fica no banco com `removido = true`."

## 2. As três peças (cliente-servidor)

| Peça | Pasta | Papel | Analogia |
|---|---|---|---|
| Front-end (:8080) | `dw3frontend` | Mostra as telas e pede os dados à API | O garçom |
| Back-end/API (:5000) | `dw3backend` | Valida, aplica regras, fala com o banco | A cozinha |
| PostgreSQL (:5432) | container `db` | Guarda os dados | O estoque |

O garçom (front) **nunca** vai ao estoque (banco). Só a cozinha (API) vai. Isso atende à regra "o front não acessa o SGBD".

## 3. Demonstração ao vivo (ordem sugerida, ~5 min)

1. `docker compose up --build` → mostre os 3 containers e as 3 portas (`docker compose ps`).
2. Abra `http://localhost:8080`. Tente entrar com senha errada (mensagem de erro) e depois com a correta.
3. DevTools (F12) → *Application* → *Cookies*: mostre o cookie `session` (marcado **HttpOnly**) que guarda o token.
4. Aba **Plano de Contas**: crie, edite e exclua um plano. Tente excluir "Energia elétrica" → erro, porque tem contas vinculadas (regra de negócio).
5. Aba **Contas a Pagar**: crie uma conta, edite (marque como paga: o resumo muda), use a busca e o filtro, exclua (note o diálogo de confirmação).
6. Mostre o soft delete no banco:
   ```bash
   docker compose exec db psql -U financeiro -d financeiro \
     -c "SELECT id, descricao, removido FROM contas_pagar ORDER BY id;"
   ```
   A conta excluída continua lá, com `removido = t`.
7. Mostre a proteção da API: `curl -i http://localhost:5000/api/contas-pagar` → **401**.
8. Rode os testes: `docker compose exec backend pytest -v` → 36 passam.

## 4. Passeio pelo código (na ordem em que as coisas acontecem)

### 4.1 Banco — `dw3backend/database/init.sql`
- Duas tabelas ligadas por `plano_conta_id REFERENCES plano_contas(id)` (chave estrangeira = o "N" do 1:N).
- Todas têm `id` e `removido`. Texto: `descricao`, `nome`. Decimal: `valor`. Data: `data_vencimento`.
- `NUMERIC(12,2)` guarda dinheiro **exato**. `float` pode dar 0,1 + 0,2 = 0,30000000000000004.

### 4.2 As camadas do back-end

Um pedido atravessa sempre: **routes → controller → model → database**.

| Arquivo (exemplo) | Responsabilidade |
|---|---|
| `routes/contas_pagar_routes.py` | Liga a URL a uma função do controller. Confere o JWT. Devolve JSON. |
| `apps/contas_pagar/controller/conta_pagar_controller.py` | Valida os dados, aplica regras, escolhe o status (201, 400, 404...). **Não conhece Flask nem SQL.** |
| `apps/contas_pagar/model/conta_pagar_model.py` | Só o SQL. |
| `database/conexao.py` | Abre a conexão, executa, faz commit/rollback. |

Vantagem: cada arquivo faz uma coisa só, então é fácil de entender e de testar.

### 4.3 Login — `apps/login/controller/login_controller.py`
1. Recebe usuário e senha em `POST /api/login`.
2. Busca o usuário no banco (`login_model`) e compara a senha com o **hash** (`check_password_hash`). Senha nunca fica salva em texto puro.
3. Se estiver certo, cria o **JWT** com `jwt.encode`, contendo o usuário (`sub`) e a expiração (`exp`), assinado com `JWT_SECRET`.

**O que é um JWT?** Um texto com 3 partes separadas por ponto: `cabeçalho.dados.assinatura`. Os dados são apenas codificados (qualquer um lê); o que protege é a **assinatura**: sem o `JWT_SECRET` ninguém consegue forjar ou alterar um token sem que a assinatura falhe. Por isso **não se coloca senha dentro do token**.

### 4.4 Proteção das rotas — `@token_obrigatorio`
É um *decorator*: uma função que "embrulha" outra. Antes de executar a rota, ele:
1. Lê o cabeçalho `Authorization: Bearer <token>`.
2. Chama `jwt.decode`, que confere assinatura e validade.
3. Se falhar → responde **401** e a rota nem executa.

Cada rota protegida só precisa de uma linha: `@token_obrigatorio`.

### 4.5 As 5 APIs por tabela

| Rota | Função (controller) | SQL essencial (model) |
|---|---|---|
| GET (lista) | `get_all` | `SELECT * FROM ... WHERE removido = FALSE` |
| GET `/<id>` | `get_by_id` | `... WHERE id = %s AND removido = FALSE` |
| POST | `insert` | `INSERT INTO ... VALUES (%s, ...) RETURNING *` |
| PUT `/<id>` | `update` | `UPDATE ... SET ... WHERE id = %s AND removido = FALSE` |
| DELETE `/<id>` | `delete` | `UPDATE ... SET removido = TRUE WHERE id = %s` |

Pontos para destacar:
- `%s` + tupla de valores (em vez de montar o texto com `+` ou f-string) evita **SQL Injection**.
- `RETURNING *` devolve a linha criada/alterada sem precisar de um segundo SELECT.
- O controller valida **no servidor**, mesmo que o formulário já valide (o front pode ser burlado).
- Códigos HTTP com significado: 400 dado inválido · 401 sem autorização · 404 não existe · 409 conflito.

### 4.6 O front-end — `dw3frontend`

O front também é um servidor Flask. Ele **monta o HTML** e, para obter os dados, **chama a API** do back-end.

| Pasta/arquivo | Papel |
|---|---|
| `routes/` | Liga cada URL do site a uma tela (ex.: `/contas-pagar`). |
| `apps/<módulo>/*_api.py` | **As 10 funções do CRUD do front** (5 por tabela). Cada uma chama uma API do back-end. |
| `apps/api_client.py` | Função base `requisicao()`: monta o cabeçalho `Authorization: Bearer ...`, chama a API com a biblioteca `requests` e converte erros em exceções. |
| `apps/login/sessao.py` | Guarda/limpa o token no **cookie de sessão** e tem o `@login_obrigatorio`. |
| `views/` | Templates HTML (Jinja): `{{ variavel }}`, `{% for %}`, `{% if %}`. |
| `public/` | CSS e o único JS (confirmação de exclusão). |

Caminho de uma tela, por exemplo **Contas a Pagar**:
1. O navegador pede `GET /contas-pagar` ao site.
2. `@login_obrigatorio` confere se há token na sessão; se não, manda para `/login`.
3. A rota chama `get_all_contas_pagar()` e `get_all_plano_contas()` (as funções do `apps/`).
4. Elas chamam a API; a resposta (JSON) vira lista Python.
5. A rota calcula status e resumo e entrega tudo ao template `views/contas_pagar/lista.html`, que gera o HTML.

Se a API responder **401**, `api_client` levanta `SessaoExpirada`; o `app.py` captura, limpa a sessão e volta ao login com o aviso.

### 4.7 Docker em 1 minuto — `docker-compose.yml`
- 3 serviços = 3 containers. Dentro da rede do Compose, o front acha a API por `http://backend:5000` e a API acha o banco por `db`.
- `env_file` lê `dw3backend/.env` e `dw3frontend/frontend.env`. O compose só sobrescreve o endereço (`DB_HOST: db`, `BACKEND_URL`), que muda dentro do Docker.
- `healthcheck` + `depends_on: service_healthy`: a API só sobe depois que o Postgres está pronto.
- `init.sql` montado em `/docker-entrypoint-initdb.d/` cria as tabelas na primeira execução.
- `volumes: pgdata` mantém os dados entre reinícios.
- Os `.env` **não vão para o Git** (estão no `.gitignore`); os `.example` mostram o formato.

### 4.8 Testes — `apps/*/tests/`
- Usam `pytest` e o `test_client()` do Flask: chamam as rotas sem subir o servidor.
- `conftest.py` tem os itens compartilhados: o cliente, um token válido (`headers`) e o `plano` de teste, que é criado e apagado a cada teste.
- Cobrem: login e JWT (sem token, inválido, expirado, assinado com outra chave), as 5 APIs, soft delete (confere que o registro segue na tabela), validações e a regra de "plano com contas".

## 5. Perguntas que o professor pode fazer

**Onde o JWT é validado?**
Na API, no decorator `@token_obrigatorio`. O front só guarda e envia o token; ele não decide nada sobre segurança.

**O que acontece quando o token expira?**
`jwt.decode` levanta `ExpiredSignatureError` → a API responde 401 → `api_client` levanta `SessaoExpirada` → o site limpa a sessão e redireciona ao login.

**Por que o token fica no cookie de sessão e não no `localStorage`?**
O enunciado permite os dois. O cookie do Flask é `HttpOnly`: scripts da página não conseguem lê-lo, o que reduz o estrago de um ataque XSS.

**Por que não precisou configurar CORS?**
CORS é uma regra dos *navegadores* para chamadas entre origens diferentes. Aqui o navegador só fala com o site (`:8080`); quem chama a API (`:5000`) é o servidor do site, e servidor não aplica CORS.

**Por que soft delete e não DELETE?**
Preserva histórico e auditoria (em finanças isso é importante) e permite recuperar um registro. O custo é lembrar de filtrar `removido = FALSE` em toda consulta.

**Por que separar controller e model?**
O controller decide *o que pode* (regras); o model sabe *como gravar* (SQL). Se trocar o banco, mexe-se só no model; se mudar uma regra, só no controller.

**Como evitou SQL Injection e XSS?**
SQL Injection: parâmetros `%s` do psycopg2 (comando e valores vão separados ao banco). XSS: o Jinja escapa automaticamente o texto antes de colocá-lo na página.

**Como o front sabe o nome do plano em cada conta?**
A API de contas devolve só `plano_conta_id` (os campos da tabela, como pede o enunciado). A rota monta um dicionário `{id: nome}` com a lista de planos e o template consulta. Alternativa: um `JOIN` no SQL.

**Como o site faz PUT e DELETE se o formulário HTML só tem GET/POST?**
O navegador envia `POST` ao site (`/excluir`); a função `delete_conta_pagar()` do site é quem chama a API com o método `DELETE`.

**E se eu tentar excluir um plano que tem contas?**
A API responde 409 com a mensagem; o site mostra o aviso. Regra em `plano_conta_controller.delete`.

## 6. Exercícios para treinar (e mostrar domínio)

Se o professor pedir uma alteração ao vivo, estas são pequenas e ensinam bastante:

1. **Novo campo `observacao`** em `contas_pagar`: coluna no `init.sql` → model e controller → campo em `views/contas_pagar/form.html` e na rota do front. (Lembre de `docker compose down -v` para recriar o banco.)
2. **Mudar o tempo do token** para 5 min: altere `JWT_EXPIRA_MINUTOS` no `dw3backend/.env` e reinicie o back-end.
3. **Filtro por plano** na tela de contas: um `<select>` no `lista.html` e uma condição em `regras.filtrar`.
4. **Rota de total** `GET /api/contas-pagar/total`: um model com `SELECT SUM(valor) ... WHERE removido = FALSE AND pago = FALSE`, um controller e uma rota.
5. **Um teste novo**: em `test_contas_pagar.py`, copie um teste existente e mude a regra que ele confere.

## 7. Glossário rápido

| Termo | Significa |
|---|---|
| API REST | Servidor que expõe operações por URLs + métodos HTTP (GET, POST, PUT, DELETE) |
| CRUD | Create, Read, Update, Delete |
| JWT | *JSON Web Token*: token assinado que prova quem é o usuário |
| Hash | "Impressão digital" irreversível de uma senha |
| Decorator | Função que adiciona comportamento a outra (`@token_obrigatorio`) |
| Blueprint | Grupo de rotas do Flask (um arquivo em `routes/`) |
| Template / View | Arquivo HTML com marcações do Jinja que o servidor preenche |
| Sessão (cookie) | Dados do usuário guardados no navegador, assinados pelo servidor |
| Soft delete | Marcar como removido em vez de apagar de verdade |
| FK | *Foreign Key*: coluna que aponta para o `id` de outra tabela |
| CORS | Regra do navegador para chamadas entre origens (portas/domínios) diferentes |
| XSS | Injeção de script via texto digitado pelo usuário |
| SQL Injection | Injeção de comandos SQL via texto digitado pelo usuário |
| pytest | Ferramenta que roda os testes automatizados |
