# Roteiro para explicar e demonstrar o projeto

O professor avalia "mesa a mesa" e o enunciado proíbe *vibe coding*. Isso significa que **você precisa entender e saber explicar cada parte**. Este roteiro ajuda a estudar na ordem em que o código é executado. Se alguma parte não ficar clara, leia o arquivo indicado com calma: todos têm comentários.

---

## 1. A ideia em 30 segundos

> "É o módulo financeiro de um ERP de cooperativa. Cadastro **Planos de Contas** (categorias, como *Energia elétrica*) e **Contas a Pagar**. Cada conta pertence a um plano: relação **1:N**. Para entrar é preciso fazer **login**; o servidor devolve um **token JWT** que o front-end envia em toda chamada. Exclusões são **soft delete**: o registro fica no banco com `removido = true`."

## 2. As três peças (cliente-servidor)

| Peça | Papel | Analogia |
|---|---|---|
| Front-end (:8080) | Mostra telas e envia pedidos | O garçom |
| Back-end/API (:5000) | Valida, aplica regras, fala com o banco | A cozinha |
| PostgreSQL (:5432) | Guarda os dados | O estoque |

O garçom (front) **nunca** vai ao estoque (banco). Só a cozinha (API) vai. Isso atende à regra "o front não acessa o SGBD".

## 3. Demonstração ao vivo (ordem sugerida, ~5 min)

1. `docker compose up --build` → mostre os 3 containers e as 3 portas (`docker compose ps`).
2. Abra `http://localhost:8080`. Tente entrar com senha errada (mensagem de erro) e depois com a correta.
3. Abra o DevTools (F12) → *Application* → *Local Storage*: mostre o **token** guardado.
4. Aba **Plano de Contas**: crie, edite e exclua um plano. Tente excluir "Energia elétrica" → erro, porque tem contas vinculadas (regra de negócio).
5. Aba **Contas a Pagar**: crie uma conta, edite (marque como paga: o resumo muda), exclua.
6. Mostre o soft delete no banco:
   ```bash
   docker compose exec db psql -U financeiro -d financeiro \
     -c "SELECT id, descricao, removido FROM contas_pagar ORDER BY id;"
   ```
   A conta excluída continua lá, com `removido = t`.
7. Mostre a proteção da API: no terminal, `curl -i http://localhost:5000/api/contas-pagar` → **401**.

## 4. Passeio pelo código (na ordem em que as coisas acontecem)

### 4.1 Banco — `database/init.sql`
- Duas tabelas ligadas por `plano_conta_id REFERENCES plano_contas(id)` (chave estrangeira = o "N" do 1:N).
- Todas têm `id` e `removido`. Texto: `descricao`, `nome`. Decimal: `valor`. Data: `data_vencimento`.
- `NUMERIC(12,2)` guarda dinheiro **exato**. `float` pode dar 0,1 + 0,2 = 0,30000000000000004.

### 4.2 Login — `backend/auth.py`
1. Recebe usuário e senha em `POST /api/login`.
2. Busca o usuário no banco e compara a senha com o **hash** (`check_password_hash`). Senha nunca fica salva em texto puro.
3. Se estiver certo, cria o **JWT** com `jwt.encode`, contendo o usuário (`sub`) e a expiração (`exp`), assinado com `JWT_SECRET`.

**O que é um JWT?** Um texto com 3 partes separadas por ponto: `cabeçalho.dados.assinatura`. Os dados são apenas codificados (qualquer um lê); o que protege é a **assinatura**: sem o `JWT_SECRET` ninguém consegue forjar ou alterar um token sem que a assinatura falhe. Por isso **não se coloca senha dentro do token**.

### 4.3 Proteção das rotas — `@token_obrigatorio`
É um *decorator*: uma função que "embrulha" outra. Antes de executar a rota, ele:
1. Lê o cabeçalho `Authorization: Bearer <token>`.
2. Chama `jwt.decode`, que confere assinatura e validade.
3. Se falhar → responde **401** e a rota nem executa.

Cada rota protegida só precisa de uma linha: `@token_obrigatorio`.

### 4.4 As 5 APIs — `plano_contas.py` e `contas_pagar.py`
Padrão idêntico nos dois arquivos:

| Rota | O que faz | SQL essencial |
|---|---|---|
| GET (lista) | GetAll | `SELECT * FROM ... WHERE removido = FALSE` |
| GET `/<id>` | GetByID | `... WHERE id = %s AND removido = FALSE` |
| POST | Insert | `INSERT INTO ... VALUES (%s, ...) RETURNING *` |
| PUT `/<id>` | Update | `UPDATE ... SET ... WHERE id = %s AND removido = FALSE` |
| DELETE `/<id>` | Delete (soft) | `UPDATE ... SET removido = TRUE WHERE id = %s` |

Pontos para destacar:
- `%s` + tupla de valores (em vez de montar o texto com `+` ou f-string) evita **SQL Injection**.
- `RETURNING *` devolve a linha criada/alterada sem precisar de um segundo SELECT.
- `_validar()` confere os dados **no servidor**, mesmo que o front já valide (o front pode ser burlado).
- Códigos HTTP com significado: 400 dado inválido · 401 sem autorização · 404 não existe · 409 conflito.

