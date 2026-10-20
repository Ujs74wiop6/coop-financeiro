-- Executado automaticamente pelo Postgres na primeira vez que o container sobe.
-- Relação: plano_contas (1) ---- (N) contas_pagar

-- Tabela 1: Plano de Contas (categorias de despesa)
CREATE TABLE plano_contas (
    id        SERIAL PRIMARY KEY,
    codigo    VARCHAR(20)  NOT NULL,          -- texto, ex.: '3.1.01'
    nome      VARCHAR(100) NOT NULL,          -- texto, ex.: 'Energia elétrica'
    removido  BOOLEAN      NOT NULL DEFAULT FALSE
);

-- Não permite dois códigos iguais entre os registros ATIVOS.
-- (Um registro removido libera o código para ser usado de novo.)
CREATE UNIQUE INDEX uq_plano_contas_codigo_ativo
    ON plano_contas (codigo) WHERE removido = FALSE;

-- Tabela 2: Contas a Pagar (cada conta pertence a UM plano de contas)
CREATE TABLE contas_pagar (
    id               SERIAL PRIMARY KEY,
    descricao        VARCHAR(150)  NOT NULL,                     -- texto
    valor            NUMERIC(12,2) NOT NULL CHECK (valor > 0),   -- decimal
    data_vencimento  DATE          NOT NULL,                     -- data
    pago             BOOLEAN       NOT NULL DEFAULT FALSE,
    plano_conta_id   INTEGER       NOT NULL REFERENCES plano_contas(id),  -- chave estrangeira (o "N" do 1:N)
    removido         BOOLEAN       NOT NULL DEFAULT FALSE
);

-- Tabela de apoio para o login (não faz parte do CRUD pedido)
CREATE TABLE usuarios (
    id          SERIAL PRIMARY KEY,
    usuario     VARCHAR(50)  NOT NULL UNIQUE,
    senha_hash  VARCHAR(255) NOT NULL        -- nunca guardamos a senha pura
);

-- Dados de exemplo para a demonstração
INSERT INTO plano_contas (codigo, nome) VALUES
    ('3.1.01', 'Energia elétrica'),
    ('3.1.02', 'Água e esgoto'),
    ('3.2.01', 'Insumos agrícolas'),
    ('3.3.01', 'Manutenção de máquinas');

INSERT INTO contas_pagar (descricao, valor, data_vencimento, pago, plano_conta_id) VALUES
    ('Fatura de energia - Outubro', 1850.40, '2026-10-20', FALSE, 1),
    ('Fatura de água - Outubro',     420.75, '2026-10-15', TRUE,  2),
    ('Compra de adubo (50 sacos)',  7300.00, '2026-11-05', FALSE, 3),
    ('Revisão do trator',           2150.90, '2026-10-30', FALSE, 4);
