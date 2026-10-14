// =====================================================================
// api.js  -  camada de comunicação com o back-end
//
// Aqui ficam as 10 funções do CRUD (5 por tabela) + login.
// Cada função chama UMA rota da API. A tela (app.js) só chama estas funções.
// =====================================================================

// ---------- Sessão (token JWT guardado no localStorage) ----------
function salvarSessao(dados) {
  localStorage.setItem("token", dados.token);
  localStorage.setItem("usuario", dados.usuario);
  localStorage.setItem("expira_em", dados.expira_em);
}

function limparSessao() {
  localStorage.removeItem("token");
  localStorage.removeItem("usuario");
  localStorage.removeItem("expira_em");
}

function obterToken() {
  return localStorage.getItem("token");
}

function obterUsuario() {
  return localStorage.getItem("usuario");
}

// ---------- Função base: toda requisição passa por aqui ----------
async function requisicao(metodo, caminho, corpo) {
  const cabecalhos = { "Content-Type": "application/json" };
  const token = obterToken();
  if (token) {
    cabecalhos["Authorization"] = "Bearer " + token; // é isto que a API valida
  }

  let resposta;
  try {
    resposta = await fetch(API_URL + caminho, {
      method: metodo,
      headers: cabecalhos,
      body: corpo ? JSON.stringify(corpo) : undefined,
    });
  } catch (e) {
    throw new Error("Não foi possível conectar à API. Ela está no ar?");
  }

  const dados = await resposta.json().catch(() => ({}));

  // 401 fora do login = token ausente/expirado/inválido -> volta para o login
  if (resposta.status === 401 && caminho !== "/login") {
    limparSessao();
    window.location.href = "index.html";
    throw new Error("Sessão expirada.");
  }
  if (!resposta.ok) {
    throw new Error(dados.erro || "Erro inesperado (" + resposta.status + ").");
  }
  return dados;
}

// ---------- Login ----------
function fazerLogin(usuario, senha) {
  return requisicao("POST", "/login", { usuario, senha });
}

// ---------- Plano de Contas (5 funções) ----------
function getAllPlanoContas()         { return requisicao("GET",    "/plano-contas"); }
function getPlanoContaByID(id)       { return requisicao("GET",    "/plano-contas/" + id); }
function insertPlanoConta(plano)     { return requisicao("POST",   "/plano-contas", plano); }
function updatePlanoConta(id, plano) { return requisicao("PUT",    "/plano-contas/" + id, plano); }
function deletePlanoConta(id)        { return requisicao("DELETE", "/plano-contas/" + id); }

// ---------- Contas a Pagar (5 funções) ----------
function getAllContasPagar()         { return requisicao("GET",    "/contas-pagar"); }
function getContaPagarByID(id)       { return requisicao("GET",    "/contas-pagar/" + id); }
function insertContaPagar(conta)     { return requisicao("POST",   "/contas-pagar", conta); }
function updateContaPagar(id, conta) { return requisicao("PUT",    "/contas-pagar/" + id, conta); }
function deleteContaPagar(id)        { return requisicao("DELETE", "/contas-pagar/" + id); }