### 4.5 Acesso ao banco — `backend/db.py`
`executar(sql, params, retorno)` abre a conexão, roda o comando e fecha. O `with conn:` faz **commit** se deu certo e **rollback** se deu erro. Só este arquivo conhece as credenciais do banco.

### 4.6 Front-end — `frontend/js/api.js`
- `requisicao()` é a função base: monta o cabeçalho com o token, chama `fetch` e trata erros. Se a API devolver 401, limpa a sessão e volta ao login.
- Abaixo dela estão as **10 funções do CRUD** (uma por API) e `fazerLogin`. São uma linha cada.
- `salvarSessao()` grava o token no `localStorage` (atende "JWT guardado em cookie, localStorage, etc.").

### 4.7 Telas — `frontend/js/app.js`
- Ao abrir, se não há token → redireciona ao login.
- `carregarTudo()` chama `getAllPlanoContas()` e `getAllContasPagar()` e desenha as tabelas.
- Ao clicar em **Editar**, usa `getByID` para buscar o registro atualizado e preencher o formulário.
- Ao salvar: se está editando → `update...`; senão → `insert...`. Depois recarrega a lista.
- `esc()` escapa o texto antes de colocá-lo na tela (evita que alguém cadastre `<script>` e ele execute: **XSS**).

## 5. Docker em 1 minuto — `docker-compose.yml`
- 3 serviços = 3 containers. Dentro da rede do Compose, o back-end acha o banco pelo nome `db` (`DB_HOST: db`).
- `healthcheck` + `depends_on: service_healthy`: a API só sobe depois que o Postgres está pronto.
- `init.sql` montado em `/docker-entrypoint-initdb.d/` cria as tabelas na primeira execução.
- `volumes: pgdata` mantém os dados entre reinícios.
- Senhas e segredo ficam no `.env`, que **não vai para o Git** (está no `.gitignore`).

## 6. Perguntas que o professor pode fazer

**Por que o front e a API estão em portas diferentes? O que é CORS?**
O navegador bloqueia, por segurança, que uma página de uma origem (`:8080`) chame outra (`:5000`) a menos que a API autorize explicitamente. Em `app.py`, `CORS(app, origins=[...])` faz essa autorização.

**Por que soft delete e não DELETE?**
Preserva histórico e auditoria (em finanças isso é importante) e permite recuperar um registro. O custo é lembrar de filtrar `removido = FALSE` em toda consulta.

**Onde o JWT é validado?**
No servidor, no decorator `@token_obrigatorio` (`auth.py`). O front só guarda e envia o token; ele não decide nada sobre segurança.

**O que acontece quando o token expira?**
`jwt.decode` levanta `ExpiredSignatureError` → a API responde 401 → `requisicao()` limpa o `localStorage` e redireciona ao login.

**Por que `localStorage` e não cookie?**
O enunciado permite os dois. `localStorage` é mais simples de demonstrar. Cookie `HttpOnly` seria mais seguro contra XSS (ver limitações em `ARQUITETURA.md`).

**Como evitou SQL Injection?**
Parâmetros `%s` do psycopg2: o banco recebe o comando e os valores separados.

**Como o front sabe o nome do plano em cada conta?**
A API de contas devolve só `plano_conta_id` (os campos da tabela, como pede o enunciado). O front já tem a lista de planos e faz a correspondência em memória (`planos.find(...)`). Alternativa: um `JOIN` no SQL.

**E se eu tentar excluir um plano que tem contas?**
A API responde 409 com a mensagem; o front mostra no diálogo. Regra implementada em `plano_contas.delete`.

## 7. Exercícios para treinar (e mostrar domínio)

Se o professor pedir uma alteração ao vivo, estas são pequenas e ensinam bastante:

1. **Novo campo `observacao`** em `contas_pagar`: coluna no `init.sql` → `_validar` e SQL em `contas_pagar.py` → campo no `app.html` e `app.js`. (Lembre de `docker compose down -v` para recriar o banco.)
2. **Mudar o tempo do token** para 5 min: altere `JWT_EXPIRA_MINUTOS` no `.env` e reinicie o back-end.
3. **Filtro por plano** na tela de contas: acrescente um `<select>` e uma condição no `.filter(...)` de `desenharContas()`.
4. **Rota de contagem** `GET /api/contas-pagar/total`: um `SELECT SUM(valor) ... WHERE removido = FALSE AND pago = FALSE`.

## 8. Glossário rápido

| Termo | Significa |
|---|---|
| API REST | Servidor que expõe operações por URLs + métodos HTTP (GET, POST, PUT, DELETE) |
| CRUD | Create, Read, Update, Delete |
| JWT | *JSON Web Token*: token assinado que prova quem é o usuário |
| Hash | "Impressão digital" irreversível de uma senha |
| Decorator | Função que adiciona comportamento a outra (`@token_obrigatorio`) |
| Soft delete | Marcar como removido em vez de apagar de verdade |
| FK | *Foreign Key*: coluna que aponta para o `id` de outra tabela |
| CORS | Regra do navegador para chamadas entre origens (portas/domínios) diferentes |
| XSS | Injeção de script via texto digitado pelo usuário |
| SQL Injection | Injeção de comandos SQL via texto digitado pelo usuário |
