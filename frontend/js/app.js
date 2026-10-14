// =====================================================================
// app.js  -  lógica das telas (Contas a Pagar e Plano de Contas)
// Usa as funções de api.js; nunca fala direto com o banco.
// =====================================================================

// ---------- Proteção da página: sem token, volta para o login ----------
if (!obterToken()) {
  window.location.href = "index.html";
}

// ---------- Estado em memória (o que está na tela agora) ----------
let planos = [];
let contas = [];
let idEmEdicao = null;        // null = criando; número = editando esse id
let acaoConfirmada = null;    // função executada ao confirmar a exclusão

// ---------- Utilitários ----------
const $ = (id) => document.getElementById(id);

// Impede que texto digitado vire HTML (proteção contra XSS)
function esc(texto) {
  const div = document.createElement("div");
  div.textContent = texto;
  return div.innerHTML;
}

function formatarMoeda(valor) {
  return Number(valor).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

// "2026-10-20" -> "20/10/2026" (sem usar Date, para evitar bug de fuso horário)
function formatarData(iso) {
  const [ano, mes, dia] = iso.split("-");
  return `${dia}/${mes}/${ano}`;
}

function hojeISO() {
  const d = new Date();
  const mes = String(d.getMonth() + 1).padStart(2, "0");
  const dia = String(d.getDate()).padStart(2, "0");
  return `${d.getFullYear()}-${mes}-${dia}`;
}

// Status calculado: paga / vencida / aberto
function statusDaConta(conta) {
  if (conta.pago) return "paga";
  return conta.data_vencimento < hojeISO() ? "vencida" : "aberto";
}

const ROTULO_STATUS = { paga: "Paga", vencida: "Vencida", aberto: "Em aberto" };

function mostrarAviso(mensagem, tipo = "ok") {
  const toast = $("toast");
  toast.textContent = mensagem;
  toast.className = "toast " + tipo;
  toast.hidden = false;
  clearTimeout(mostrarAviso.timer);
  mostrarAviso.timer = setTimeout(() => (toast.hidden = true), 3500);
}

function mostrarErroNoForm(idElemento, mensagem) {
  const p = $(idElemento);
  p.textContent = mensagem;
  p.hidden = false;
}

// ---------- Cabeçalho, abas e botões gerais ----------
$("nome-usuario").textContent = obterUsuario();

$("btn-sair").addEventListener("click", () => {
  limparSessao();
  window.location.href = "index.html";
});

document.querySelectorAll(".aba").forEach((botao) => {
  botao.addEventListener("click", () => {
    document.querySelectorAll(".aba").forEach((b) => b.classList.remove("ativa"));
    botao.classList.add("ativa");
    $("tela-contas").hidden = botao.dataset.tela !== "tela-contas";
    $("tela-planos").hidden = botao.dataset.tela !== "tela-planos";
  });
});

// Botões "Cancelar" dos diálogos
document.querySelectorAll("[data-fechar]").forEach((botao) => {
  botao.addEventListener("click", () => $(botao.dataset.fechar).close());
});

// ---------- Carregamento inicial ----------
async function carregarTudo() {
  try {
    // Planos primeiro, porque a tabela de contas mostra o NOME do plano
    planos = await getAllPlanoContas();
    contas = await getAllContasPagar();
    desenharPlanos();
    desenharContas();
  } catch (erro) {
    mostrarAviso(erro.message, "erro");
  }
}

// =====================================================================
// PLANO DE CONTAS
// =====================================================================
function desenharPlanos() {
  const termo = $("busca-plano").value.trim().toLowerCase();
  const filtrados = planos.filter(
    (p) => p.codigo.toLowerCase().includes(termo) || p.nome.toLowerCase().includes(termo)
  );

  if (filtrados.length === 0) {
    $("tbody-planos").innerHTML = `<tr><td colspan="3" class="vazio">Nenhum plano encontrado.</td></tr>`;
    return;
  }
  $("tbody-planos").innerHTML = filtrados
    .map(
      (p) => `
      <tr>
        <td>${esc(p.codigo)}</td>
        <td>${esc(p.nome)}</td>
        <td class="acoes">
          <button class="btn btn-mini" data-editar-plano="${p.id}">Editar</button>
          <button class="btn btn-mini btn-perigo" data-excluir-plano="${p.id}">Excluir</button>
        </td>
      </tr>`
    )
    .join("");
}

function abrirFormPlano(plano) {
  idEmEdicao = plano ? plano.id : null;
  $("titulo-plano").textContent = plano ? "Editar plano de contas" : "Novo plano de contas";
  $("plano-codigo").value = plano ? plano.codigo : "";
  $("plano-nome").value = plano ? plano.nome : "";
  $("erro-plano").hidden = true;
  $("dlg-plano").showModal();
}

$("btn-novo-plano").addEventListener("click", () => abrirFormPlano(null));
$("busca-plano").addEventListener("input", desenharPlanos);

$("form-plano").addEventListener("submit", async (evento) => {
  evento.preventDefault();
  const dados = {
    codigo: $("plano-codigo").value.trim(),
    nome: $("plano-nome").value.trim(),
  };
  if (!dados.codigo || !dados.nome) {
    return mostrarErroNoForm("erro-plano", "Preencha código e nome.");
  }
  try {
    if (idEmEdicao) {
      await updatePlanoConta(idEmEdicao, dados);
    } else {
      await insertPlanoConta(dados);
    }
    $("dlg-plano").close();
    mostrarAviso(idEmEdicao ? "Plano atualizado." : "Plano criado.");
    await carregarTudo();
  } catch (erro) {
    mostrarErroNoForm("erro-plano", erro.message);
  }
});

// Cliques nos botões da tabela (delegação de eventos: um listener para a tabela toda)
$("tbody-planos").addEventListener("click", async (evento) => {
  const botao = evento.target.closest("button");
  if (!botao) return;

  if (botao.dataset.editarPlano) {
    try {
      // Busca o registro atualizado no servidor (usa GetByID)
      abrirFormPlano(await getPlanoContaByID(botao.dataset.editarPlano));
    } catch (erro) {
      mostrarAviso(erro.message, "erro");
    }
  }
  if (botao.dataset.excluirPlano) {
    const plano = planos.find((p) => p.id == botao.dataset.excluirPlano);
    pedirConfirmacao(`Excluir o plano "${plano.codigo} - ${plano.nome}"?`, async () => {
      await deletePlanoConta(plano.id);
      mostrarAviso("Plano removido.");
      await carregarTudo();
    });
  }
});

// =====================================================================
// CONTAS A PAGAR
// =====================================================================
function desenharResumo() {
  let aberto = 0, vencidas = 0, pagas = 0;
  contas.forEach((c) => {
    const status = statusDaConta(c);
    if (status === "paga") pagas += c.valor;
    else if (status === "vencida") vencidas += c.valor;
    else aberto += c.valor;
  });
  $("res-aberto").textContent = formatarMoeda(aberto);
  $("res-vencidas").textContent = formatarMoeda(vencidas);
  $("res-pagas").textContent = formatarMoeda(pagas);
}

function desenharContas() {
  desenharResumo();

  const termo = $("busca-conta").value.trim().toLowerCase();
  const filtroStatus = $("filtro-status").value;
  const filtradas = contas.filter(
    (c) =>
      c.descricao.toLowerCase().includes(termo) &&
      (filtroStatus === "" || statusDaConta(c) === filtroStatus)
  );

  if (filtradas.length === 0) {
    $("tbody-contas").innerHTML = `<tr><td colspan="6" class="vazio">Nenhuma conta encontrada.</td></tr>`;
    return;
  }
  $("tbody-contas").innerHTML = filtradas
    .map((c) => {
      const plano = planos.find((p) => p.id === c.plano_conta_id);
      const status = statusDaConta(c);
      return `
      <tr>
        <td>${esc(c.descricao)}</td>
        <td>${plano ? esc(plano.codigo + " - " + plano.nome) : "-"}</td>
        <td>${formatarData(c.data_vencimento)}</td>
        <td class="num">${formatarMoeda(c.valor)}</td>
        <td><span class="selo selo-${status}">${ROTULO_STATUS[status]}</span></td>
        <td class="acoes">
          <button class="btn btn-mini" data-editar-conta="${c.id}">Editar</button>
          <button class="btn btn-mini btn-perigo" data-excluir-conta="${c.id}">Excluir</button>
        </td>
      </tr>`;
    })
    .join("");
}

function abrirFormConta(conta) {
  if (planos.length === 0) {
    return mostrarAviso("Cadastre um plano de contas antes de criar uma conta.", "erro");
  }
  idEmEdicao = conta ? conta.id : null;
  $("titulo-conta").textContent = conta ? "Editar conta a pagar" : "Nova conta a pagar";

  // Preenche o <select> com os planos cadastrados
  $("conta-plano").innerHTML = planos
    .map((p) => `<option value="${p.id}">${esc(p.codigo + " - " + p.nome)}</option>`)
    .join("");

  $("conta-descricao").value = conta ? conta.descricao : "";
  $("conta-plano").value = conta ? conta.plano_conta_id : planos[0].id;
  $("conta-valor").value = conta ? conta.valor : "";
  $("conta-vencimento").value = conta ? conta.data_vencimento : hojeISO();
  $("conta-pago").checked = conta ? conta.pago : false;
  $("erro-conta").hidden = true;
  $("dlg-conta").showModal();
}

$("btn-nova-conta").addEventListener("click", () => abrirFormConta(null));
$("busca-conta").addEventListener("input", desenharContas);
$("filtro-status").addEventListener("change", desenharContas);

$("form-conta").addEventListener("submit", async (evento) => {
  evento.preventDefault();
  const dados = {
    descricao: $("conta-descricao").value.trim(),
    plano_conta_id: Number($("conta-plano").value),
    valor: $("conta-valor").value,
    data_vencimento: $("conta-vencimento").value,
    pago: $("conta-pago").checked,
  };
  if (!dados.descricao || !dados.valor || !dados.data_vencimento) {
    return mostrarErroNoForm("erro-conta", "Preencha descrição, valor e vencimento.");
  }
  try {
    if (idEmEdicao) {
      await updateContaPagar(idEmEdicao, dados);
    } else {
      await insertContaPagar(dados);
    }
    $("dlg-conta").close();
    mostrarAviso(idEmEdicao ? "Conta atualizada." : "Conta criada.");
    await carregarTudo();
  } catch (erro) {
    mostrarErroNoForm("erro-conta", erro.message);
  }
});

$("tbody-contas").addEventListener("click", async (evento) => {
  const botao = evento.target.closest("button");
  if (!botao) return;

  if (botao.dataset.editarConta) {
    try {
      abrirFormConta(await getContaPagarByID(botao.dataset.editarConta));
    } catch (erro) {
      mostrarAviso(erro.message, "erro");
    }
  }
  if (botao.dataset.excluirConta) {
    const conta = contas.find((c) => c.id == botao.dataset.excluirConta);
    pedirConfirmacao(`Excluir a conta "${conta.descricao}"?`, async () => {
      await deleteContaPagar(conta.id);
      mostrarAviso("Conta removida.");
      await carregarTudo();
    });
  }
});

// =====================================================================
// CONFIRMAÇÃO DE EXCLUSÃO (usada pelas duas telas)
// =====================================================================
function pedirConfirmacao(texto, acao) {
  $("texto-confirma").textContent = texto;
  $("erro-confirma").hidden = true;
  acaoConfirmada = acao;
  $("dlg-confirma").showModal();
}

$("btn-confirmar").addEventListener("click", async () => {
  try {
    await acaoConfirmada();
    $("dlg-confirma").close();
  } catch (erro) {
    // ex.: tentar excluir um plano que ainda tem contas vinculadas
    mostrarErroNoForm("erro-confirma", erro.message);
  }
});

// ---------- Início ----------
carregarTudo();
