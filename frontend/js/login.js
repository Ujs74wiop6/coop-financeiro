// Lógica da tela de login

// Se já existe um token salvo, não precisa logar de novo
if (obterToken()) {
  window.location.href = "app.html";
}

const form = document.getElementById("form-login");
const msgErro = document.getElementById("erro-login");
const btnEntrar = document.getElementById("btn-entrar");

form.addEventListener("submit", async (evento) => {
  evento.preventDefault(); // impede o recarregamento da página
  msgErro.hidden = true;

  const usuario = form.usuario.value.trim();
  const senha = form.senha.value;
  if (!usuario || !senha) {
    msgErro.textContent = "Preencha usuário e senha.";
    msgErro.hidden = false;
    return;
  }

  btnEntrar.disabled = true;
  btnEntrar.textContent = "Entrando...";
  try {
    const dados = await fazerLogin(usuario, senha);
    salvarSessao(dados);                 // guarda o JWT
    window.location.href = "app.html";   // entra no sistema
  } catch (erro) {
    msgErro.textContent = erro.message;
    msgErro.hidden = false;
    btnEntrar.disabled = false;
    btnEntrar.textContent = "Entrar";
  }
});
